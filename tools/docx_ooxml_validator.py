"""Schema-shape checks for generated .docx files.

``python-docx`` opens a file and ``lxml`` parses it happily even when the XML
violates ECMA-376 in ways Word refuses to load -- Word reports "unreadable
content" and offers to repair the file instead. This module asserts the
structural rules Word actually enforces, so the pipeline output can be checked
without a human opening Word.

Usage::

    python tools/docx_ooxml_validator.py path/to/output.docx [more.docx ...]

Exit code is 0 when every file passes, 1 otherwise.
"""
from __future__ import annotations

import sys
import zipfile
from collections import Counter

from lxml import etree

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
WQ = f"{{{W}}}"
W14 = "{http://schemas.microsoft.com/office/word/2010/wordml}"
W15 = "{http://schemas.microsoft.com/office/word/2012/wordml}"

# CT_Settings children that may appear in the w: namespace. Anything else in
# that namespace is an invented element and Word will not load the file.
SETTINGS_ALLOWED = {
    "writeProtection", "view", "zoom", "removePersonalInformation", "removeDateAndTime",
    "doNotDisplayPageBoundaries", "displayBackgroundShape", "printPostScriptOverText",
    "printFractionalCharacterWidth", "printFormsData", "embedTrueTypeFonts",
    "embedSystemFonts", "saveSubsetFonts", "saveFormsData", "mirrorMargins",
    "alignBordersAndEdges", "bordersDoNotSurroundHeader", "bordersDoNotSurroundFooter",
    "gutterAtTop", "hideSpellingErrors", "hideGrammaticalErrors", "activeWritingStyle",
    "proofState", "formsDesign", "attachedTemplate", "linkStyles",
    "stylePaneFormatFilter", "stylePaneSortMethod", "documentType", "mailMerge",
    "revisionView", "trackChanges", "doNotTrackMoves", "doNotTrackFormatting",
    "documentProtection", "autoFormatOverride", "styleLockTheme", "styleLockQFSet",
    "defaultTabStop", "autoHyphenation", "consecutiveHyphenLimit", "hyphenationZone",
    "doNotHyphenateCaps", "showEnvelope", "summaryLength", "clickAndTypeStyle",
    "defaultTableStyle", "evenAndOddHeaders", "bookFoldRevPrinting", "bookFoldPrinting",
    "bookFoldPrintingSheets", "drawingGridHorizontalSpacing",
    "drawingGridVerticalSpacing", "displayHorizontalDrawingGridEvery",
    "displayVerticalDrawingGridEvery", "doNotUseMarginsForDrawingGridOrigin",
    "drawingGridHorizontalOrigin", "drawingGridVerticalOrigin", "doNotShadeFormData",
    "noPunctuationKerning", "characterSpacingControl", "printTwoOnOne",
    "strictFirstAndLastChars", "noLineBreaksAfter", "noLineBreaksBefore",
    "savePreviewPicture", "doNotValidateAgainstSchema", "saveInvalidXml",
    "ignoreMixedContent", "alwaysShowPlaceholderText", "doNotDemarcateInvalidXml",
    "saveXmlDataOnly", "useXSLTWhenSaving", "saveThroughXslt", "showXMLTags",
    "alwaysMergeEmptyNamespace", "updateFields", "hdrShapeDefaults", "footnotePr",
    "endnotePr", "compat", "docVars", "rsids", "attachedSchema", "themeFontLang",
    "clrSchemeMapping", "doNotIncludeSubdocsInStats", "doNotAutoCompressPictures",
    "forceUpgrade", "captions", "readModeInkLockDown", "smartTagType", "shapeDefaults",
    "doNotEmbedSmartTags", "decimalSymbol", "listSeparator",
}

# CT_TrackChangesView permits exactly these attributes.
REVISION_VIEW_ATTRS = {"markup", "comments", "insDel", "formatting", "inkAnnotations"}

# CT_Row / CT_Tc / CT_P: the *Pr property element must be first when present.
PR_FIRST_CHILD = {
    "w:p": "w:pPr",
    "w:tr": "w:trPr",
    "w:tc": "w:tcPr",
    "w:tbl": "w:tblPr",
    "w:r": "w:rPr",
}


def local(tag) -> str:
    return tag.split("}")[-1] if isinstance(tag, str) and "}" in tag else str(tag)


def _check_parts_parse(zf: zipfile.ZipFile, errors: list[str]) -> None:
    for name in zf.namelist():
        if name.endswith((".xml", ".rels")):
            try:
                etree.fromstring(zf.read(name))
            except Exception as exc:  # noqa: BLE001
                errors.append(f"{name}: not well-formed XML: {exc}")


def _check_settings(zf: zipfile.ZipFile, errors: list[str]) -> None:
    if "word/settings.xml" not in zf.namelist():
        return
    root = etree.fromstring(zf.read("word/settings.xml"))
    for child in root:
        if not child.tag.startswith(WQ):
            continue
        if local(child.tag) not in SETTINGS_ALLOWED:
            errors.append(
                f"word/settings.xml: <w:{local(child.tag)}> is not a valid CT_Settings child"
            )
    rev = root.find(f"{WQ}revisionView")
    if rev is not None:
        attrs = {local(k) for k in rev.attrib}
        bad = sorted(attrs - REVISION_VIEW_ATTRS)
        if bad:
            errors.append(f"word/settings.xml: <w:revisionView> has invalid attributes {bad}")


