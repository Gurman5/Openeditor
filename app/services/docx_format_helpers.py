"""Shared low-level helpers for the tracked formatting passes (C-25/C-26/C-27).

Font helpers (C-27 + the APA002 check) live here so the sweep and the check
cannot disagree about what "wrong font" means. Heading helpers (C-25) give the
References and front-matter passes one way to find a heading and record a
tracked paragraph-property change.

All helpers operate on lxml elements inside a ``.docx`` zip part and never
touch the zip itself — callers own reading/writing.
"""

from __future__ import annotations

from copy import deepcopy

from lxml import etree

from app.services.config import DEFAULT_FONT
from app.services.language_corrections import AUTHOR, DATE, WQ

# Run-font attributes carrying an explicit typeface, in the order Word
# resolves them.
FONT_ATTRS = ("ascii", "hAnsi", "eastAsia", "cs")

# Theme-bound counterparts: a run carrying only these resolves through
# word/theme/theme1.xml (minor font = Cambria in our template), NOT through
# the paragraph style — so it must be rewritten to an explicit font.
THEME_ATTRS = ("asciiTheme", "hAnsiTheme", "eastAsiaTheme", "cstheme")


def is_symbol_font(name: str | None) -> bool:
    """True for typefaces that must never be normalised (equations, symbols).

    Mirrors the exclusion already used for table runs in
    ``output_generation_samfix`` — a ∑ set in Symbol that the sweep rewrote
    to Calibri would silently corrupt the manuscript.
    """
    if not name:
        return False
    from app.services.config import SYMBOL_FONTS

    return name.strip().lower() in SYMBOL_FONTS


def rfonts_explicit(rfonts_el: etree._Element | None) -> dict[str, str]:
    """Return the explicit ``{attr: typeface}`` map of a ``w:rFonts`` element."""
    if rfonts_el is None:
        return {}
    out: dict[str, str] = {}
    for attr in FONT_ATTRS:
        val = rfonts_el.get(f"{WQ}{attr}")
        if val:
            out[attr] = val
    return out


def rfonts_theme(rfonts_el: etree._Element | None) -> dict[str, str]:
    """Return the theme-bound ``{attr: theme}`` map of a ``w:rFonts`` element."""
    if rfonts_el is None:
        return {}
    out: dict[str, str] = {}
    for attr in THEME_ATTRS:
        val = rfonts_el.get(f"{WQ}{attr}")
        if val:
            out[attr] = val
    return out


def rfonts_needs_fix(
    rfonts_el: etree._Element | None,
    char_style_fonts: dict[str, str] | None = None,
    target: str = DEFAULT_FONT,
) -> str | None:
    """Classify why a run's fonts need normalising, or return None.

    Returns ``"explicit"`` when a non-symbol explicit typeface differs from
    ``target``, ``"theme"`` when the run is theme-bound with no usable
    explicit font, ``"char-style"`` when it inherits a wrong font from a
    linked character style — else None (already correct, symbol, or plainly
    inheriting from the paragraph style, which the styles.xml sweep owns).
    """
    target_low = (target or "").strip().lower()
    explicit = rfonts_explicit(rfonts_el)

    # A run whose Latin slots are symbol typefaces renders symbols — the
    # sweep must not touch it (font or size decisions for such runs belong
    # to the author).
    latin = [explicit.get(a, "") for a in ("ascii", "hAnsi")]
    if any(is_symbol_font(v) for v in latin if v):
        return None

    wrong = [
        v for v in explicit.values()
        if v and v.strip().lower() != target_low and not is_symbol_font(v)
    ]
    if wrong:
        return "explicit"
    if explicit:
        # Explicit fonts present and all correct (or symbol-only in
        # non-Latin slots) — nothing to do.
        return None
    if rfonts_theme(rfonts_el):
        # No explicit typeface: resolves through the Office theme, not the
        # paragraph style. Our template's minor font is Cambria, so this
        # run does NOT render in the target font.
        return "theme"
    if char_style_fonts:
        wrong_cs = [
            v for v in char_style_fonts.values()
            if v and v.strip().lower() != target_low and not is_symbol_font(v)
        ]
        if wrong_cs:
            return "char-style"
    return None


def strip_theme_font_attrs(rfonts_el: etree._Element) -> bool:
    """Remove ``*Theme`` attributes; True when anything was removed."""
    removed = False
    for attr in THEME_ATTRS:
        key = f"{WQ}{attr}"
        if key in rfonts_el.attrib:
            del rfonts_el.attrib[key]
            removed = True
    return removed


def set_explicit_font(
    rfonts_el: etree._Element,
    target: str = DEFAULT_FONT,
) -> bool:
    """Pin every non-symbol Latin slot to ``target``; True when changed.

    Slots already carrying a symbol typeface are left alone (mixed-script
    runs keep their symbol coverage); theme attributes are stripped so the
    explicit value wins.
    """
    changed = strip_theme_font_attrs(rfonts_el)
    for attr in FONT_ATTRS:
        key = f"{WQ}{attr}"
        current = rfonts_el.get(key)
        if current is not None and is_symbol_font(current):
            continue
        if current != target:
            rfonts_el.set(key, target)
            changed = True
    return changed


