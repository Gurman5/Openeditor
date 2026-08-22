"""Smoke test for reference_reconstructor and reference_format_corrections."""
from app.services.reference_reconstructor import (
    _format_single_author,
    build_apa7_from_crossref,
    detect_format_issues,
    format_author_list,
    references_are_equivalent,
)

PASS = 0
FAIL = 0

def check(label, got, expected):
    global PASS, FAIL
    if got == expected:
        print(f"  PASS  {label}")
        PASS += 1
    else:
        print(f"  FAIL  {label}")
        print(f"        got:      {got!r}")
        print(f"        expected: {expected!r}")
        FAIL += 1

def check_true(label, condition):
    global PASS, FAIL
    if condition:
        print(f"  PASS  {label}")
        PASS += 1
    else:
        print(f"  FAIL  {label}")
        FAIL += 1

# ── Author formatting ─────────────────────────────────────────────────────────
print("=== Author formatting ===")
check("Dorit -> D.",        _format_single_author({"family": "Maor",   "given": "Dorit"}),        "Maor, D.")
check("Jason D. -> J. D.", _format_single_author({"family": "Ensor",  "given": "Jason D."}),      "Ensor, J. D.")
check("V. E. stays",       _format_single_author({"family": "Fisher", "given": "V. E."}),         "Fisher, V. E.")
check("Jean-Baptiste",     _format_single_author({"family": "Dupont", "given": "Jean-Baptiste"}), "Dupont, J.-B.")
check("suffix Jr.",        _format_single_author({"family": "King",   "given": "M.", "suffix": "Jr."}), "King, M., Jr.")
check("org author",        _format_single_author({"name": "World Health Organization"}),           "World Health Organization")

print()
print("=== Author list rules ===")
one   = format_author_list([{"family": "Smith", "given": "J."}])
check("1 author no amp",  one, "Smith, J.")

two   = format_author_list([{"family": "Smith", "given": "J."}, {"family": "Jones", "given": "A."}])
check("2 authors amp",    two, "Smith, J., & Jones, A.")

twenty_one = [{"family": f"Auth{i}", "given": "A."} for i in range(1, 22)]
result_21 = format_author_list(twenty_one)
check_true("21+ ellipsis present",  "…" in result_21)
check_true("21+ no trailing amp",   not result_21.endswith("& Auth21, A."))
check_true("21+ last author last",  result_21.endswith("Auth21, A."))
check_true("21+ Auth19 included",   "Auth19, A." in result_21)

# ── Journal article reconstruction ───────────────────────────────────────────
print()
print("=== Journal article ===")
cr_journal = {
    "type": "journal-article",
    "author": [
        {"family": "Maor",   "given": "Dorit"},
        {"family": "Ensor",  "given": "Jason D."},
        {"family": "Fraser", "given": "Barry J."},
    ],
    "title": ["Doctoral supervision in virtual spaces"],
    "container-title": ["Higher Education Research &amp; Development"],
    "volume": 35,
    "issue": "1",
    "page": "172-188",
    "issued": {"date-parts": [[2015]]},
    "DOI": "10.1080/07294360.2015.1121206",
}
apa = build_apa7_from_crossref(cr_journal)
check_true("returns string",        apa is not None)
check_true("en dash in pages",      "–" in apa)
check_true("https://doi.org/",      "https://doi.org/" in apa)
check_true("HTML entity decoded",   "&amp;" not in apa)
check_true("volume(issue) correct", "35(1)" in apa)
check_true("authors formatted",     "Maor, D." in apa)
print(f"  output: {apa}")

# ── Book chapter ──────────────────────────────────────────────────────────────
print()
print("=== Book chapter ===")
cr_chapter = {
    "type": "book-chapter",
    "author": [{"family": "Taylor", "given": "Robert"}],
    "title": ["Chapter on methods"],
    "container-title": ["Handbook of research"],
    "editor": [{"family": "Smith", "given": "Alice B."}],
    "page": "23-45",
    "publisher": "Springer",
    "issued": {"date-parts": [[2021]]},
    "DOI": "10.1007/978-3-000000-0_2",
}
apa2 = build_apa7_from_crossref(cr_chapter)
check_true("returns string",    apa2 is not None)
check_true("pp. present",       "pp." in apa2)
check_true("(Ed.) present",     "(Ed.)" in apa2)
check_true("en dash in pages",  "–" in apa2)
check_true("In present",        "In Smith, A. B." in apa2)
print(f"  output: {apa2}")

# ── Dataset ───────────────────────────────────────────────────────────────────
print()
print("=== Dataset ===")
cr_data = {
    "type": "dataset",
    "author": [{"family": "Johnson", "given": "P."}],
    "title": ["Climate data"],
    "publisher": "NOAA",
    "issued": {"date-parts": [[2019]]},
    "DOI": "10.1000/data.1",
}
apa3 = build_apa7_from_crossref(cr_data)
check_true("returns string",    apa3 is not None)
check_true("[Data set] label",  "[Data set]" in apa3)
check_true("DOI url present",   "https://doi.org/" in apa3)
print(f"  output: {apa3}")

# ── detect_format_issues ──────────────────────────────────────────────────────
print()
print("=== detect_format_issues ===")

# Bad: hyphen page + missing DOI
bad = "Maor, D., Ensor, J. D., & Fraser, B. J. (2015). Title. Journal, 35(1), 172-188."
issues_bad = detect_format_issues(bad, apa, cr_journal)
check_true("hyphen page flagged",  any("page separator" in i for i in issues_bad))
check_true("missing DOI flagged",  any("missing DOI" in i for i in issues_bad))

# Bad: wrong DOI format (bare doi:)
bad_doi = "Maor, D. (2015). Title. Journal, 35(1), 172–188. doi:10.1080/07294360.2015.1121206"
issues_doi = detect_format_issues(bad_doi, apa, cr_journal)
check_true("wrong DOI format flagged", any("DOI format" in i for i in issues_doi))

# Bad: full names instead of initials
full_names = "Maor, Dorit, Ensor, Jason D., & Fraser, Barry J. (2015). Title. Journal, 35(1), 172–188."
issues_names = detect_format_issues(full_names, apa, cr_journal)
check_true("full names flagged",  any("author names" in i for i in issues_names))

# Good: correct reference — no issues
good = ("Maor, D., Ensor, J. D., & Fraser, B. J. (2015). "
        "Doctoral supervision in virtual spaces. "
        "Higher Education Research & Development, 35(1), 172–188. "
        "https://doi.org/10.1080/07294360.2015.1121206")
issues_good = detect_format_issues(good, apa, cr_journal)
check("correct ref: no issues", issues_good, [])
check_true("correct ref: equivalent", references_are_equivalent(good, apa))

# ── Type: None for unknown CrossRef type ──────────────────────────────────────
print()
print("=== Unknown type returns None ===")
cr_unknown = {"type": "grant", "title": ["Some grant"], "issued": {"date-parts": [[2020]]}}
check("unknown type -> None", build_apa7_from_crossref(cr_unknown), None)

print()
print(f"Results: {PASS} passed, {FAIL} failed")
if FAIL:
    raise SystemExit(1)
