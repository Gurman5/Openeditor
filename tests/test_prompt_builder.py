from app.domain.models import ParagraphRecord
from app.services.ai.prompt_builder import (
    VALID_CATEGORIES,
    build_prompts,
)

PACK = "tests/jutlp_sample_docx_test_pack"


def _make_paragraphs():
    """Build a minimal set of ParagraphRecord objects for testing."""
    return [
        ParagraphRecord(0, "Test Title Here", "Article Title", False),
        ParagraphRecord(1, "John Doe", "Authors", False),
        ParagraphRecord(2, "a University X, Country", "Author Affiliations", False),
        ParagraphRecord(3, "Abstract", "Heading Front Page", False),
        ParagraphRecord(
            4,
            "This study investigates the impact of teaching methods.",
            "Front Page Text",
            False,
        ),
        ParagraphRecord(5, "Practitioner Notes", "Heading Front Page", False),
        ParagraphRecord(6, "Note one about practice.", "Practitioner Notes", False),
        ParagraphRecord(7, "Note two about practice.", "Practitioner Notes", False),
        ParagraphRecord(8, "Keywords", "Heading Front Page", False),
        ParagraphRecord(9, "teaching, learning, AI", "Normal", False),
        ParagraphRecord(10, "Introduction", "Heading 1", False),
        ParagraphRecord(
            11,
            "This paper addresses the problem of engagement.",
            "Normal",
            False,
        ),
        ParagraphRecord(12, "Literature", "Heading 1", False),
        ParagraphRecord(13, "Prior work has shown mixed results.", "Normal", False),
        ParagraphRecord(14, "Method", "Heading 1", False),
        ParagraphRecord(15, "We used a mixed-methods approach.", "Normal", False),
        ParagraphRecord(16, "Results", "Heading 1", False),
        ParagraphRecord(17, "Participants reported higher engagement.", "Normal", False),
        ParagraphRecord(18, "Discussion", "Heading 1", False),
        ParagraphRecord(19, "The findings suggest practical value.", "Normal", False),
        ParagraphRecord(20, "Conclusion", "Heading 1", False),
        ParagraphRecord(21, "In summary, this study contributes.", "Normal", False),
    ]


def _make_parsed_structure():
    return {
        "front_page": {
            "title_found": True,
            "authors_found": True,
            "affiliations_found": True,
            "abstract_heading_found": True,
            "practitioner_notes_heading_found": True,
            "keywords_heading_found": True,
            "abstract": {
                "found": True,
                "paragraphs": [
                    ParagraphRecord(
                        4,
                        "This study investigates the impact of teaching methods.",
                        "Front Page Text",
                        False,
                    )
                ],
                "paragraph_count": 1,
                "word_count": 8,
            },
            "practitioner_notes_count": 2,
            "keywords": ["teaching", "learning", "AI"],
        },
        "main_sections": [
            "Introduction",
            "Literature",
            "Method",
            "Results",
            "Discussion",
            "Conclusion",
        ],
        "subsections": {
            "Method": [],
            "Discussion": [],
        },
        "style_counts": {},
    }


class TestSystemPrompt:
    def test_contains_guidelines(self):
        paragraphs = _make_paragraphs()
        parsed = _make_parsed_structure()
        system, _ = build_prompts(paragraphs, parsed)

        assert "JUTLP Editorial Guidelines" in system

    def test_contains_all_categories(self):
        paragraphs = _make_paragraphs()
        parsed = _make_parsed_structure()
        system, _ = build_prompts(paragraphs, parsed)

        for cat in VALID_CATEGORIES:
            assert cat in system

    def test_contains_activist_persona(self):
        paragraphs = _make_paragraphs()
        parsed = _make_parsed_structure()
        system, _ = build_prompts(paragraphs, parsed)

        # The persona was reworded to "activist sub-editor / copy editor".
        # Match the load-bearing tokens so minor future rewording doesn't
        # break the test, while still catching a complete persona-loss.
        assert "activist" in system
        assert ("copy editor" in system) or ("copy-editor" in system)

    def test_contains_exclusion_rules(self):
        paragraphs = _make_paragraphs()
        parsed = _make_parsed_structure()
        system, _ = build_prompts(paragraphs, parsed)

        assert "Do NOT flag" in system
        assert "references or citations" in system

    def test_contains_severity_labels(self):
        """The prompt instructs the LLM to use specific severity labels.

        Originally written when a migration from high/medium/low →
        requires_attention/advisory/minor was being trialled. That migration
        was rolled back: the prompt now uses high/medium/low and the
        downstream parser (llm_client.py) accepts BOTH vocabularies for
        backward compat. This test locks in the current vocabulary so a
        future accidental drift fails loudly.
        """
        paragraphs = _make_paragraphs()
        parsed = _make_parsed_structure()
        system, _ = build_prompts(paragraphs, parsed)

        assert "high" in system
        assert "medium" in system
        assert "low" in system