def _check_property_elements_first(root: etree._Element, errors: list[str]) -> None:
    offenders: Counter = Counter()
    detail: dict[str, str] = {}
    for tag, pr_tag in PR_FIRST_CHILD.items():
        for el in root.iter(f"{WQ}{tag.split(':')[1]}"):
            kids = list(el)
            if not kids:
                continue
            pr = el.find(f"{WQ}{pr_tag.split(':')[1]}")
            if pr is not None and kids[0] is not pr:
                key = f"{tag}/{local(kids[0].tag)}"
                offenders[key] += 1
                detail[key] = (
                    f"ECMA-376 requires <{pr_tag}> to be the first child of <{tag}>, "
                    f"but <{local(kids[0].tag)}> comes first"
                )
    for key, count in offenders.items():
        errors.append(f"{detail[key]} ({count} occurrence{'' if count == 1 else 's'})")


def _check_comments(zf: zipfile.ZipFile, root: etree._Element, errors: list[str]) -> None:
    starts = [e.get(f"{WQ}id") for e in root.iter(f"{WQ}commentRangeStart")]
    ends = [e.get(f"{WQ}id") for e in root.iter(f"{WQ}commentRangeEnd")]
    refs = [e.get(f"{WQ}id") for e in root.iter(f"{WQ}commentReference")]
    defined: list[str] = []
    comments_root = None
    if "word/comments.xml" in zf.namelist():
        comments_root = etree.fromstring(zf.read("word/comments.xml"))
        defined = [c.get(f"{WQ}id") for c in comments_root.findall(f"{WQ}comment")]

    dangling = sorted((set(starts) | set(ends) | set(refs)) - set(defined))
    if dangling:
        errors.append(f"comment anchors with no matching w:comment: {dangling}")

    unmatched = Counter(starts) - Counter(ends)
    if unmatched:
        errors.append(f"commentRangeStart without commentRangeEnd: {dict(unmatched)}")

    dupes = {i: c for i, c in Counter(starts).items() if c > 1}
    if dupes:
        errors.append(f"duplicate commentRangeStart ids: {dict(dupes)}")

    # Word 2013+ threaded-comment sidecars, all keyed by w14:paraId.
    _check_comment_sidecars(zf, comments_root, errors)


def _check_comment_sidecars(zf: zipfile.ZipFile, comments_root, errors: list[str]) -> None:
    sidecars = [
        p
        for p in ("word/commentsExtended.xml", "word/commentsIds.xml", "word/commentsExtensible.xml")
        if p in zf.namelist()
    ]
    if not sidecars:
        return

    if comments_root is None:
        errors.append(
            f"threaded-comment sidecars {sidecars} present but there is no word/comments.xml"
        )
        return

    live = {
        para.get(f"{W14}paraId")
        for comment in comments_root.findall(f"{WQ}comment")
        for para in comment.findall(f"{WQ}p")
        if para.get(f"{W14}paraId") is not None
    }
    if not live:
        errors.append(
            f"threaded-comment sidecars {sidecars} present but no w:comment carries a "
            f"w14:paraId; Word cannot match them and will refuse to open the file"
        )
        return

    for part in sidecars:
        root = etree.fromstring(zf.read(part))
        referenced = {
            next((v for k, v in child.attrib.items() if k.split("}")[-1] == "paraId"), None)
            for child in root
        }
        referenced.discard(None)
        orphans = sorted(referenced - live)
        if orphans:
            errors.append(
                f"{part} references {len(orphans)} paraId(s) absent from comments.xml, "
                f"e.g. {orphans[:5]}"
            )


def _check_revisions(root: etree._Element, errors: list[str]) -> None:
    ids = [e.get(f"{WQ}id") for e in root.iter() if local(e.tag) in ("ins", "del")]
    dupes = {i: c for i, c in Counter(ids).items() if c > 1}
    if dupes:
        errors.append(f"duplicate revision w:id values: {dict(dupes)}")
    for d in root.iter(f"{WQ}del"):
        if any(True for _ in d.iter(f"{WQ}t")):
            errors.append("tracked deletion uses <w:t>; ECMA-376 requires <w:delText>")
            break


def validate(path: str) -> list[str]:
    """Return a list of problems; empty means the file passes."""
    errors: list[str] = []
    try:
        with zipfile.ZipFile(path) as zf:
            bad = zf.testzip()
            if bad is not None:
                errors.append(f"corrupt zip entry: {bad}")
            if "word/document.xml" not in zf.namelist():
                errors.append("missing word/document.xml")
                return errors
            _check_parts_parse(zf, errors)
            if "word/document.xml" in zf.namelist():
                root = etree.fromstring(zf.read("word/document.xml"))
                _check_property_elements_first(root, errors)
                _check_comments(zf, root, errors)
                _check_revisions(root, errors)
            _check_settings(zf, errors)
    except zipfile.BadZipFile as exc:
        errors.append(f"not a valid .docx (zip) container: {exc}")
    return errors


def main(argv: list[str]) -> int:
    if not argv:
        print(__doc__)
        return 2
    failed = False
    for path in argv:
        problems = validate(path)
        if problems:
            failed = True
            print(f"FAIL {path}")
            for p in problems:
                print(f"  - {p}")
        else:
            print(f"PASS {path}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
