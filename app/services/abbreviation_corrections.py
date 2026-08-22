"""Deterministic abbreviation / journal-style fixes emitted as tracked changes.

Three small rules that the body-LLM prompt previously asked the LLM to handle
but missed in practice (notably when the abbreviation was preceded by
punctuation, brackets, or dashes):

1. ``e.g.`` followed by whitespace but no comma → ``e.g.,``.
2. ``i.e.`` followed by whitespace but no comma → ``i.e.,``.
   Bare ``eg`` / ``eg.`` / ``ie`` / ``ie.`` get normalised to the proper
   periodised + comma form.
3. ``Fig.`` or ``fig.`` immediately followed by a digit (e.g. ``Fig. 3``)
   → ``Figure 3`` — per JUTLP house style.

Each match is emitted as a tracked ``<w:del>/<w:ins>`` pair so the editor can
still accept or reject individual changes in Word. No author-query comment
is attached — these are small punctuation/expansion fixes and a per-occurrence
comment would be noise.

The pass deliberately leans on a lookbehind that admits ``(``, ``[``, ``—``,
``–``, ``-``, ``,``, ``;`` etc. as left-context — the previous LLM-driven
treatment used a ``\\b`` boundary which silently dropped these cases.
"""

from __future__ import annotations

import os
import re
import zipfile

from lxml import etree

from app.services.acronym_corrections import (
    _patch_content_types,
    _patch_rels,
    _split_run_for_track_change_only,
)
from app.services.document_zones import (
    iter_paragraphs_with_zone,
    should_skip_paragraph,
)
from app.services.language_corrections import WQ
from app.services.quotation_utils import find_quote_spans

# ---------------------------------------------------------------------------
# Regexes
# ---------------------------------------------------------------------------
#
# The left-boundary lookbehind ``(?<![A-Za-z])`` is the central design choice
# — it rejects mid-word matches (``siege``, ``Configure``, ``shielding``) but
# admits every non-letter context including punctuation, brackets, em/en
# dashes, and start-of-string. A bare ``\\b`` is NOT used because ``\\b``
# does not match between two non-word characters, so ``(e.g. foo)`` was
# being silently skipped by the LLM-only treatment.

# ``e.g.`` not already followed by a comma. Replacement: ``e.g.,``.
_EG_RE = re.compile(r"(?<![A-Za-z])e\.g\.(?!,)")

# ``i.e.`` not already followed by a comma. Replacement: ``i.e.,``.
_IE_RE = re.compile(r"(?<![A-Za-z])i\.e\.(?!,)")

# Bare ``eg`` / ``eg.`` followed by whitespace + lowercase letter (so it is
# clearly the abbreviation, not someone's initials). Replacement: ``e.g.,``.
_BARE_EG_RE = re.compile(r"(?<![A-Za-z])eg\.?(?=\s+[a-z])")
_BARE_IE_RE = re.compile(r"(?<![A-Za-z])ie\.?(?=\s+[a-z])")

# ``Fig.`` or ``fig.`` immediately followed by whitespace + digit. Lower-case
# ``fig.`` is gated on a digit follower so we don't rewrite ``a fig. tree``.
_FIG_RE = re.compile(r"(?<![A-Za-z])[Ff]ig\.(?=\s+\d)")


