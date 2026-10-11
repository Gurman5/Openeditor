"""Effective-format resolver (K-0.4a: basedOn chain + theme fonts,
K-0.4b: docDefaults, Word built-in defaults, numeric units).

Answers "what formatting does this run/paragraph actually get?" by walking,
for each property, from the most specific level to the least specific and
taking the first value found:

  run properties (font, size):
    run rPr -> character style chain (w:rStyle + basedOn) -> paragraph style
    chain -> docDefaults/rPrDefault -> Word built-in default
  paragraph properties (spacing, indent, alignment):
    paragraph pPr -> paragraph style chain (w:pStyle or the default paragraph
    style, + basedOn) -> docDefaults/pPrDefault -> Word built-in default

Spacing and indent are resolved attribute by attribute (line can come from
Normal while before comes from Heading1). firstLine and hanging are one
group: the first level that sets either one decides both.

Theme fonts (w:asciiTheme etc.) are looked up in word/theme/theme1.xml. On the
same w:rFonts element a theme attribute wins over an explicit w:ascii, as in Word.

Values are raw OOXML strings (size "22" = half-points, line "480" = 240ths of
a line when lineRule is auto, spacing/indents in twips). A value that came from
Word's built-in defaults has source "word-default". The "units" entry gives
the same values as numbers: points, line multiples and inches.
"""

from __future__ import annotations

from lxml import etree

from tools.corpus.docx_view import AcceptedView, RunView, accept_revisions, parse_xml, w

A_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"
PKG_REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
THEME_REL_TYPE = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/theme"

UNSET = "unset"
SPACING_ATTRS = ("line", "lineRule", "before", "after")
# Strict-mode names (start/end) are read as left/right.
_INDENT_SIDES = {"left": ("left", "start"), "right": ("right", "end")}
# Theme attribute suffix -> font slot in a:majorFont / a:minorFont.
_THEME_SLOTS = {"Ascii": "latin", "HAnsi": "latin", "EastAsia": "ea", "Bidi": "cs"}

# What Word uses when nothing in the document sets a value (source "word-default").
WORD_DEFAULT = "word-default"
WORD_DEFAULTS = {
    "font": "Times New Roman",
    "size": "20",                 # 10 pt
    "spacing.line": "240",        # single
    "spacing.lineRule": "auto",
    "spacing.before": "0",
    "spacing.after": "0",
    "indent.left": "0",
    "indent.right": "0",
    "align": "left",
}


def _read_theme_fonts(parts: dict[str, bytes]) -> dict[str, dict[str, str]]:
    """{"major": {"latin": ..., "ea": ..., "cs": ...}, "minor": {...}}."""
    theme_name = "word/theme/theme1.xml"
    rels = parts.get("word/_rels/document.xml.rels")
    if rels is not None:
        for rel in parse_xml(rels).iter(f"{{{PKG_REL_NS}}}Relationship"):
            if rel.get("Type") == THEME_REL_TYPE:
                theme_name = "word/" + rel.get("Target").lstrip("/").removeprefix("word/")
                break
    if theme_name not in parts:
        return {}

    theme = parse_xml(parts[theme_name])
    fonts: dict[str, dict[str, str]] = {}
    for kind in ("major", "minor"):
        scheme = theme.find(f".//{{{A_NS}}}{kind}Font")
        if scheme is None:
            continue
        fonts[kind] = {}
        for slot in ("latin", "ea", "cs"):
            el = scheme.find(f"{{{A_NS}}}{slot}")
            if el is not None and el.get("typeface"):
                fonts[kind][slot] = el.get("typeface")
    return fonts


