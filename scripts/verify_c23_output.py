"""
Runs build_edited_document on the 01_valid_identified.docx fixture and asserts
the APA 7 heading treatment C-23 landed in the output:

  APA-11  Heading 1-5 style definitions carry the right alignment, weight,
          indent, spacing, font and keepNext for each level
  APA-11  no heading paragraph carries a direct w:jc that would override the
          style (the old CENTER_ALIGNED_HEADING_TEXTS policy wrote one)
  APA-11  heading paragraphs keep their paragraph-level keepNext
  APA-11  Heading 2 text is title case

The old text-matching policy is what this replaces: it could not tell Level 1
from Level 2, so it centred every listed section heading regardless of level.
"""
# TODO: Delete script after completion of Track C
import os
import re
import shutil
import sys
import tempfile
import zipfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lxml import etree

from app.services.output_generation_samfix import build_edited_document

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
WQ = f"{{{W}}}"
SRC = "tests/jutlp_sample_docx_test_pack/01_valid_identified.docx"

# level -> (expected jc, bold, italic, left indent)
APA11 = {
    1: ("center", True, False, None),
    2: ("left", True, False, None),
    3: ("left", True, True, None),
    4: ("left", True, False, "720"),
    5: ("left", True, True, "720"),
}

failures = []


def check(label, ok, detail=""):
    status = "PASS" if ok else "FAIL"
    print(f"  [{status}] {label}" + (f"  -- {detail}" if detail else ""))
    if not ok:
        failures.append(label)


def flag_on(el):
    if el is None:
        return False
    return el.get(f"{WQ}val") not in ("0", "false", "off")


tmp = tempfile.mkdtemp(prefix="c23_")
src = os.path.join(tmp, "in.docx")
out = os.path.join(tmp, "out.docx")
shutil.copy(SRC, src)
build_edited_document(src, out)
print("built:", out, os.path.getsize(out), "bytes")
print()

z = zipfile.ZipFile(out)
names = z.namelist()
doc_root = etree.fromstring(z.read("word/document.xml"))
styles_root = etree.fromstring(z.read("word/styles.xml"))

styles_by_id = {
    st.get(f"{WQ}styleId"): st for st in styles_root.findall(f"{WQ}style")
}

print("== APA-11 heading style definitions (C-23) ==")
for level, (exp_jc, exp_bold, exp_italic, exp_left) in APA11.items():
    style_el = styles_by_id.get(f"Heading{level}")
    check(f"Heading {level} style present", style_el is not None)
    if style_el is None:
        continue

    p_pr = style_el.find(f"{WQ}pPr")
    r_pr = style_el.find(f"{WQ}rPr")
    check(f"Heading {level} has pPr", p_pr is not None)
    if p_pr is None:
        continue

    jc = p_pr.find(f"{WQ}jc")
    got_jc = jc.get(f"{WQ}val") if jc is not None else None
    check(f"Heading {level} jc={exp_jc}", got_jc == exp_jc, f"got {got_jc}")

    sp = p_pr.find(f"{WQ}spacing")
    check(f"Heading {level} line=480",
          sp is not None and sp.get(f"{WQ}line") == "480",
          sp.get(f"{WQ}line") if sp is not None else None)
    check(f"Heading {level} after=0",
          sp is not None and sp.get(f"{WQ}after") in (None, "0"),
          sp.get(f"{WQ}after") if sp is not None else None)
    check(f"Heading {level} before=0 (no Word default)",
          sp is not None and sp.get(f"{WQ}before") in (None, "0"),
          sp.get(f"{WQ}before") if sp is not None else None)

    check(f"Heading {level} keepNext on style",
          p_pr.find(f"{WQ}keepNext") is not None)

    ind = p_pr.find(f"{WQ}ind")
    if exp_left is None:
        left = ind.get(f"{WQ}left") if ind is not None else None
        hanging = ind.get(f"{WQ}hanging") if ind is not None else None
        check(f"Heading {level} flush left (no indent)",
              left in (None, "0") and hanging is None,
              f"left={left} hanging={hanging}")
    else:
        check(f"Heading {level} ind left={exp_left}",
              ind is not None and ind.get(f"{WQ}left") == exp_left,
              ind.get(f"{WQ}left") if ind is not None else None)

    check(f"Heading {level} has rPr", r_pr is not None)
    if r_pr is not None:
        check(f"Heading {level} bold={exp_bold}",
              flag_on(r_pr.find(f"{WQ}b")) is exp_bold)
        check(f"Heading {level} italic={exp_italic}",
              flag_on(r_pr.find(f"{WQ}i")) is exp_italic)
        fonts = r_pr.find(f"{WQ}rFonts")
        got_font = fonts.get(f"{WQ}ascii") if fonts is not None else None
        check(f"Heading {level} font=Calibri (C-27/D2)",
              got_font == "Calibri", f"got {got_font}")
        check(f"Heading {level} hAnsi/cs=Calibri, no theme binding (C-27)",
              fonts is not None
              and fonts.get(f"{WQ}hAnsi") == "Calibri"
              and fonts.get(f"{WQ}cs") == "Calibri"
              and fonts.get(f"{WQ}asciiTheme") is None
              and fonts.get(f"{WQ}hAnsiTheme") is None,
              f"hAnsi={fonts.get(f'{WQ}hAnsi') if fonts is not None else None}")
