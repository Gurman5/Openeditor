"""Two journal-style decimal checks emitted as Word comments.

1. **Excess precision** — the journal reports to two decimal places per APA7.
   Some specific analyses legitimately need more, so the bot flags the issue
   *once* on the first occurrence in the document and skips the rest. The
   editor can then review the whole paper from that one prompt.

2. **Comma-as-decimal** — authors trained in non-English contexts sometimes
   write ``36,1`` where the journal expects ``36.1``. We do **not** auto-fix
   (the same comma is sometimes a thousand separator) — every suspect
   occurrence gets its own comment so the editor can verify each in place.
   We use a conservative heuristic that only flags ``\\d+,\\d{1,2}`` so
   common thousand separators like ``1,000`` don't generate noise.

Comments are emitted via the same machinery as ``acronym_corrections`` so
they share the "Author Query N." numbered format and the same skip-styles
(headings, references, author block).
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
from app.services.document_zones import iter_paragraphs_with_zone, should_skip_paragraph
from app.services.language_corrections import WQ, W
from app.services.quotation_utils import find_quote_spans

# ---------------------------------------------------------------------------
# Detection patterns
# ---------------------------------------------------------------------------

# A decimal value with strictly more than 2 fractional digits, isolated from
# other dots/digits so version strings like ``3.10.5`` and money formats like
# ``1,234.50`` don't trip the regex.
_EXCESS_DECIMAL = re.compile(r"(?<![.\d])\d+\.\d{3,}(?![.\d])")

# A number that uses a comma where a decimal point may be intended. Strictly
# 1–2 digits after the comma; the trailing negative-lookahead ``(?![.,\d])``
# is what excludes ``1,234`` (third digit follows the matched ``\d{1,2}``)
# and ``1,234,567``.
_COMMA_DECIMAL = re.compile(r"(?<![.\d])\d+,\d{1,2}(?![.,\d])")

# ---------------------------------------------------------------------------
# Comment messages (client-supplied wording)
# ---------------------------------------------------------------------------

_PRECISION_COMMENT = (
    "This Journal reports to two decimal places in line with APA7. "
    "We understand some specific analyses require reporting beyond two "
    "decimal places in APA7. Please review carefully to ensure your "
    "reporting meets these guidelines."
)

_COMMA_DECIMAL_COMMENT = (
    "Please check this number — a comma is being used where a decimal "
    "point may be intended (e.g., 36,1 should be 36.1)."
)


# ---------------------------------------------------------------------------
# Paragraph helpers (mirrored from sibling correction modules)
# ---------------------------------------------------------------------------


def _get_style_name(para_el: etree._Element) -> str:
    pPr = para_el.find(f"{WQ}pPr")
    if pPr is None:
        return ""
    pStyle = pPr.find(f"{WQ}pStyle")
    if pStyle is None:
        return ""
    return pStyle.get(f"{WQ}val", "")


def _iter_text_runs(para_el: etree._Element):
    """Yield (run_element, text) for body-text runs we may safely modify.

    Skips runs inside tracked-change wrappers and runs that have already been
    wrapped in a comment range (their immediate preceding sibling is a
    ``w:commentRangeStart``). Without the latter check, the per-paragraph
    re-scan loop would re-find the same match every iteration when no
    tracked-change replacement is emitted (the matched text stays in place
    inside the comment range).
    """
    for r in para_el.iter(f"{WQ}r"):
        parent = r.getparent()
        if parent is not None and parent.tag in (f"{WQ}del", f"{WQ}ins"):
            continue
        prev_sibling = r.getprevious()
        if (
            prev_sibling is not None
            and prev_sibling.tag == f"{WQ}commentRangeStart"
        ):
            continue
        t_el = r.find(f"{WQ}t")
        if t_el is None:
            continue
        yield r, t_el.text or ""


# ---------------------------------------------------------------------------
# Per-paragraph processing
# ---------------------------------------------------------------------------


def _has_corrected_form_in_tracked_ins(
    para_el: etree._Element, comma_value: str
) -> bool:
    """Return True if a sibling ``<w:ins>`` already supplies ``comma_value``
    with the comma replaced by a period.

    This prevents a redundant "comma is being used where a decimal point may
    be intended" comment when an earlier pipeline pass has already applied
    that very correction as a tracked change — the editor sees the fix in
    the gutter; a separate prose comment is noise.
    """
    corrected = comma_value.replace(",", ".")
    for ins_el in para_el.iter(f"{WQ}ins"):
        ins_text = "".join(
            (t.text or "") for t in ins_el.iter(f"{WQ}t") if t.text
        )
        if corrected in ins_text:
            return True
    return False


def _find_next_action(
    para_el: etree._Element,
    precision_fired: bool,
):
    """Return ``(run_el, start, end, check_kind, message, value)`` for the
    earliest applicable match in the paragraph, or ``None`` if nothing more
    needs to happen.

    ``check_kind`` is ``"precision"`` for an excess-decimal flag (only
    eligible while ``precision_fired`` is False) or ``"comma_decimal"`` for
    a suspected comma-as-decimal.

    Matches that sit inside a direct quotation (paired double quotes) are
    skipped — JUTLP policy: direct quotations retain the source's
    original text.
    """
    best = None  # (run, start, end, check, message, value)
    # Compute quote spans once at paragraph level; offsets are mapped
    # from each run to paragraph-global as we walk.
    para_plain = "".join(t for _, t in _iter_text_runs(para_el))
    quote_spans = find_quote_spans(para_plain)
    run_offset = 0
    for run_el, run_text in _iter_text_runs(para_el):
        candidates: list[tuple[int, int, str, str, str]] = []

        def _in_quote(start: int, end: int) -> bool:
            ps, pe = run_offset + start, run_offset + end
            for s, e in quote_spans:
                if ps < e and s < pe:
                    return True
            return False

        if not precision_fired:
            for m in _EXCESS_DECIMAL.finditer(run_text):
                if _in_quote(m.start(), m.end()):
                    continue
                candidates.append(
                    (m.start(), m.end(), "precision", _PRECISION_COMMENT, m.group(0))
                )
        for m in _COMMA_DECIMAL.finditer(run_text):
            if _in_quote(m.start(), m.end()):
                continue
            # Skip the flag when a sibling tracked-insertion already supplies
            # the corrected form (e.g. "1.4%" appears in a <w:ins> next to
            # the still-visible "1,4%"). Avoids piling a redundant comment
            # on top of a fix the editor can already see in the gutter.
            if _has_corrected_form_in_tracked_ins(para_el, m.group(0)):
                continue
            candidates.append(
                (m.start(), m.end(), "comma_decimal", _COMMA_DECIMAL_COMMENT, m.group(0))
            )
        run_offset += len(run_text)
        if not candidates:
            continue
        candidates.sort(key=lambda c: c[0])
        first = candidates[0]
        return (run_el, first[0], first[1], first[2], first[3], first[4])
    return best


def _process_paragraph(
    para_el: etree._Element,
    next_comment_id: int,
    comments_root: etree._Element,
    actions: list[dict],
    precision_fired: list[bool],
) -> int:
    """Apply every actionable comment found in ``para_el``. Returns the
    updated ``next_comment_id``.

    ``precision_fired`` is a single-element list used as a tiny mutable
    container so the precision-once-per-document flag is visible across
    paragraphs.
    """
    # Skip check is now done at the call-site via document_zones helpers so
    # both the style-skip set and the zone-skip rule fire consistently.
    while True:
        action = _find_next_action(para_el, precision_fired[0])
        if action is None:
            return next_comment_id
        run_el, start, end, kind, message, value = action

        comments_root.append(_make_comment_element(next_comment_id, message))
        # Reuse the acronym module's run-splitter with expansion=None so the
        # matched text is wrapped in a comment range without any tracked-
        # change rewrite. ``change_id`` isn't used in this branch but the
        # helper requires the argument — pass any int.
        _split_run_for_action(
            run_el,
            start,
            end,
            expansion=None,
            comment_id=next_comment_id,
            change_id=0,
        )
        actions.append(
            {
                "check": kind,
                "value": value,
                "comment_id": next_comment_id,
            }
        )
        if kind == "precision":
            precision_fired[0] = True
        next_comment_id += 1


def apply_decimal_corrections(
    input_path: str,
    output_path: str,
    next_change_id: int = 1,
) -> tuple[int, list[dict]]:
    """Run both decimal checks over ``input_path`` and write to ``output_path``.

    Mirrors the return shape of sibling correction passes
    (``apply_au_spelling_corrections``, ``apply_acronym_corrections``):
    ``(next_change_id, actions)``. This pass emits no tracked changes, so
    ``next_change_id`` is returned unchanged — it's threaded for parity.
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

    actions: list[dict] = []
    precision_fired = [False]

    for para_el, zone in iter_paragraphs_with_zone(doc_root):
        if should_skip_paragraph(para_el, zone):
            continue
        next_comment_id = _process_paragraph(
            para_el,
            next_comment_id,
            comments_root,
            actions,
            precision_fired,
        )

    if not actions:
        # Nothing to write. Copy through if input != output to keep the
        # caller's contract simple.
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

    tmp = output_path + ".dec.tmp"
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
