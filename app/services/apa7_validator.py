import re

from app.domain.apa7_template import APA7_STRUCTURE
from app.services.apa7_formatting_checks import (
    check_abstract_format,
    check_fonts,
    check_keywords_format,
    check_references_hanging_indent,
    check_references_heading_format,
    check_references_page_break,
)
from app.services.document_analysis_services import (
    parse_docx_structure,
)

_W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
_WQ = f"{{{_W}}}"


def _result(rule_id: str, status: str, message: str) -> dict:
    return {"rule_id": rule_id, "status": status, "message": message}


def strip_leading_section_number(text: str) -> str:
    return re.sub(r"^\d+(\.\d+)*\.?\s+", "", text).strip()


def subsection_alias_match(canonical: str, found_list: list[str]) -> bool:
    c_lower = canonical.strip().lower()
    for f in found_list:
        f_clean = strip_leading_section_number(f).strip().lower()
        if f_clean == c_lower:
            return True
    return False


def _matches_section(
    heading_text: str,
    canonical: str,
    aliases: list[str] | None = None,
) -> bool:
    h = strip_leading_section_number(heading_text).strip().lower()
    for name in [canonical] + (aliases or []):
        n = name.strip().lower()
        if h == n or h.startswith(n + ":"):
            return True
    return False


def _section_present(found_headings: list[str], canonical: str) -> bool:
    aliases = APA7_STRUCTURE["section_aliases"].get(canonical, [])
    return any(_matches_section(h, canonical, aliases) for h in found_headings)


def check_required_sections(parsed: dict) -> list[dict]:
    results = []
    found = parsed["main_sections"]
    aliases = APA7_STRUCTURE["section_aliases"]

    for i, section in enumerate(APA7_STRUCTURE["main_sections"]):
        rule_id = f"SEC{i + 1:03d}"
        section_aliases = aliases.get(section, [])

        if any(_matches_section(h, section, section_aliases) for h in found):
            results.append(_result(rule_id, "pass", f"'{section}' found"))
            continue

        combined = next(
            (h for h in found if section.lower() in h.lower()),
            None,
        )
        if combined:
            results.append(
                _result(
                    rule_id,
                    "fail",
                    f"'{section}' found combined with another section ('{combined}') — "
                    f"APA-7 requires it as a separate top-level section",
                )
            )
        else:
            # JB-07: Joey-phrased missing-section message; fall back to the
            # generic text only if a section lacks a map entry.
            message = (
                APA7_STRUCTURE.get("missing_section_queries", {}).get(section)
                or f"Required section '{section}' not found"
            )
            results.append(_result(rule_id, "fail", message))

    return results


def check_section_order(parsed: dict) -> list[dict]:
    found = parsed["main_sections"]
    canonical = APA7_STRUCTURE["main_sections"]
    aliases = APA7_STRUCTURE["section_aliases"]

    def canonical_index(name):
        for i, s in enumerate(canonical):
            if _matches_section(name, s, aliases.get(s, [])):
                return i
        return None

    indices = [canonical_index(s) for s in found if canonical_index(s) is not None]

    if indices == sorted(indices):
        return [_result("SEC009", "pass", "Sections are in the correct order")]

    return [_result("SEC009", "warn", "Sections are out of the expected order")]


def _looks_like_subheading(text: str) -> bool:
    t = (text or "").strip()
    return bool(t) and len(t) <= 80 and t[-1] not in ".!?"


def _extra_subheadings(found_subs: list[str], required: list[str]) -> list[str]:
    return [
        f
        for f in found_subs
        if _looks_like_subheading(f)
        and not any(subsection_alias_match(req, [f]) for req in required)
    ]


def check_method_subsections(parsed: dict) -> list[dict]:
    if not _section_present(parsed["main_sections"], "Method"):
        return []

    results = []
    found_subs = parsed["subsections"].get("Method", [])
    required = APA7_STRUCTURE["required_subsections"]["Method"]

    for i, sub in enumerate(required):
        rule_id = f"MET{i + 1:03d}"
        if subsection_alias_match(sub, found_subs):
            results.append(_result(rule_id, "pass", f"Method subsection '{sub}' found"))
        else:
            results.append(_result(rule_id, "fail", f"Required Method subsection '{sub}' missing"))

    return results


