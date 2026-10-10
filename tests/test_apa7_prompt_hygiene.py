"""Regression guard: no JUTLP-era strings may appear in the LLM prompts.

Track D (APA 7 retarget). Every prompt the LLM layer emits must be free of
JUTLP house-style references, the 15-word title limit, Practitioner Notes,
and the CRediT taxonomy. Fails if any of those leak back in.
"""

from app.domain.apa7_editorial_examples import APA7_EDITORIAL_EXAMPLES
from app.domain.apa7_guidelines import APA7_GUIDELINES
from app.services.ai import prompt_builder
from app.services.body_llm_edits import BODY_EDIT_SYSTEM_PROMPT
from app.services.grammar_corrections import _SYSTEM_PROMPT as GRAMMAR_PROMPT
from app.services.keywords_generation import (
    _SYSTEM_PROMPT as KEYWORDS_PROMPT,
    _build_user_prompt as keywords_user_prompt,
)
from app.services.sentence_coherence_corrections import (
    _SYSTEM_PROMPT as COHERENCE_PROMPT,
    _build_user_prompt as coherence_user_prompt,
)

FORBIDDEN = (
    "jutlp",              # JUTLP / jutlp / JUTLP_TITLE_WORD_LIMIT
    "practitioner notes",
    "credit",             # CRediT / credit.niso.org
    "15 word",
    "15-word",
)


def test_no_jutlp_strings_in_prompts():
    prompts = [
        ("guidelines", APA7_GUIDELINES),
        ("examples", APA7_EDITORIAL_EXAMPLES),
        ("prompt_builder.system", prompt_builder._build_system_prompt(None, None)),
        ("prompt_builder.user", prompt_builder._build_user_prompt([], {})),
        ("body_llm_edits.system", BODY_EDIT_SYSTEM_PROMPT),
        ("grammar.system", GRAMMAR_PROMPT),
        ("coherence.system", COHERENCE_PROMPT),
        ("coherence.user", coherence_user_prompt(["A simple, complete sentence."])),
        ("keywords.system", KEYWORDS_PROMPT),
        ("keywords.user", keywords_user_prompt("A title", "A long enough abstract.")),
    ]

    failures = []
    for label, text in prompts:
        lowered = text.lower()
        for bad in FORBIDDEN:
            if bad in lowered:
                failures.append(f"{label}: {bad!r}")
    assert not failures, "Forbidden strings found:\n" + "\n".join(failures)