class StyleResolver:
    """Style lookups for one document. Chains are cached per styleId."""

    def __init__(self, parts: dict[str, bytes]):
        self._styles: dict[str, etree._Element] = {}
        self.default_paragraph_style: str | None = None
        self.default_rpr: etree._Element | None = None   # docDefaults/rPrDefault/rPr
        self.default_ppr: etree._Element | None = None   # docDefaults/pPrDefault/pPr
        if "word/styles.xml" in parts:
            # Accepting revisions drops rPrChange/pPrChange snapshots in styles too.
            styles = accept_revisions(parse_xml(parts["word/styles.xml"]))
            defaults = styles.find(w("docDefaults"))
            if defaults is not None:
                self.default_rpr = defaults.find(f"{w('rPrDefault')}/{w('rPr')}")
                self.default_ppr = defaults.find(f"{w('pPrDefault')}/{w('pPr')}")
            for s in styles.iter(w("style")):
                sid = s.get(w("styleId"))
                self._styles[sid] = s
                if (s.get(w("type")) == "paragraph"
                        and s.get(w("default")) in ("1", "true", "on")):
                    self.default_paragraph_style = sid
        self.theme_fonts = _read_theme_fonts(parts)
        self._chains: dict[str | None, list[tuple[str, etree._Element]]] = {}

    def chain(self, style_id: str | None) -> list[tuple[str, etree._Element]]:
        """[(styleId, <w:style>), ...] from style_id down its basedOn chain.
        Stops at a missing style or a loop."""
        if style_id not in self._chains:
            out, seen, sid = [], set(), style_id
            while sid is not None and sid not in seen and sid in self._styles:
                seen.add(sid)
                style = self._styles[sid]
                out.append((sid, style))
                based = style.find(w("basedOn"))
                sid = based.get(w("val")) if based is not None else None
            self._chains[style_id] = out
        return self._chains[style_id]

    def paragraph_style_id(self, p: etree._Element) -> str | None:
        ps = p.find(f"{w('pPr')}/{w('pStyle')}")
        sid = ps.get(w("val")) if ps is not None else None
        return sid if sid in self._styles else self.default_paragraph_style

    # -- levels: (source label, rPr/pPr element), most specific first ------

    def _style_levels(self, style_id, tag):
        return [(f"style:{sid}", s.find(w(tag))) for sid, s in self.chain(style_id)]

    def run_levels(self, r: etree._Element, p: etree._Element):
        levels = []
        rpr = r.find(w("rPr"))
        if rpr is not None:
            levels.append(("direct", rpr))
            rstyle = rpr.find(w("rStyle"))
            if rstyle is not None:
                levels += self._style_levels(rstyle.get(w("val")), "rPr")
        levels += self._style_levels(self.paragraph_style_id(p), "rPr")
        levels.append(("docDefaults", self.default_rpr))
        return [(src, el) for src, el in levels if el is not None]

    def paragraph_levels(self, p: etree._Element):
        levels = [("direct", p.find(w("pPr")))]
        levels += self._style_levels(self.paragraph_style_id(p), "pPr")
        levels.append(("docDefaults", self.default_ppr))
        return [(src, el) for src, el in levels if el is not None]

    # -- property resolution ----------------------------------------------

    def theme_font(self, theme_attr: str) -> str:
        kind = "major" if theme_attr.startswith("major") else "minor"
        slot = _THEME_SLOTS.get(theme_attr[len(kind):], "latin")
        return self.theme_fonts.get(kind, {}).get(slot, UNSET)

    def resolve_paragraph(self, p: etree._Element) -> dict:
        levels = self.paragraph_levels(p)
        sources: dict[str, str] = {}

        def first(tag, attrs, key):
            """First level whose <tag> has any of `attrs` (checked per level)."""
            for src, ppr in levels:
                el = ppr.find(w(tag))
                if el is None:
                    continue
                for attr in attrs:
                    if el.get(w(attr)) is not None:
                        sources[key] = src
                        return el.get(w(attr))
            return UNSET

        spacing = {a: first("spacing", (a,), f"spacing.{a}") for a in SPACING_ATTRS}

        indent = {side: first("ind", names, f"indent.{side}")
                  for side, names in _INDENT_SIDES.items()}
        indent["firstLine"] = indent["hanging"] = UNSET
        for src, ppr in levels:
            ind = ppr.find(w("ind"))
            if ind is not None and (ind.get(w("firstLine")) is not None
                                    or ind.get(w("hanging")) is not None):
                for key in ("firstLine", "hanging"):
                    if ind.get(w(key)) is not None:
                        indent[key] = ind.get(w(key))
                        sources[f"indent.{key}"] = src
                break
        if indent["firstLine"] == indent["hanging"] == UNSET:
            indent["firstLine"] = indent["hanging"] = "0"
            sources["indent.firstLine"] = sources["indent.hanging"] = WORD_DEFAULT

        result = {"spacing": spacing, "indent": indent,
                  "align": first("jc", ("val",), "align"), "sources": sources}
        _fill_word_defaults(result)
        result["units"] = paragraph_units(result)
        return result

    def resolve_run(self, r: etree._Element, p: etree._Element) -> dict:
        levels = self.run_levels(r, p)
        sources: dict[str, str] = {}

        font = UNSET
        for src, rpr in levels:
            rf = rpr.find(w("rFonts"))
            if rf is None:
                continue
            theme_attr = rf.get(w("asciiTheme"))
            if theme_attr:
                font = self.theme_font(theme_attr)
                sources["font"] = f"{src} (theme {theme_attr})"
                break
            if rf.get(w("ascii")):
                font = rf.get(w("ascii"))
                sources["font"] = src
                break

        size = UNSET
        for src, rpr in levels:
            sz = rpr.find(w("sz"))
            if sz is not None and sz.get(w("val")) is not None:
                size = sz.get(w("val"))
                sources["size"] = src
                break

        result = {"font": font, "size": size, "sources": sources}
        _fill_word_defaults(result)
        return result