class TestUserPrompt:
    def test_contains_title(self):
        paragraphs = _make_paragraphs()
        parsed = _make_parsed_structure()
        _, user = build_prompts(paragraphs, parsed)

        assert "Test Title Here" in user

    def test_contains_authors(self):
        paragraphs = _make_paragraphs()
        parsed = _make_parsed_structure()
        _, user = build_prompts(paragraphs, parsed)

        assert "John Doe" in user

    def test_contains_keywords(self):
        paragraphs = _make_paragraphs()
        parsed = _make_parsed_structure()
        _, user = build_prompts(paragraphs, parsed)

        assert "teaching" in user
        assert "learning" in user

    def test_contains_abstract(self):
        paragraphs = _make_paragraphs()
        parsed = _make_parsed_structure()
        _, user = build_prompts(paragraphs, parsed)

        assert "investigates the impact of teaching methods" in user

    def test_practitioner_notes_numbered(self):
        paragraphs = _make_paragraphs()
        parsed = _make_parsed_structure()
        _, user = build_prompts(paragraphs, parsed)

        assert "1. Note one about practice." in user
        assert "2. Note two about practice." in user

    def test_contains_sections(self):
        paragraphs = _make_paragraphs()
        parsed = _make_parsed_structure()
        _, user = build_prompts(paragraphs, parsed)

        assert "## Section: Introduction" in user
        assert "## Section: Literature" in user
        assert "## Section: Method" in user
        assert "## Section: Results" in user
        assert "## Section: Discussion" in user
        assert "## Section: Conclusion" in user

    def test_contains_section_body_text(self):
        paragraphs = _make_paragraphs()
        parsed = _make_parsed_structure()
        _, user = build_prompts(paragraphs, parsed)

        assert "addresses the problem of engagement" in user
        assert "Prior work has shown mixed results" in user

    def test_omits_table_and_figure_text_from_section_body(self):
        paragraphs = [
            ParagraphRecord(0, "Introduction", "Heading 1", False),
            ParagraphRecord(1, "Table 1. One. Two. Three. Four.", "Normal", False),
            ParagraphRecord(2, "Mean score 4.5", "Table Text", False),
            ParagraphRecord(3, "Figure 2. One. Two. Three. Four.", "Normal", False),
            ParagraphRecord(4, "Caption text should be hidden.", "Caption", False),
            ParagraphRecord(5, "This body paragraph should remain.", "Normal", False),
            ParagraphRecord(6, "Literature", "Heading 1", False),
            ParagraphRecord(7, "Literature body.", "Normal", False),
            ParagraphRecord(8, "Method", "Heading 1", False),
            ParagraphRecord(9, "Method body.", "Normal", False),
        ]
        parsed = {
            **_make_parsed_structure(),
            "main_sections": ["Introduction", "Literature", "Method"],
        }
        _, user = build_prompts(paragraphs, parsed)

        assert "This body paragraph should remain" in user
        assert "Table 1" not in user
        assert "Mean score" not in user
        assert "Figure 2" not in user
        assert "Caption text" not in user

    def test_omits_table_and_figure_text_from_text_fallback_sections(self):
        paragraphs = [
            ParagraphRecord(0, "Title", "Article Title", False),
            ParagraphRecord(1, "Introduction", "Heading 1", False),
            ParagraphRecord(2, "Table 1. One. Two. Three. Four.", "Normal", False),
            ParagraphRecord(3, "Fallback body paragraph should remain.", "Normal", False),
            ParagraphRecord(4, "Method", "Normal", False),
            ParagraphRecord(5, "Figure 1. One. Two. Three. Four.", "Normal", False),
            ParagraphRecord(6, "Method body should remain.", "Normal", False),
        ]
        parsed = {**_make_parsed_structure(), "main_sections": ["Introduction"]}
        _, user = build_prompts(paragraphs, parsed)

        assert "Fallback body paragraph should remain" in user
        assert "Method body should remain" in user
        assert "Table 1" not in user
        assert "Figure 1" not in user

    def test_alias_section_headings_are_included(self):
        """Regression: sections headed by an ALIAS ("Methodology", "Findings",
        "Literature Review") — even when all are Heading-1 styled — must reach
        the LLM with their body text. Previously the style-based path matched
        section names by exact string and silently dropped alias headings, so
        the LLM reported them "not present in the manuscript"."""
        paragraphs = [
            ParagraphRecord(0, "Title", "Article Title", False),
            ParagraphRecord(1, "Introduction", "Heading 1", False),
            ParagraphRecord(2, "Intro body sentence.", "Normal", False),
            ParagraphRecord(3, "Literature Review", "Heading 1", False),
            ParagraphRecord(4, "Lit review body.", "Normal", False),
            ParagraphRecord(5, "Methodology", "Heading 1", False),
            ParagraphRecord(6, "We used surveys and interviews.", "Normal", False),
            ParagraphRecord(7, "Findings", "Heading 1", False),
            ParagraphRecord(8, "Participants reported gains.", "Normal", False),
            ParagraphRecord(9, "Discussion", "Heading 1", False),
            ParagraphRecord(10, "Implications discussed.", "Normal", False),
        ]
        parsed = {
            **_make_parsed_structure(),
            "main_sections": [
                "Introduction", "Literature Review", "Methodology",
                "Findings", "Discussion",
            ],
        }
        _, user = build_prompts(paragraphs, parsed)

        # Aliases are emitted under their canonical section names.
        assert "## Section: Literature" in user
        assert "## Section: Method" in user
        assert "## Section: Results" in user
        # …and crucially the body text of each is present.
        assert "Lit review body." in user
        assert "We used surveys and interviews." in user
        assert "Participants reported gains." in user

    def test_titled_heading_is_included(self):
        """A titled heading ("Introduction: Background") maps to its canonical
        section so its body is not dropped."""
        paragraphs = [
            ParagraphRecord(0, "Title", "Article Title", False),
            ParagraphRecord(1, "Introduction: Background and Motivation", "Heading 1", False),
            ParagraphRecord(2, "Intro body that must be seen.", "Normal", False),
            ParagraphRecord(3, "Method", "Heading 1", False),
            ParagraphRecord(4, "Method body.", "Normal", False),
        ]
        parsed = {
            **_make_parsed_structure(),
            "main_sections": ["Introduction: Background and Motivation", "Method"],
        }
        _, user = build_prompts(paragraphs, parsed)
        assert "## Section: Introduction" in user
        assert "Intro body that must be seen." in user

    def test_missing_title_style_falls_back_to_first_paragraph(self):
        paragraphs = [p for p in _make_paragraphs() if p.style != "Article Title"]
        parsed = _make_parsed_structure()
        _, user = build_prompts(paragraphs, parsed)

        # Without Article Title style, falls back to first non-empty paragraph.
        # Title header now includes the word count, e.g. "## Title (2 words; ...)".
        assert "## Title (" in user
        assert "Not found" not in user

    def test_missing_abstract_is_omitted(self):
        # When a front-page element is missing, the section must NOT appear
        # in the user prompt — the deterministic checker flags absence.
        # Including a "Not found" placeholder previously caused the LLM to
        # duplicate the deterministic check and produce redundant notes.
        paragraphs = [
            p for p in _make_paragraphs()
            if p.text != "Abstract" and p.style != "Front Page Text"
        ]
        parsed = _make_parsed_structure()
        _, user = build_prompts(paragraphs, parsed)

        assert "## Abstract" not in user
        assert "Not found" not in user


class TestBuildPromptsWithRealDocx:
    def test_with_valid_identified_docx(self):
        from app.services.document_analysis_services import (
            load_paragraphs,
            parse_docx_structure,
        )

        docx_path = f"{PACK}/01_valid_identified.docx"
        paragraphs = load_paragraphs(docx_path)
        parsed = parse_docx_structure(docx_path)

        system, user = build_prompts(paragraphs, parsed)

        assert len(system) > 500
        assert len(user) > 200
        assert "## Section: Introduction" in user
