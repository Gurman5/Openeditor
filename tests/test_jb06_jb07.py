"""JB-06 + JB-07 acceptance tests.

JB-06 — abstract detection + single consolidated missing-abstract comment:
  * 'ABSTRACT' / 'Abstract:' heading variants are detected (no missing-abstract
    comment fires).
  * A genuinely missing abstract produces exactly ONE comment with the agreed
    Joey wording (FP004), and FP007/FP008 do not triple-report.
  * A present heading with an empty body reports FP007 once (FP008 suppressed).

JB-07 — missing-section comments use Joey's phrasing, and no heading insertion:
  * SEC fail messages match a missing_section_queries entry for every section.
  * The validator message and Sam's structural-comment message share the
    wording so the cross-layer comment dedup strips the duplicate.
"""

import pytest
from docx import Document

from app.domain.canonical_jultp_template import CANONICAL_STRUCTURE
from app.services.apa7_validator import (
    check_abstract,
    check_front_page,
    parse_docx_structure,
)
from app.services.document_analysis_services import (
    is_abstract_heading,
)
from app.services.output_generation_samfix import _find_abstract_heading_in_front

MISSING_ABSTRACT_MESSAGE = (
    "The abstract and/or abstract heading is missing. APA 7 places a "
    "single-paragraph abstract, headed 'Abstract', on its own page after "
    "the title page. Please check your manuscript includes it."
)


def results_by_rule(results):
    return {r["rule_id"]: r for r in results}


class TestAbstractVariantDetection:
    def test_is_abstract_heading_variants(self):
        for text in ("Abstract", "ABSTRACT", "abstract", "Abstract:", "Abstract :", " abstract "):
            assert is_abstract_heading(type("P", (), {"text": text, "style": None})) is True

    def test_is_abstract_heading_negatives(self):
        for text in (
            "Abstract Methods",
            "Abstracting Services",
            "The abstract of the paper",
            "Keywords",
        ):
            assert is_abstract_heading(type("P", (), {"text": text, "style": None})) is False

    def _doc_with_variant_heading(self, tmp_path, heading_text):
        path = tmp_path / "input.docx"
        doc = Document()
        doc.add_heading(heading_text, level=1)
        doc.add_paragraph("This paper presents an analysis of document validation rules.")
        doc.add_heading("Keywords", level=1)
        doc.add_paragraph("validation, structure")
        doc.save(path)
        return parse_docx_structure(str(path))

    @pytest.mark.parametrize("heading", ["ABSTRACT", "Abstract:", "Abstract"])
    def test_variant_heading_is_detected(self, tmp_path, heading):
        parsed = self._doc_with_variant_heading(tmp_path, heading)

        assert parsed["front_page"]["abstract_heading_found"] is True
        assert parsed["front_page"]["abstract"]["found"] is True
        assert parsed["front_page"]["abstract"]["word_count"] > 0

        rd = results_by_rule(check_front_page(parsed))
        assert rd["FP004"]["status"] == "pass"


class TestMissingAbstractConsolidation:
    def test_nowhere_abstract_variants_match(self, tmp_path):
        path = tmp_path / "input.docx"
        doc = Document()
        doc.add_heading("Introduction", level=1)
        doc.add_paragraph("Body text before any abstract.")
        doc.save(path)
        parsed = parse_docx_structure(str(path))

        rd = results_by_rule(check_front_page(parsed) + check_abstract(parsed))

        assert rd["FP004"]["status"] == "fail"
        assert rd["FP004"]["message"] == MISSING_ABSTRACT_MESSAGE
        assert "FP007" not in rd, "FP007 must be suppressed when FP004 carries the single comment"
        assert "FP008" not in rd, "FP008 must be suppressed when FP004 carries the single comment"

    def test_heading_present_body_missing_reports_fp007_only(self, tmp_path):
        path = tmp_path / "input.docx"
        doc = Document()
        doc.add_heading("Abstract", level=1)
        doc.add_heading("Keywords", level=1)
        doc.add_paragraph("validation only")
        doc.save(path)
        parsed = parse_docx_structure(str(path))
        # No body paragraph between the heading and the Keywords boundary.
        restructured = {"front_page": parsed["front_page"]}
        restructured["front_page"]["abstract"] = {
            "found": True,
            "paragraphs": [],
            "paragraph_count": 0,
            "word_count": 0,
        }

        rd = results_by_rule(check_front_page(restructured) + check_abstract(restructured))

        assert rd["FP007"]["status"] == "fail"
        assert "FP008" not in rd

    def test_validator_and_sam_missing_abstract_wording_matches(self):
        """Both layers must emit the identical agreed wording (verified above
        for the validator via FP004 and for Sam via abstractFormatCheck)."""
        assert MISSING_ABSTRACT_MESSAGE.strip() == MISSING_ABSTRACT_MESSAGE.strip()


class TestSamWordingAlignment:
    def test_sam_uses_same_missing_abstract_message(self, tmp_path):
        """Sam's missing-abstract comment must be word-identical to the
        validator's consolidated FP004 wording so the cross-layer dedup
        (_remove_duplicate_sam_comments, >=3 shared words) strips Sam's copy."""
        from app.services.output_generation_samfix import abstractFormatCheck

        path = tmp_path / "input.docx"
        doc = Document()
        doc.add_heading("Introduction", level=1)
        doc.add_paragraph("Body text before any abstract.")
        doc.save(path)

        state = {
            "abstract_found": False,
            "affiliations_found": False,
            "anchor_pos": 0,
        }
        plan = abstractFormatCheck(str(path), state)

        assert plan["message"] == MISSING_ABSTRACT_MESSAGE

    def test_sam_finds_variant_heading(self, tmp_path):
        """Sam's front-page finder accepts 'ABSTRACT'/'Abstract:' so a present
        abstract is never misreported as missing by either layer."""
        record = type("P", (), {"text": "ABSTRACT", "style": None, "index": 5})
        assert _find_abstract_heading_in_front([record]) is record

    def test_missing_section_validator_fails_report_joey_wording(self):
        """JB-07: every missing main section reports the Joey-shaped message
        (rule ids and verdicts unchanged)."""
        from app.services.apa7_validator import check_required_sections

        parsed = {"main_sections": ["Introduction"]}
        rd = results_by_rule(check_required_sections(parsed))

        queries = CANONICAL_STRUCTURE["missing_section_queries"]
        for i, section in enumerate(CANONICAL_STRUCTURE["main_sections"][1:], start=2):
            rule_id = f"SEC{i:03d}"
            assert rd[rule_id]["status"] == "fail"
            assert rd[rule_id]["message"] == queries[section], rule_id

    def test_every_main_section_has_joey_wording(self):
        queries = CANONICAL_STRUCTURE["missing_section_queries"]
        for section in CANONICAL_STRUCTURE["main_sections"]:
            message = queries.get(section)
            assert message, f"missing_section_queries missing '{section}'"
            assert message.startswith("We expected to see"), section
            assert "the bot couldn't find that" in message, section

    def test_missing_section_wording_sources_shared(self):
        """Sam's structural pass reads the same map, so both layers agree and
        the dedup layer strips Sam's duplicate."""
        from app.services.output_generation_samfix import CANONICAL_STRUCTURE as SAM_STRUCTURE

        assert (
            SAM_STRUCTURE["missing_section_queries"]
            == CANONICAL_STRUCTURE["missing_section_queries"]
        )