print()


def heading_paras():
    body = doc_root.find(f"{WQ}body")
    for p in body.iter(f"{WQ}p"):
        p_style = p.find(f"{WQ}pPr/{WQ}pStyle")
        if p_style is None:
            continue
        sid = p_style.get(f"{WQ}val", "")
        if sid.startswith("Heading") and sid[-1:].isdigit():
            yield sid, p


print("== heading paragraphs free of direct overrides ==")
count = 0
bad_jc = no_keep_next = 0
level2_texts = []
for sid, p in heading_paras():
    count += 1
    if p.find(f"{WQ}pPr/{WQ}jc") is not None:
        bad_jc += 1
        print(f"    direct jc on {sid}: "
              f"{p.find(f'{WQ}pPr/{WQ}jc').get(f'{WQ}val')}")
    if p.find(f"{WQ}pPr/{WQ}keepNext") is None:
        no_keep_next += 1
    if sid == "Heading2":
        level2_texts.append("".join(t.text or "" for t in p.iter(f"{WQ}t")).strip())

check(f"found {count} heading paragraph(s)", count > 0, f"{count} found")
check("no heading carries a direct w:jc", bad_jc == 0, f"{bad_jc} bad")
check("every heading paragraph has keepNext", no_keep_next == 0, f"{no_keep_next} missing")
print()

print("== APA-11 title case on Heading 2 ==")
print("  Heading 2 texts:", level2_texts)

#> APA-11: articles, coordinating conjunctions and prepositions of four or
#> fewer letters stay lower case in title case - unless they lead the heading.
APA_TITLECASE_EXEMPT = {
    "a", "an", "the",
    "and", "but", "or", "nor", "for", "yet", "so",
    "at", "by", "in", "of", "on", "to", "up", "as", "off", "out", "via",
    "from", "into", "onto", "over", "with", "per",
}

for text in level2_texts:
    words = [w for w in re.split(r"\s+", text) if w]
    bad = []
    for i, word in enumerate(words):
        if not word.isalpha():
            continue
        if i == 0:
            # The first word is always capitalised, whatever it is.
            if not word[0].isupper():
                bad.append(word)
        elif word.lower() in APA_TITLECASE_EXEMPT:
            # Exempt words must actually be lower case in APA title case.
            if word[0].isupper():
                bad.append(word)
        elif not word[0].isupper():
            bad.append(word)
    check(f"title case: {text!r}", not bad, f"wrongly cased: {bad}")
print()

print("RESULT:", "PASS" if not failures else f"FAIL ({len(failures)}: {failures})")
print("output kept at:", out)
raise SystemExit(0 if not failures else 1)
