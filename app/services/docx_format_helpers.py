"""Shared low-level helpers for the tracked formatting passes (C-25/C-26/C-27).

Font helpers (C-27 + the APA002 check) live here so the sweep and the check
cannot disagree about what "wrong font" means. Heading helpers arrive with
C-25 (``find_canonical_heading``, ``set_tracked_ppr``).

All helpers operate on lxml elements inside a ``.docx`` zip part and never
touch the zip itself — callers own reading/writing.
"""

from __future__ import annotations

from lxml import etree

from app.services.config import DEFAULT_FONT
from app.services.language_corrections import WQ

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
