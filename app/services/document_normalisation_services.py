"""Strip author-supplied formatting noise from incoming .docx files.

Authors sometimes submit copy with leftover tracked changes from their own
revision rounds, coloured text used to flag self-edits, or highlighting. The
journal's editorial workflow expects a clean baseline, so we normalise these
before validation, reference checking, and the LLM editorial review run.

There is one exception: paragraphs styled with the journal's "Guidance Notes"
template style are advisory text the author was supposed to delete. When we
encounter those, we delete the entire paragraph rather than just stripping its
formatting.

The transform operates on `word/document.xml` directly via lxml — high-level
python-docx APIs don't expose tracked-change wrappers reliably enough.
"""

from __future__ import annotations

import json
import shutil
import zipfile
from dataclasses import dataclass, field
from pathlib import Path

from lxml import etree

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
WQ = f"{{{W}}}"

# Style id/name used by the JULTP template for editorial guidance paragraphs.
# Matches `forbidden_styles` entry in app/rules/canonical_jultp_template.py.
GUIDANCE_NOTES_STYLE = "Guidance Notes"
# Word often stores style ids without spaces while keeping the friendly name
# with spaces; accept both common forms.
_GUIDANCE_STYLE_VALUES = {GUIDANCE_NOTES_STYLE, "GuidanceNotes"}


@dataclass
class NormalisationReport:
    """Counts of what was changed during normalisation.

    Aggregate counts feed the single-line summary comment on the output
    document. Per-strip detail lists (``colour_strips`` /
    ``highlight_strips``) feed an optional JSON sidecar so reviewers can
    answer "what was highlighted in paragraph 47?" without diffing the
    binary docx.
    """

    accepted_revisions: int = 0
    runs_colour_stripped: int = 0
    runs_highlight_stripped: int = 0
    guidance_paragraphs_deleted: int = 0
    blank_paragraphs_removed: int = 0
    colour_strips: list[dict] = field(default_factory=list)
    highlight_strips: list[dict] = field(default_factory=list)

    @property
    def changed(self) -> bool:
        return (
            self.accepted_revisions > 0
            or self.runs_colour_stripped > 0
            or self.runs_highlight_stripped > 0
            or self.guidance_paragraphs_deleted > 0
            or self.blank_paragraphs_removed > 0
        )

    def summary_text(self) -> str:
        """Human-readable single-line summary for the document comment."""
        parts: list[str] = []
        if self.accepted_revisions:
            parts.append(f"accepted {self.accepted_revisions} tracked change(s)")
        if self.runs_colour_stripped:
            parts.append(f"removed colour from {self.runs_colour_stripped} run(s)")
        if self.runs_highlight_stripped:
            parts.append(f"removed highlighting from {self.runs_highlight_stripped} run(s)")
        if self.guidance_paragraphs_deleted:
            parts.append(
                f"deleted {self.guidance_paragraphs_deleted} Guidance Notes paragraph(s)"
            )
        if self.blank_paragraphs_removed:
            parts.append(
                f"removed {self.blank_paragraphs_removed} blank paragraph(s)"
            )
        if not parts:
            return "No author formatting noise detected."
        return "Normalised author formatting: " + "; ".join(parts) + "."

    def write_sidecar(self, docx_path: str | Path) -> Path | None:
        """Write an audit JSON next to ``docx_path`` listing every strip.

        Returns the path written, or ``None`` if there is no detail to
        record. The sidecar's filename is ``<docx_stem>.normalisation.json``
        so multiple outputs in the same directory don't collide.
        """
        if not (self.colour_strips or self.highlight_strips):
            return None
        docx_path = Path(docx_path)
        sidecar = docx_path.with_suffix(".normalisation.json")
        payload = {
            "accepted_revisions": self.accepted_revisions,
            "guidance_paragraphs_deleted": self.guidance_paragraphs_deleted,
            "blank_paragraphs_removed": self.blank_paragraphs_removed,
            "colour_strips": self.colour_strips,
            "highlight_strips": self.highlight_strips,
        }
        sidecar.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        return sidecar


def _unwrap(element: etree._Element) -> None:
    """Replace `element` with its children in the parent."""
    parent = element.getparent()
    if parent is None:
        return
    index = list(parent).index(element)
    for i, child in enumerate(list(element)):
        parent.insert(index + i, child)
    parent.remove(element)


