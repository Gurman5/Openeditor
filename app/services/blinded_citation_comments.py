"""Flag blinded / placeholder citations and self-references.

For peer review authors anonymise self-citations and their own affiliation,
leaving artefacts such as ``([Author] et al., under review)`` or ``[University]``
in the text. JUTLP publishes *identified* manuscripts, so these blinding
placeholders are not acceptable in the final submission — they must be replaced
with the real author name(s)/full reference and the actual institution name.

This pass is **comment-only** — de-anonymising the text is the author's job
(only they know the real citation), so the bot explains the problem and the
editor/author fixes it.

Detection is deliberately narrow to avoid false positives: it fires only on
**square-bracketed** self-reference placeholders — ``[Author]``, ``[Authors]``,
``[University]``, ``[Institution]``, ``[Affiliation]``, ``[Name]``,
``[redacted]``, ``[removed]``, ``[blinded]``, ``[anonymised]``. Unbracketed
prose like "an anonymous survey" or "data were anonymised" is therefore never
flagged. A single comment is anchored per paragraph, listing the placeholders
found there.
"""

from __future__ import annotations

import os
import re
import zipfile

from lxml import etree

from app.services.acronym_corrections import (
    _make_comment_element,
    _patch_content_types,
    _patch_rels,
    _split_run_for_action,
)
from app.services.language_corrections import WQ, W

# Square-bracketed blinding placeholders. The bracket is what makes the signal
# reliable — these tokens only appear bracketed when they are review artefacts.
_PLACEHOLDER_RE = re.compile(
    r"\[\s*(?:authors?|universit(?:y|ies)|institutions?|institutes?|"
    r"affiliations?|names?|redacted|removed|blinded|anonymi[sz]ed)\s*\]",
    re.IGNORECASE,
)


def _classify(token: str) -> str:
    """'inst' for institution/affiliation placeholders, else 'author'."""
    core = re.sub(r"[\[\]\s]", "", token).lower()
    if core.startswith(("universit", "institut", "affiliation")):
        return "inst"
    return "author"


def _build_comment(tokens: list[str]) -> str:
    quoted = ", ".join(f"“{t}”" for t in tokens)
    cats = {_classify(t) for t in tokens}
    msg = (
        "JUTLP publishes identified, non-blinded manuscripts, so review-stage "
        "blinding placeholders are not acceptable in the final submission. "
        f"This text still contains: {quoted}. "
    )
    if "author" in cats:
        msg += (
            "Please replace anonymised self-citations such as "
            "“[Author] et al., under review” with the full author "
            "name(s) and a complete reference. "
        )
    if "inst" in cats:
        msg += (
            "Please replace institution/affiliation placeholders with the "
            "actual name."
        )
    return msg.strip()


def _own_text_runs(para_el: etree._Element):
    """Yield (run_el, text) for runs that belong DIRECTLY to ``para_el``.

    Runs inside a nested paragraph (e.g. a floating text box) or inside a
    tracked ``<w:del>``/``<w:ins>``, and runs already opening a comment range,
    are skipped — so we neither double-count text-box content nor anchor on our
    own tracked changes.
    """
    for r in para_el.iter(f"{WQ}r"):
        anc = r.getparent()
        owner = None
        while anc is not None:
            if anc.tag == f"{WQ}p":
                owner = anc
                break
            anc = anc.getparent()
        if owner is not para_el:
            continue
        parent = r.getparent()
        if parent is not None and parent.tag in (f"{WQ}del", f"{WQ}ins"):
            continue
        prev = r.getprevious()
        if prev is not None and prev.tag == f"{WQ}commentRangeStart":
            continue
        t_el = r.find(f"{WQ}t")
        if t_el is None:
            continue
        yield r, (t_el.text or "")


def _distinct(tokens) -> list[str]:
    seen: list[str] = []
    for t in tokens:
        if t not in seen:
            seen.append(t)
    return seen