def check_discussion_subsections(parsed: dict) -> list[dict]:
    found = parsed["main_sections"]
    discussion_present = _section_present(found, "Discussion")
    required = APA7_STRUCTURE["required_subsections"]["Discussion"]

    if not discussion_present:
        return [
            _result(f"DIS{i + 1:03d}", "fail", f"Required Discussion subsection '{sub}' missing")
            for i, sub in enumerate(required)
        ]

    results = []
    found_subs = parsed["subsections"].get("Discussion", [])

    for i, sub in enumerate(required):
        rule_id = f"DIS{i + 1:03d}"
        if subsection_alias_match(sub, found_subs):
            results.append(_result(rule_id, "pass", f"Discussion subsection '{sub}' found"))
        else:
            results.append(
                _result(rule_id, "fail", f"Required Discussion subsection '{sub}' missing")
            )

    return results


def check_front_page(parsed: dict) -> list[dict]:
    fp = parsed["front_page"]
    checks = [
        ("FP001", fp["title_found"], "Article title found", "Article title not found"),
        ("FP002", fp["authors_found"], "Authors block found", "Authors block not found"),
        ("FP003", fp["affiliations_found"], "Affiliations block found", "Affiliations not found"),
        (
            "FP004",
            fp["abstract_heading_found"],
            "Abstract heading found",
            "The abstract and/or abstract heading is missing. APA 7 places a "
            "single-paragraph abstract, headed 'Abstract', on its own page after "
            "the title page. Please check your manuscript includes it.",
        ),
        (
            "FP006",
            fp["keywords_heading_found"],
            "Keywords heading found",
            "Keywords heading not found",
        ),
    ]
    return [
        _result(rule_id, "pass" if ok else "fail", pass_msg if ok else fail_msg)
        for rule_id, ok, pass_msg, fail_msg in checks
    ]


def check_abstract(parsed: dict) -> list[dict]:
    front = APA7_STRUCTURE["front_page"]
    abstract = parsed["front_page"]["abstract"]
    max_words = front["abstract_max_words"]

    # JB-06: when the heading itself is missing, FP004 already carries the
    # single consolidated missing-abstract comment — FP007/FP008 are
    # suppressed so the author sees one comment, not a triple-report.
    # A present heading with a zero-word body still fails FP007 on its own
    # (FP008's "length cannot be checked" is redundant noise).
    if not abstract["found"] or abstract["word_count"] == 0:
        if not parsed["front_page"]["abstract_heading_found"]:
            return []
        return [
            _result("FP007", "fail", "Abstract body not found"),
        ]

    wc = abstract["word_count"]
    if wc > max_words:
        msg = f"Abstract is too long: {wc} words (max {max_words})."
        status = "fail"
    else:
        msg = f"Abstract length OK ({wc} words, max {max_words})"
        status = "pass"

    return [
        _result("FP007", "pass", "Abstract body found"),
        _result("FP008", status, msg),
    ]


def check_keywords(parsed: dict) -> list[dict]:
    count = len(parsed["front_page"]["keywords"])
    max_count = APA7_STRUCTURE["front_page"]["keywords_max_count"]

    if count == 0:
        return [_result("FP010", "fail", "No keywords found")]
    if count <= max_count:
        return [_result("FP010", "pass", f"{count} keyword(s) found (max {max_count})")]
    return [_result("FP010", "fail", f"{count} keywords found — exceeds maximum of {max_count}")]


def build_report(results: list[dict]) -> dict:
    return {
        "total": len(results),
        "pass": sum(1 for r in results if r["status"] == "pass"),
        "warn": sum(1 for r in results if r["status"] == "warn"),
        "fail": sum(1 for r in results if r["status"] == "fail"),
        "results": results,
    }


def validate(docx_path: str) -> dict:
    parsed = parse_docx_structure(docx_path)

    results = []
    results += check_required_sections(parsed)
    results += check_section_order(parsed)
    results += check_method_subsections(parsed)
    results += check_discussion_subsections(parsed)
    results += check_front_page(parsed)
    results += check_abstract(parsed)
    results += check_keywords(parsed)
    results += check_fonts(docx_path)
    results += check_abstract_format(docx_path)
    results += check_keywords_format(docx_path)
    results += check_references_page_break(docx_path)
    results += check_references_heading_format(docx_path)
    results += check_references_hanging_indent(docx_path)

    # Ensure every result item contains matrix_id (C-20a)
    for res in results:
        if isinstance(res, dict) and "matrix_id" not in res:
            res["matrix_id"] = res.get("rule_id", "APA7-GENERIC")

    return build_report(results)