def _fill_word_defaults(result: dict) -> None:
    """Replace "unset" values with Word's built-in defaults (source "word-default").
    Keys are "font"/"size"/"align" or "<group>.<attr>" for spacing/indent.
    A value some level DID set but that could not be read (a theme font missing
    from theme1.xml) already has a source, so it stays "unset"."""
    for key, default in WORD_DEFAULTS.items():
        group, _, attr = key.partition(".")
        if group not in result:
            continue
        holder, name = (result[group], attr) if attr else (result, group)
        if holder[name] == UNSET and key not in result["sources"]:
            holder[name] = default
            result["sources"][key] = WORD_DEFAULT


# --------------------------------------------------------------------------
# Numeric units
# --------------------------------------------------------------------------

def _num(value) -> float | None:
    """Raw OOXML number -> float; None for "unset" or anything unreadable."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _div(value, by: float) -> float | None:
    n = _num(value)
    return None if n is None else round(n / by, 4)


def paragraph_units(para: dict) -> dict:
    """Spacing/indent/alignment as numbers: points, line multiples, inches.
    first_line_in is negative for a hanging indent."""
    spacing, indent = para["spacing"], para["indent"]
    rule = spacing["lineRule"] if spacing["lineRule"] != UNSET else "auto"
    hanging = _num(indent["hanging"])
    if hanging:
        first_line_in = round(-hanging / 1440, 4)
    else:
        first_line_in = _div(indent["firstLine"], 1440)
    align = {"start": "left", "end": "right"}.get(para["align"], para["align"])
    return {
        "line_rule": rule,
        "line_multiple": _div(spacing["line"], 240) if rule == "auto" else None,
        "line_pt": _div(spacing["line"], 20) if rule in ("exact", "atLeast") else None,
        "before_pt": _div(spacing["before"], 20),
        "after_pt": _div(spacing["after"], 20),
        "left_in": _div(indent["left"], 1440),
        "right_in": _div(indent["right"], 1440),
        "first_line_in": first_line_in,
        "align": None if align == UNSET else align,
    }


def get_resolver(doc: AcceptedView) -> StyleResolver:
    """The cached StyleResolver for an AcceptedView (built on first use)."""
    resolver = getattr(doc, "_style_resolver", None)
    if resolver is None:
        resolver = StyleResolver(doc.parts)
        doc._style_resolver = resolver
    return resolver


def _owning_paragraph(r: etree._Element) -> etree._Element:
    p = r.getparent()
    while p is not None and p.tag != w("p"):
        p = p.getparent()
    if p is None:
        raise ValueError("run is not inside a w:p")
    return p


def resolve_effective(run: RunView | etree._Element, doc: AcceptedView) -> dict:
    """Agreed interface: effective formatting of one run.

    Returns {"font", "size", "spacing": {line, lineRule, before, after},
    "indent": {left, right, firstLine, hanging}, "align", "sources", "units"}.
    Each value is a raw OOXML string; "sources" says which level supplied each
    value (e.g. "direct", "style:Normal (theme minorHAnsi)", "docDefaults",
    "word-default"). "units" holds the same values as numbers (size_pt,
    line_multiple / line_pt, before_pt, after_pt, left_in, right_in,
    first_line_in, align); unreadable numbers are None.
    A theme font whose theme1.xml entry is missing stays "unset".
    """
    r = run.element if isinstance(run, RunView) else run
    p = _owning_paragraph(r)
    resolver = get_resolver(doc)
    para = resolver.resolve_paragraph(p)
    run_props = resolver.resolve_run(r, p)
    return {
        "font": run_props["font"],
        "size": run_props["size"],
        "spacing": para["spacing"],
        "indent": para["indent"],
        "align": para["align"],
        "sources": {**para["sources"], **run_props["sources"]},
        "units": {"size_pt": _div(run_props["size"], 2), **para["units"]},
    }


def resolve_paragraph(paragraph, doc: AcceptedView) -> dict:
    """Effective spacing/indent/align of a paragraph (works with no runs)."""
    p = getattr(paragraph, "element", paragraph)
    return get_resolver(doc).resolve_paragraph(p)