# ── Heading lookup (C-25 / C-26) ─────────────────────────────────────────


def normalise_heading_text(text: str) -> str:
    """Lower-case, strip a leading section number and trailing ``:``/``.``.

    Matches the normalisation ``canonical_jultp_template._normalise_subsection``
    applies, so a lookup agrees with the alias map the validators use.
    """
    if not text:
        return ""
    from app.domain.canonical_jultp_template import _normalise_subsection

    return _normalise_subsection(text)


def paragraph_text(para_el: etree._Element) -> str:
    """All ``w:t`` text of a paragraph (including tracked deletions/insertions)."""
    return "".join(t.text or "" for t in para_el.iter(f"{WQ}t")).strip()


def get_or_add_ppr(para_el: etree._Element) -> etree._Element:
    """Return the paragraph's ``w:pPr``, creating it as the first child."""
    p_pr = para_el.find(f"{WQ}pPr")
    if p_pr is None:
        p_pr = etree.Element(f"{WQ}pPr")
        para_el.insert(0, p_pr)
    return p_pr


def heading_names(canonical: str) -> list[str]:
    """Canonical heading label plus every registered alias, normalised."""
    from app.domain.canonical_jultp_template import CANONICAL_STRUCTURE

    names = [canonical]
    names.extend(CANONICAL_STRUCTURE.get("section_aliases", {}).get(canonical, []))
    return {normalise_heading_text(n) for n in names if n}


def find_canonical_heading(
    body_paras: list[etree._Element],
    canonical: str,
    text_only: bool = False,
) -> etree._Element | None:
    """Find the paragraph that heads a canonical section, by TEXT.

    Deliberately text-based: an author who marked "References" as bold Normal
    text (not ``Heading 1``) must still be found, or the fixer would skip a
    section that is plainly present and the checker would report it missing —
    the same reasoning that closed that gap for structure validation.

    ``text_only=True`` additionally requires the paragraph NOT to carry a
    heading style, which is how a caller asks "is this a pseudo-heading I
    should promote?".
    """
    names = heading_names(canonical)
    for para_el in body_paras:
        text = normalise_heading_text(paragraph_text(para_el))
        if text not in names:
            continue
        if text_only and para_style_id(para_el).lower().startswith("heading"):
            continue
        return para_el
    return None


def para_style_id(para_el: etree._Element) -> str:
    p_pr = para_el.find(f"{WQ}pPr")
    if p_pr is None:
        return ""
    p_style = p_pr.find(f"{WQ}pStyle")
    return p_style.get(f"{WQ}val", "") if p_style is not None else ""


def set_para_style(para_el: etree._Element, style_id: str) -> None:
    p_pr = get_or_add_ppr(para_el)
    p_style = p_pr.find(f"{WQ}pStyle")
    if p_style is None:
        p_style = etree.Element(f"{WQ}pStyle")
        p_pr.insert(0, p_style)
    p_style.set(f"{WQ}val", style_id)


def set_tracked_ppr(
    para_el: etree._Element,
    tag: str,
    attrs: dict[str, str],
    change_id: int,
) -> int:
    """Apply one paragraph property as a tracked change; returns the next id.

    A paragraph may carry only ONE ``w:pPrChange``, so an existing one is
    reused (it already holds the pre-change snapshot) and the new property is
    inserted before it — mirroring the reuse logic in
    ``reference_indent_corrections``. ``w:pPrChange`` must stay the LAST child
    of ``w:pPr`` or Word rejects the part.
    """
    p_pr = get_or_add_ppr(para_el)
    existing = p_pr.find(f"{WQ}pPrChange")
    old_p_pr = deepcopy(p_pr) if existing is None else None

    # Drop the property this call owns, then rebuild it. Other direct
    # properties on the paragraph are left alone.
    for el in p_pr.findall(f"{WQ}{tag}"):
        p_pr.remove(el)

    new_el = etree.Element(f"{WQ}{tag}")
    for key, val in attrs.items():
        new_el.set(f"{WQ}{key}", val)

    if existing is not None:
        existing.addprevious(new_el)
    else:
        p_pr.append(new_el)
        change = etree.SubElement(p_pr, f"{WQ}pPrChange")
        change.set(f"{WQ}id", str(change_id))
        change.set(f"{WQ}author", AUTHOR)
        change.set(f"{WQ}date", DATE)
        change.append(old_p_pr)
        return change_id + 1
    return change_id


def has_tracked_page_break_before(para_el: etree._Element) -> bool:
    """True when ``para_el`` starts a new page.

    Accepts the property form (``w:pageBreakBefore``) and the run form (a
    trailing ``<w:br w:type="page"/>`` inside the paragraph), because authors
    use both and the validator accepts both.
    """
    p_pr = para_el.find(f"{WQ}pPr")
    if p_pr is not None:
        pb = p_pr.find(f"{WQ}pageBreakBefore")
        if pb is not None:
            val = (pb.get(f"{WQ}val", "true") or "true").lower()
            if val not in ("false", "0", "off"):
                return True
    for br in para_el.iter(f"{WQ}br"):
        if br.get(f"{WQ}type") == "page":
            return True
    return False
