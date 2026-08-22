"""LLM-driven keyword generation for manuscripts missing a Keywords section.

JUTLP's template requires a Keywords section directly under Practitioner
Notes — "Max. 5, 1 line, no abbreviations" per the editor's guidance. When
the author has omitted the section, the front-page restyling pass already
inserts an empty `Keywords` heading and a "please add 5 keywords" comment.
This module generates a starter set of 5 keyword candidates from the
manuscript's title + abstract so the editor receives a draft list as a
tracked insertion rather than an empty placeholder.

Design notes:

* **Generation, not edit.** Existing LLM passes (`grammar_corrections`,
  `sentence_coherence_corrections`, `body_llm_edits`) all propose
  modifications to existing prose. This pass produces NEW text drawn from
  title + abstract context.
* **Best-effort.** Any failure path (`LLMError`, empty abstract, all
  candidates filtered out) returns an empty list. The caller falls back
  to the heading-only stub + the original "please add" comment, so the
  pipeline still does something useful when the LLM is down.
* **No acronyms.** Per the front-page template note. Single-token uppercase
  candidates are dropped.
* **Length cap.** Each keyword must be 1-4 words; longer entries are
  multi-concept and unsuitable for a Keywords line.
* **Case-insensitive dedupe.** Returned list contains no duplicates.
"""

from __future__ import annotations

import re

from app.services.ai.llm_client import LLMError, call_llm_json

# Hard caps -----------------------------------------------------------------

# Maximum keywords ever returned. Per JUTLP template ("Max. 5").
_MAX_KEYWORDS = 5

# Maximum words per keyword. Multi-word phrases like "professional learning
# communities" are fine; 5+ word phrases are over-specific.
_MAX_WORDS_PER_KEYWORD = 4

# Minimum abstract length before we bother calling the LLM. Abstracts
# shorter than ~30 chars are typically a heading marker the parser
# misidentified — we'd just burn tokens producing junk.
_MIN_ABSTRACT_CHARS = 30


_KEYWORDS_SCHEMA = {
    "name": "keywords_generation",
    "strict": True,
    "schema": {
        "type": "object",
        "properties": {
            "keywords": {
                "type": "array",
                "items": {"type": "string"},
            },
        },
        "required": ["keywords"],
        "additionalProperties": False,
    },
}


_SYSTEM_PROMPT = """\
You are an editor for the Journal of University Teaching and Learning
Practice (JUTLP) generating a Keywords list for a manuscript that omitted
one.

Your ONLY task is to produce exactly five short keywords that describe the
manuscript's topic, drawn from its title and abstract.

Rules:
1. Return exactly five keywords.
2. Each keyword is 1-4 words. No full sentences, no clauses.
3. NO acronyms or initialisms (per JUTLP template: "no abbreviations").
   Write `artificial intelligence`, not `AI`. Write `peer review`, not `PR`.
4. Use lowercase except for proper nouns (e.g. `Bloom's taxonomy`,
   `Australia`). Do not capitalise common nouns.
5. Keywords should be DISTINCT — do not list near-synonyms
   (`learning` and `learnings`, `students` and `student`).
6. Avoid generic filler words like "study", "research", "paper",
   "analysis" — these add no discoverability.
7. Prefer the manuscript's own terminology where it appears in the
   title or abstract.
"""


def _build_user_prompt(title: str, abstract: str) -> str:
    return (
        "Generate five Keywords for this manuscript.\n\n"
        f"Title: {title.strip()}\n\n"
        f"Abstract: {abstract.strip()}"
    )


# Acronym = 2+ consecutive uppercase letters, optionally with a trailing
# lowercase `s` (e.g. `LMSs`). Mirrors the heuristic used in
# `grammar_corrections._ACRONYM_RE`.
_ACRONYM_RE = re.compile(r"\b[A-Z]{2,}s?\b")

# Generic filler words that contribute nothing to discoverability. We drop
# any keyword that IS one of these wholesale.
_GENERIC_FILLER = frozenset({
    "study", "research", "paper", "analysis", "article",
    "investigation", "review", "examination",
})


def _clean_one(raw: str) -> str:
    """Strip surrounding whitespace and quotes; collapse internal whitespace."""
    s = raw.strip().strip('"').strip("'").strip()
    s = re.sub(r"\s+", " ", s)
    return s


def _is_acceptable(keyword: str) -> bool:
    if not keyword:
        return False
    if _ACRONYM_RE.search(keyword):
        return False
    words = keyword.split()
    if not words or len(words) > _MAX_WORDS_PER_KEYWORD:
        return False
    if keyword.lower() in _GENERIC_FILLER:
        return False
    # Defensive: reject anything that contains a sentence terminator —
    # almost certainly the LLM regressing to phrasal output.
    if any(ch in keyword for ch in ".!?"):
        return False
    return True


def _dedupe_case_insensitive(keywords: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for k in keywords:
        key = k.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(k)
    return out


def generate_keywords(title: str, abstract: str) -> list[str]:
    """Return up to ``_MAX_KEYWORDS`` keyword candidates for the manuscript.

    Best-effort: returns ``[]`` when the LLM is unavailable, the abstract is
    too short to derive a meaningful keyword set, or every candidate fails
    the post-validation gate. Callers should treat ``[]`` as "fall back to
    the placeholder comment".
    """
    title = (title or "").strip()
    abstract = (abstract or "").strip()
    if len(abstract) < _MIN_ABSTRACT_CHARS:
        return []

    try:
        result = call_llm_json(
            system_prompt=_SYSTEM_PROMPT,
            user_prompt=_build_user_prompt(title, abstract),
            response_schema=_KEYWORDS_SCHEMA,
        )
    except LLMError:
        return []

    raw = result.get("content", {}).get("keywords", []) or []
    cleaned = [_clean_one(k) for k in raw if isinstance(k, str)]
    filtered = [k for k in cleaned if _is_acceptable(k)]
    deduped = _dedupe_case_insensitive(filtered)
    return deduped[:_MAX_KEYWORDS]