# Rule tuple: (compiled_regex, replacement_text, action_label).
# Order matters only for diagnostic logging — the regexes are mutually
# exclusive on any one substring.
_RULES: tuple[tuple[re.Pattern[str], str, str], ...] = (
    (_EG_RE, "e.g.,", "eg_comma"),
    (_IE_RE, "i.e.,", "ie_comma"),
    (_BARE_EG_RE, "e.g.,", "bare_eg"),
    (_BARE_IE_RE, "i.e.,", "bare_ie"),
    (_FIG_RE, "Figure", "fig_expand"),
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _iter_text_runs(para_el: etree._Element):
    """Yield (run_element, text) for body-text runs we may safely modify.

    Mirrors the helper used by ``decimal_corrections`` — skips runs inside
    tracked-change wrappers (so the pass doesn't re-process a previous
    correction) and runs already inside an open comment range.
    """
    for r in para_el.iter(f"{WQ}r"):
        parent = r.getparent()
        if parent is not None and parent.tag in (f"{WQ}del", f"{WQ}ins"):
            continue
        prev_sibling = r.getprevious()
        if prev_sibling is not None and prev_sibling.tag == f"{WQ}commentRangeStart":
            continue
        t_el = r.find(f"{WQ}t")
        if t_el is None:
            continue
        yield r, t_el.text or ""


def _overlaps_quote(
    quote_spans: list[tuple[int, int]],
    para_start: int,
    para_end: int,
) -> bool:
    for s, e in quote_spans:
        if para_start < e and s < para_end:
            return True
    return False


def _find_first_match(
    text: str,
    *,
    run_offset: int = 0,
    quote_spans: list[tuple[int, int]] | None = None,
):
    """Return the earliest rule-match in ``text`` as
    ``(start, end, replacement, label)`` or ``None`` if no rule matches.

    When two rules could match at the same offset the one with the longer
    match wins — keeps the behaviour deterministic across rule reordering.

    When ``quote_spans`` is provided (paragraph-global offsets) and
    ``run_offset`` is the paragraph-global start of this run, matches
    whose paragraph-global range overlaps any quote span are skipped —
    JUTLP policy: direct quotations retain the source's original text.
    """
    spans = quote_spans or []
    best: tuple[int, int, str, str] | None = None
    for regex, replacement, label in _RULES:
        # Walk every match in this run rather than just the first, so a
        # quoted match doesn't shadow a later legitimate one.
        for m in regex.finditer(text):
            if spans and _overlaps_quote(
                spans, run_offset + m.start(), run_offset + m.end()
            ):
                continue
            cand = (m.start(), m.end(), replacement, label)
            if best is None or cand[0] < best[0] or (
                cand[0] == best[0] and (cand[1] - cand[0]) > (best[1] - best[0])
            ):
                best = cand
            break  # earliest match in this regex; outer loop checks others
    return best


def _process_paragraph(
    para_el: etree._Element,
    next_change_id: int,
    actions: list[dict],
) -> int:
    """Apply every matching rule in ``para_el``, returning updated
    ``next_change_id``.

    Loops until no run yields another match — each rewrite shifts offsets so
    we recompute from the current state rather than caching positions.
    """
    while True:
        # Compute quote spans from the paragraph's full plain text so
        # matches inside `"..."` regions can be filtered. Rebuilt each
        # iteration because earlier rewrites in this paragraph shift
        # offsets — cheap to recompute.
        para_plain = "".join(t for _, t in _iter_text_runs(para_el))
        quote_spans = find_quote_spans(para_plain)
        any_match = False
        run_offset = 0
        for run_el, run_text in _iter_text_runs(para_el):
            match = _find_first_match(
                run_text, run_offset=run_offset, quote_spans=quote_spans
            )
            if match is None:
                run_offset += len(run_text)
                continue
            start, end, replacement, label = match
            original = run_text[start:end]
            next_change_id = _split_run_for_track_change_only(
                run_el,
                start,
                end,
                replacement,
                next_change_id,
            )
            actions.append(
                {
                    "rule": label,
                    "original": original,
                    "replacement": replacement,
                }
            )
            any_match = True
            break  # run_el is now stale — restart the run iteration
        if not any_match:
            return next_change_id


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def apply_abbreviation_corrections(
    input_path: str,
    output_path: str,
    next_change_id: int = 1,
) -> tuple[int, list[dict]]:
    """Run the abbreviation pass over ``input_path`` and write ``output_path``.

    Mirrors the return shape of sibling correction passes
    (``apply_au_spelling_corrections``, ``apply_acronym_corrections``):
    ``(next_change_id, actions)``.
    """
    with zipfile.ZipFile(input_path, "r") as z:
        names = z.namelist()
        doc_xml = z.read("word/document.xml")
        rels_xml = z.read("word/_rels/document.xml.rels")
        ct_xml = z.read("[Content_Types].xml")
        has_comments = "word/comments.xml" in names
        comments_xml = z.read("word/comments.xml") if has_comments else None

    doc_root = etree.fromstring(doc_xml)

    actions: list[dict] = []
    for para_el, zone in iter_paragraphs_with_zone(doc_root):
        if should_skip_paragraph(para_el, zone):
            continue
        next_change_id = _process_paragraph(para_el, next_change_id, actions)

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
    # No comments emitted, but keep rels / content-types patched for parity
    # with sibling passes — these helpers are idempotent.
    new_rels_xml = _patch_rels(rels_xml)
    new_ct_xml = _patch_content_types(ct_xml)

    tmp = output_path + ".abbr.tmp"
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
                elif item.filename == "word/comments.xml" and has_comments:
                    zout.writestr(item, comments_xml)
                else:
                    zout.writestr(item, zin.read(item.filename))
        os.replace(tmp, output_path)
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise

    return next_change_id, actions