def _anchor_paragraph_comment(
    para_el: etree._Element, comments_root: etree._Element, comment_id: int
) -> bool:
    """Detect placeholders in ``para_el`` and, if any, anchor one comment.

    Returns True when a comment was added.
    """
    runs = list(_own_text_runs(para_el))
    own_text = "".join(text for _, text in runs)
    matches = list(_PLACEHOLDER_RE.finditer(own_text))
    if not matches:
        return False

    tokens = _distinct(m.group(0).strip() for m in matches)
    message = _build_comment(tokens)
    first_start = matches[0].start()
    first_end = matches[0].end()

    # Locate the run containing the first match and anchor the comment there.
    cum = 0
    for run_el, text in runs:
        run_start, run_end = cum, cum + len(text)
        if run_start <= first_start < run_end:
            local_start = first_start - run_start
            local_end = min(len(text), first_end - run_start)
            if local_end > local_start:
                comments_root.append(_make_comment_element(comment_id, message))
                _split_run_for_action(
                    run_el, local_start, local_end,
                    expansion=None, comment_id=comment_id, change_id=0,
                )
                return True
            break
        cum = run_end

    # Fallback (placeholder split across runs): anchor the first non-empty run.
    for run_el, text in runs:
        if text.strip():
            comments_root.append(_make_comment_element(comment_id, message))
            _split_run_for_action(
                run_el, 0, len(text),
                expansion=None, comment_id=comment_id, change_id=0,
            )
            return True
    return False


def apply_blinded_citation_comments(
    input_path: str,
    output_path: str,
    next_change_id: int = 1,
) -> tuple[int, list[dict]]:
    """Comment on blinded / placeholder citations and self-references.

    Comment-only, so ``next_change_id`` is threaded unchanged. Returns
    ``(next_change_id, actions)`` to match the sibling comment passes.
    """
    with zipfile.ZipFile(input_path, "r") as z:
        names = z.namelist()
        doc_xml = z.read("word/document.xml")
        rels_xml = z.read("word/_rels/document.xml.rels")
        ct_xml = z.read("[Content_Types].xml")
        has_comments = "word/comments.xml" in names
        comments_xml = z.read("word/comments.xml") if has_comments else None

    doc_root = etree.fromstring(doc_xml)

    if comments_xml:
        comments_root = etree.fromstring(comments_xml)
        existing = [
            int(el.get(f"{WQ}id", 0))
            for el in comments_root.findall(f"{WQ}comment")
        ]
        next_comment_id = max(existing, default=0) + 1
    else:
        comments_root = etree.Element(f"{WQ}comments", nsmap={"w": W})
        next_comment_id = 1

    body = doc_root.find(f"{WQ}body")
    actions: list[dict] = []
    if body is not None:
        for para_el in body.iter(f"{WQ}p"):
            if _anchor_paragraph_comment(para_el, comments_root, next_comment_id):
                actions.append(
                    {"rule": "blinded_citation", "comment_id": next_comment_id}
                )
                next_comment_id += 1

    if not actions:
        if input_path != output_path:
            with zipfile.ZipFile(input_path, "r") as zin, zipfile.ZipFile(
                output_path, "w", zipfile.ZIP_DEFLATED
            ) as zout:
                for item in zin.infolist():
                    zout.writestr(item, zin.read(item.filename))
        return next_change_id, actions

    new_doc_xml = etree.tostring(
        doc_root, xml_declaration=True, encoding="UTF-8", standalone=True
    )
    new_comments_xml = etree.tostring(
        comments_root, xml_declaration=True, encoding="UTF-8", standalone=True
    )
    new_rels_xml = _patch_rels(rels_xml)
    new_ct_xml = _patch_content_types(ct_xml)

    tmp = output_path + ".blindcite.tmp"
    try:
        with zipfile.ZipFile(input_path, "r") as zin, zipfile.ZipFile(
            tmp, "w", zipfile.ZIP_DEFLATED
        ) as zout:
            for item in zin.infolist():
                if item.filename == "word/document.xml":
                    zout.writestr(item, new_doc_xml)
                elif item.filename == "word/_rels/document.xml.rels":
                    zout.writestr(item, new_rels_xml)
                elif item.filename == "[Content_Types].xml":
                    zout.writestr(item, new_ct_xml)
                elif item.filename == "word/comments.xml":
                    zout.writestr(item, new_comments_xml)
                else:
                    zout.writestr(item, zin.read(item.filename))
            if not has_comments:
                zout.writestr("word/comments.xml", new_comments_xml)
        os.replace(tmp, output_path)
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise

    return next_change_id, actions