def _accept_tracked_changes(doc_root: etree._Element) -> int:
    """Resolve all tracked-change wrappers as if 'Accept All Changes' was clicked.

    - `w:ins` / `w:moveTo`: keep content (unwrap the wrapper).
    - `w:del` / `w:moveFrom`: remove element and content.
    - `w:pPrChange` / `w:rPrChange` / `w:sectPrChange`: drop the change record,
      keep the current properties (which already reflect the post-change state).

    Returns the count of accept-style operations performed.
    """
    count = 0

    # Drop deletion wrappers entirely (and the runs they contain).
    for tag in (f"{WQ}del", f"{WQ}moveFrom"):
        for el in doc_root.iter(tag):
            parent = el.getparent()
            if parent is not None:
                parent.remove(el)
                count += 1

    # Re-iterate after structural changes; insertion wrappers come next.
    for tag in (f"{WQ}ins", f"{WQ}moveTo"):
        # Materialise to a list because we mutate during iteration.
        for el in list(doc_root.iter(tag)):
            _unwrap(el)
            count += 1

    # Property-level change records: just drop them.
    for tag in (f"{WQ}pPrChange", f"{WQ}rPrChange", f"{WQ}sectPrChange"):
        for el in list(doc_root.iter(tag)):
            parent = el.getparent()
            if parent is not None:
                parent.remove(el)
                count += 1

    return count


def _ancestor_paragraph_index(rpr: etree._Element, p_to_index: dict) -> int:
    """Map an rPr back to the document-order index of its containing ``<w:p>``.

    ``p_to_index`` is a pre-built ``{<w:p element>: index}`` dict — building
    it once amortises the lookup cost across hundreds of runs.
    """
    el = rpr
    while el is not None:
        if el.tag == f"{WQ}p":
            return p_to_index.get(el, -1)
        el = el.getparent()
    return -1


def _run_snippet(rpr: etree._Element, max_chars: int = 60) -> str:
    """Return up to ``max_chars`` of the run's visible text, for audit logs."""
    r = rpr.getparent()
    if r is None:
        return ""
    parts: list[str] = []
    for t in r.findall(f"{WQ}t"):
        if t.text:
            parts.append(t.text)
        if sum(len(p) for p in parts) >= max_chars:
            break
    snippet = "".join(parts).strip()
    if len(snippet) > max_chars:
        snippet = snippet[: max_chars - 1] + "…"
    return snippet


def _strip_run_colour_and_highlight(
    doc_root: etree._Element,
) -> tuple[int, int, list[dict], list[dict]]:
    """Remove direct-formatting colour and highlight from every run.

    Style-driven colour (defined in styles.xml) is left untouched — only the
    run-level overrides authors typically use to flag self-edits are removed.

    Returns ``(runs_colour_stripped, runs_highlight_stripped, colour_details,
    highlight_details)``. The two detail lists carry per-run metadata
    (paragraph index, text snippet, original colour/highlight value) so a
    sidecar audit file can be written.
    """
    p_to_index = {p: idx for idx, p in enumerate(doc_root.iter(f"{WQ}p"))}

    colour_runs = 0
    highlight_runs = 0
    colour_details: list[dict] = []
    highlight_details: list[dict] = []

    for rpr in doc_root.iter(f"{WQ}rPr"):
        colour_el = rpr.find(f"{WQ}color")
        if colour_el is not None:
            colour_details.append({
                "paragraph_index": _ancestor_paragraph_index(rpr, p_to_index),
                "snippet": _run_snippet(rpr),
                "value": colour_el.get(f"{WQ}val", ""),
            })
            rpr.remove(colour_el)
            colour_runs += 1

        # Highlights come in two shapes: w:highlight (named palette) and
        # w:shd (cell-shading-style RGB highlight). Both should go.
        removed_highlight = False
        highlight_value = ""
        for tag in (f"{WQ}highlight", f"{WQ}shd"):
            el = rpr.find(tag)
            if el is not None:
                # Prefer w:val (named highlight palette); fall back to
                # w:fill (RGB shading) so the audit captures whichever
                # attribute carried the colour.
                if not highlight_value:
                    highlight_value = (
                        el.get(f"{WQ}val") or el.get(f"{WQ}fill") or ""
                    )
                rpr.remove(el)
                removed_highlight = True
        if removed_highlight:
            highlight_details.append({
                "paragraph_index": _ancestor_paragraph_index(rpr, p_to_index),
                "snippet": _run_snippet(rpr),
                "value": highlight_value,
            })
            highlight_runs += 1

    return colour_runs, highlight_runs, colour_details, highlight_details


def _delete_guidance_paragraphs(doc_root: etree._Element) -> int:
    """Drop every `w:p` whose paragraph style is the journal Guidance Notes."""
    deleted = 0
    for p in list(doc_root.iter(f"{WQ}p")):
        ppr = p.find(f"{WQ}pPr")
        if ppr is None:
            continue
        pstyle = ppr.find(f"{WQ}pStyle")
        if pstyle is None:
            continue
        val = pstyle.get(f"{WQ}val")
        if val and val in _GUIDANCE_STYLE_VALUES:
            parent = p.getparent()
            if parent is not None:
                parent.remove(p)
                deleted += 1
    return deleted


def _is_paragraph_blank(p: etree._Element) -> bool:
    """Return True if `p` carries no visible content worth keeping.

    A paragraph is "blank" only when *all* of these hold:
    - No visible text after stripping whitespace.
    - No inline image, drawing, or embedded object.
    - No section break — `w:sectPr` carries page/section state for the
      preceding content and must never be lost.
    - No bookmark range starts or ends here — removing the paragraph would
      orphan the matching anchor.
    """
    # Visible text in any run.
    for t in p.iter(f"{WQ}t"):
        if (t.text or "").strip():
            return False

    # Embedded media / drawings / OLE — author intent, keep the paragraph.
    for tag in (f"{WQ}drawing", f"{WQ}pict", f"{WQ}object"):
        if p.find(f".//{tag}") is not None:
            return False

    # Also keep textboxes (e.g. Editor's box)
    for element in p.iter():
        if etree.QName(element).localname in {"txbxContent", "textbox"}:
            return False

    # Section break attached to this paragraph.
    ppr = p.find(f"{WQ}pPr")
    if ppr is not None and ppr.find(f"{WQ}sectPr") is not None:
        return False

    # Bookmark anchors — leave the paragraph in place so cross-references
    # don't break.
    for tag in (f"{WQ}bookmarkStart", f"{WQ}bookmarkEnd"):
        if p.find(f".//{tag}") is not None:
            return False

    return True


def _remove_blank_paragraphs(doc_root: etree._Element) -> int:
    """Drop empty paragraphs authors used as visual gaps between content.

    The journal template defines paragraph spacing via paragraph styles, so
    these blank `w:p` elements are pure noise and break the template's
    intended rhythm. Paragraphs inside table cells are skipped — Word
    requires at least one paragraph per cell for a valid layout.
    """
    removed = 0
    for p in list(doc_root.iter(f"{WQ}p")):
        # Skip paragraphs nested inside table cells — removing them can
        # produce an invalid docx.
        ancestor = p.getparent()
        in_table_cell = False
        while ancestor is not None:
            if ancestor.tag == f"{WQ}tc":
                in_table_cell = True
                break
            ancestor = ancestor.getparent()
        if in_table_cell:
            continue

        if not _is_paragraph_blank(p):
            continue

        parent = p.getparent()
        if parent is not None:
            parent.remove(p)
            removed += 1
    return removed


def normalise_docx(input_path: str | Path, output_path: str | Path) -> NormalisationReport:
    """Write a normalised copy of `input_path` to `output_path` and return a report.

    The original file is not mutated. All non-`word/document.xml` parts (images,
    media, relationships, content types, comments, headers/footers, etc.) are
    copied through unchanged so downstream stages see a fully valid package.
    """
    input_path = str(input_path)
    output_path = str(output_path)

    if input_path != output_path:
        shutil.copyfile(input_path, output_path)

    with zipfile.ZipFile(output_path, "r") as zin:
        names = zin.namelist()
        if "word/document.xml" not in names:
            # Not a Word document we can normalise — leave it alone.
            return NormalisationReport()
        doc_xml = zin.read("word/document.xml")

    doc_root = etree.fromstring(doc_xml)

    report = NormalisationReport()
    report.accepted_revisions = _accept_tracked_changes(doc_root)
    colour_runs, highlight_runs, colour_details, highlight_details = (
        _strip_run_colour_and_highlight(doc_root)
    )
    report.runs_colour_stripped = colour_runs
    report.runs_highlight_stripped = highlight_runs
    report.colour_strips = colour_details
    report.highlight_strips = highlight_details
    report.guidance_paragraphs_deleted = _delete_guidance_paragraphs(doc_root)
    report.blank_paragraphs_removed = _remove_blank_paragraphs(doc_root)

    if not report.changed:
        return report

    new_doc_xml = etree.tostring(
        doc_root, xml_declaration=True, encoding="UTF-8", standalone=True
    )

    tmp_path = output_path + ".norm.tmp"
    with zipfile.ZipFile(output_path, "r") as zin, zipfile.ZipFile(
        tmp_path, "w", zipfile.ZIP_DEFLATED
    ) as zout:
        for item in zin.infolist():
            if item.filename == "word/document.xml":
                zout.writestr(item, new_doc_xml)
            else:
                zout.writestr(item, zin.read(item.filename))
    Path(tmp_path).replace(output_path)

    return report
