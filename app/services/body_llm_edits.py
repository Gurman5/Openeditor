"""LLM-generated surgical copy-edits for the document body.

Produces tracked-change edits (word/short-phrase replacements) for the prose
between the first body heading and the References section. Designed to NEVER
propose paragraph rewrites — the LLM schema, prompt, and post-validation all
enforce that constraint.
"""

import logging
import re

from app.services.ai.llm_client import LLMError, call_llm_json
from app.services.document_analysis_services import (
    get_section_bounds,
    load_paragraphs,
)
from app.services.grammar_corrections import _is_au_to_us_replacement
from app.services.language_corrections import AU_CORRECTIONS

log = logging.getLogger(__name__)

# Pairs that must never be changed in either direction
_BLOCKED_PAIRS: frozenset[tuple[str, str]] = frozenset({
    ("program", "programme"),
    ("programs", "programmes"),
    ("people", "peoples"),
    ("peoples", "people"),
    ("language", "languages"),
    ("languages", "language"),
    ("culture", "cultures"),
    ("cultures", "culture"),
    ("knowledge", "knowledges"),
    ("knowledges", "knowledge"),
})

# Source phrases the LLM must never touch, regardless of what `replace` is.
# These are domain terms or wordings where prior LLM passes produced wrong
# edits (e.g. singularising "parallel texts", which is a corpus-linguistics
# term of art; swapping "equality" for "equity"; inserting an extra "s" into
# "AI tool companies"). Matched case-sensitively as exact substrings of
# `find`.
_PROTECTED_TERMS: frozenset[str] = frozenset({
    "parallel texts",
    "language equality",
    "AI tool companies",
    "Differently,",
    "differently,",
    "Indigenous",
    "indigenous",
    "Country",
    "on Country",
})

# Tokens that, when inserted or removed by a single-content-word edit, are
# almost always meaning-shifts the author did not request.
_HEDGING_AND_DISCOURSE_TOKENS: frozenset[str] = frozenset({
    "may", "might", "could", "possibly", "perhaps",
    "contrast", "however", "nevertheless",
})

# Auxiliary/modal pairs whose swap is a tense flip the author didn't write.
_AUXILIARY_TOKENS: frozenset[str] = frozenset({
    "is", "was", "are", "were", "has", "had", "have",
    "do", "did", "does",
    "will", "would", "shall", "should", "can", "could",
})

_REASON_CATEGORY_TERMS: frozenset[str] = frozenset({
    "abbreviation",
    "agreement",
    "australian",
    "capitalisation",
    "capitalization",
    "format",
    "formatting",
    "grammar",
    "grammatical",
    "homophone",
    "latin",
    "localisation",
    "localization",
    "pluralisation",
    "pluralization",
    "punctuation",
    "spelling",
    "style",
    "subject-verb",
    "us->au",
    "us to au",
})


def _strip_quotes(text: str) -> str:
    """Normalise curly quotes/apostrophes to ASCII for comparison only."""
    return (
        text
        .replace("‘", "'")
        .replace("’", "'")
        .replace("“", '"')
        .replace("”", '"')
    )


def _token_diff(find_text: str, replace_text: str) -> tuple[list[str], list[str]] | None:
    """Return the symmetric token difference between ``find`` and ``replace``.

    Tokens are word-character runs. Returns ``(only_in_find, only_in_replace)``
    representing tokens that differ. Returns ``None`` when the two strings
    share no common tokens (the edit is a large rewrite, not a tweak).
    """
    f_tokens = re.findall(r"[A-Za-z']+", find_text)
    r_tokens = re.findall(r"[A-Za-z']+", replace_text)
    f_lower = [t.lower() for t in f_tokens]
    r_lower = [t.lower() for t in r_tokens]
    common = set(f_lower) & set(r_lower)
    if not common and (f_tokens or r_tokens):
        return None
    only_f = [t for t, lo in zip(f_tokens, f_lower) if lo not in r_lower]
    only_r = [t for t, lo in zip(r_tokens, r_lower) if lo not in f_lower]
    return only_f, only_r


def _fix_au_spellings(text: str) -> str:
    """Replace any US spellings in text with AU equivalents."""
    def _replace(m: re.Match) -> str:
        word = m.group(0)
        au = AU_CORRECTIONS.get(word.lower())
        if au is None:
            return word
        if word.isupper():
            return au.upper()
        if word[0].isupper():
            return au[0].upper() + au[1:]
        return au
    return re.sub(r'\b[A-Za-z]+\b', _replace, text)


def _reason_identifies_change(reason: str, find_text: str, replace_text: str) -> bool:
    """Return True when the LLM reason is specific enough for display."""
    reason = (reason or "").strip()
    if not reason:
        return False
    folded = reason.casefold()
    if any(term in folded for term in _REASON_CATEGORY_TERMS):
        return True
    if re.search(r"\bAU\b", reason) is not None:
        return True
    return find_text.casefold() in folded and replace_text.casefold() in folded

SKIP_STYLES = {
    "Heading 1",
    "Heading 2",
    "Heading 3",
    "Caption",
    "APA 7 Reference List Entry",
    "Authors",
    "Author Affiliations",
    "Article Title",
}

MIN_PARAGRAPH_CHARS = 40
MAX_EDITS_PER_PARAGRAPH = 5
MAX_FIND_WORDS = 6
MAX_FIND_CHARS = 80
REPLACE_LENGTH_RATIO = 2.5


BODY_EDIT_SCHEMA = {
    "name": "body_edit_suggestions",
    "strict": True,
    "schema": {
        "type": "object",
        "properties": {
            "edits": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "find": {"type": "string"},
                        "replace": {"type": "string"},
                        "reason": {"type": "string"},
                    },
                    "required": ["find", "replace", "reason"],
                    "additionalProperties": False,
                },
            },
        },
        "required": ["edits"],
        "additionalProperties": False,
    },
}


BODY_EDIT_SYSTEM_PROMPT = (
    "You are a copy-editor for the Journal of University Teaching and Learning Practice "
    "(JUTLP). The journal uses Australian English and APA 7. You review one paragraph of "
    "an academic manuscript and return a JSON list of SURGICAL word- or short-phrase-"
    "level corrections only.\n"
    "\n"
    "STRICT RULES — violations must be rejected by you before returning:\n"
    "1. Each `find` must be an EXACT, case-sensitive, verbatim substring of the input paragraph.\n"
    "2. Each `find` must be at most 6 words and at most 80 characters.\n"
    "3. Each `replace` must be similar in length to `find` (never more than ~2x as long).\n"
    "4. Do NOT paraphrase, reword, merge sentences, or change meaning.\n"
    "5. If the correct fix would require rewriting the sentence, SKIP the edit entirely.\n"
    "\n"
    "SPELLING DIRECTION — CRITICAL:\n"
    "   Convert spelling variants to JUTLP house style ONLY. Never reverse the direction.\n"
    "   - Correct direction (convert): utilize->utilise, center->centre, analyze->analyse, "
    "organization->organisation, color->colour, behavior->behaviour, programme->program."
    "\n"
    "   - Leave UNCHANGED (these are already Australian): utilise, centre, analyse, "
    "organisation, colour, behaviour, focussed, focused (both accepted), harmonised, "
    "harmonized (both accepted), program, recognise, practise (verb), "
    "practice (noun), licence (noun), license (verb), travelled, labelled, -ise endings, "
    "-our endings, -re endings, -ll- doubled forms.\n"
    "   If a word is ALREADY in an acceptable Australian form, do NOT propose an edit "
    "for it. When in doubt, leave the word alone.\n"
    "\n"
    "ALLOWED EDIT CATEGORIES:\n"
    "   a. US -> AU spelling and programme -> program house style (one-directional, as above).\n"
    "   b. Incorrect pluralisation where the singular/plural mismatch is objective "
    "(e.g. syllabi vs syllabuses where the singular is syllabus, datum vs data).\n"
    "   c. Clear grammar errors:\n"
    "      - Subject-verb agreement (e.g. 'the students was' -> 'the students were').\n"
    "      - Wrong homophones: there/their/they're, its/it's, affect/effect, then/than, "
    "to/too, your/you're.\n"
    "      Subject-verb agreement: only propose when the subject is the ONLY clause-level "
    "noun phrase. If the sentence has a complex subject ('A and B are', 'one of X is', "
    "'data storage, X, and Y are'), leave it.\n"
    "   d. Latin and scholarly abbreviation punctuation: et.al. -> et al., ie -> i.e., "
    "eg -> e.g., cf -> cf., etc -> etc. (with appropriate full stops).\n"
    "\n"
    "DISALLOWED / UNCERTAIN (SKIP SILENTLY):\n"
    "   - Article insertions or removals (a/an/the) — do NOT propose these.\n"
    "   - Indigenous/indigenous casing — retain the author's preference.\n"
    "   - Hyphenation decisions (compound modifiers) — do NOT propose these.\n"
    "   - Apostrophe / quotation-mark style — do NOT propose curly->straight substitutions. "
    "If the source already uses ' or \" keep them; if it uses ' or \" keep those. Never flip.\n"
    "   - Tense changes between past and present (is/was, are/were, has/had, share/shared, "
    "etc.) — do NOT propose these. The author's tense reflects a deliberate framing choice.\n"
    "   - Hedging insertions. Do NOT insert words such as 'may', 'might', 'could', "
    "'possibly', 'perhaps' that the author did not write.\n"
    "   - Discourse-marker rewrites (e.g. 'differently'->'by contrast', "
    "'however'->'nevertheless') — do NOT propose these.\n"
    "   - Word swaps that change meaning, even when both forms are grammatical (e.g. "
    "'equality'->'equity', 'supposed'->'suggested', 'tool'->'tools', 'texts'->'text'). "
    "If two readings of the source are plausible, leave it.\n"
    "   - Singular/plural flips on a single noun when the surrounding sentence is unchanged "
    "(e.g. 'parallel texts'->'parallel text') — these usually break a term of art.\n"
    "   - Do not switch people/peoples, language/languages, culture/cultures, or "
    "knowledge/knowledges; these may carry deliberate Indigenous scholarship meanings.\n"
    "   - Colloquial-to-formal word swaps (e.g. quick -> efficient) — do NOT propose these.\n"
    "   - Possessive/apostrophe corrections (e.g. universities -> university's) — do NOT "
    "propose these; context is too ambiguous.\n"
    "   - Word removals that change sentence structure (e.g. dropping 'have' from "
    "'have described') — do NOT propose these.\n"
    "   - Any rewording for clarity, tone, register, or conciseness.\n"
    "   - Merging or splitting paragraphs or sentences.\n"
    "\n"
    "CITATION HANDLING:\n"
    "   - DIRECT quotations (text inside \"quotation marks\" or inside a block quote): "
    "never edit, even if the quoted text contains spelling or grammar errors.\n"
    "   - INDIRECT citations (paraphrases followed by a parenthetical citation such as "
    "'(Author, 2024)'): only correct OBJECTIVE errors from the allowed categories "
    "above. Never make subjective style changes in citation-adjacent text.\n"
    "   - The parenthetical citation itself (the '(Author, 2024)' or numeric reference): "
    "never edit.\n"
    "   - Proper nouns and author names: never edit.\n"
    "\n"
    "Return an empty `edits` array if no qualifying corrections exist. An empty array "
    "is the correct answer for paragraphs that are already clean.\n"
    "\n"
    "Respond with JSON matching the provided schema. `reason` is a short (<= 200 chars) "
    "explanation that names the category (e.g. 'US->AU spelling', 'subject-verb "
    "agreement', 'Latin abbreviation punctuation')."
)


def _is_skippable_paragraph(paragraph) -> bool:
    if paragraph.is_empty:
        return True
    if paragraph.style in SKIP_STYLES:
        return True
    if len(paragraph.text) < MIN_PARAGRAPH_CHARS:
        return True
    return False


def _body_paragraphs(paragraphs):
    heading1_indices = [p.index for p in paragraphs if p.style == "Heading 1" and not p.is_empty]
    if not heading1_indices:
        return []
    body_start = heading1_indices[0]

    references_bounds = get_section_bounds(paragraphs, "References")
    body_end = references_bounds[0] if references_bounds is not None else len(paragraphs)

    selected = []
    for paragraph in paragraphs:
        if paragraph.index < body_start or paragraph.index >= body_end:
            continue
        if _is_skippable_paragraph(paragraph):
            continue
        selected.append(paragraph)
    return selected


def _validate_edit(edit: dict, paragraph_text: str) -> bool:
    find_text = edit.get("find")
    replace_text = edit.get("replace")

    if not isinstance(find_text, str) or not isinstance(replace_text, str):
        return False
    if find_text == "" or replace_text == "":
        return False
    if find_text == replace_text:
        return False
    if _is_au_to_us_replacement(find_text, replace_text):
        return False
    if (find_text.lower(), replace_text.lower()) in _BLOCKED_PAIRS:
        return False
    if len(find_text) > MAX_FIND_CHARS:
        return False
    if len(find_text.split()) > MAX_FIND_WORDS:
        return False
    if len(replace_text) > REPLACE_LENGTH_RATIO * max(len(find_text), 1):
        return False
    if find_text not in paragraph_text:
        return False

    # Reject when the only change is curly<->straight quotes/apostrophes.
    # The bot may upgrade ASCII to typographic via dedicated passes, but the
    # LLM editor must never flip the direction in either direction here.
    if _strip_quotes(find_text) == _strip_quotes(replace_text):
        return False

    # Reject when the only change is hyphenation. The prompt forbids
    # hyphenation decisions; this is a hard guard for when the LLM ignores it.
    # Case-insensitive so `Evidences-Based → evidencesbased` is also caught —
    # a case-sensitive compare let that variant through.
    if (
        ("-" in find_text or "-" in replace_text)
        and find_text.lower().replace("-", "") == replace_text.lower().replace("-", "")
    ):
        return False

    # Reject when every occurrence of `find` sits inside a direct quotation.
    # JUTLP policy: direct quotations retain the source's original text. If
    # the same phrase also appears unquoted, that unquoted occurrence may still
    # be edited; the DOCX application pass skips quoted repeats.
    from app.services.quotation_utils import is_in_quote
    find_start = paragraph_text.find(find_text)
    has_unquoted_occurrence = False
    while find_start != -1:
        find_end = find_start + len(find_text)
        if not is_in_quote(paragraph_text, find_start, find_end):
            has_unquoted_occurrence = True
            break
        find_start = paragraph_text.find(find_text, find_start + 1)
    if not has_unquoted_occurrence:
        return False

    # Reject when `find` overlaps a protected domain term. These are phrases
    # where prior LLM passes have produced wrong "fixes" — break a corpus
    # linguistics term of art, swap equality for equity, etc.
    for term in _PROTECTED_TERMS:
        if term in find_text:
            return False

    diff = _token_diff(find_text, replace_text)
    if diff is not None:
        only_f, only_r = diff

        # Tense flips: the only differing tokens are auxiliary/modals.
        if only_f and only_r:
            all_aux = (
                all(t.lower() in _AUXILIARY_TOKENS for t in only_f)
                and all(t.lower() in _AUXILIARY_TOKENS for t in only_r)
            )
            if all_aux:
                return False

        # Inserted/removed hedging or discourse tokens.
        for t in only_f + only_r:
            if t.lower() in _HEDGING_AND_DISCOURSE_TOKENS:
                return False

        # Pure plural flip on a single token (texts<->text, tool<->tools,
        # concerns<->concern). Only differ by trailing "s" on one token, no
        # other tokens changed. Misses some legitimate plural fixes, but the
        # cost of a wrong plural change is far higher than the cost of
        # skipping a real one — the editor will catch it on read-through.
        if len(only_f) == 1 and len(only_r) == 1:
            a, b = only_f[0].lower(), only_r[0].lower()
            if a + "s" == b or b + "s" == a:
                return False

    return True


def _dedupe_edits(edits: list[dict]) -> list[dict]:
    seen = set()
    unique = []
    for edit in edits:
        key = (edit["find"], edit["replace"])
        if key in seen:
            continue
        seen.add(key)
        unique.append(edit)
    return unique


def _propagate_repeated_edits(edits: list[dict], body_paragraphs) -> list[dict]:
    """Apply accepted exact edits to repeated matching body text.

    The LLM reviews each paragraph independently, so it can accept a correction
    in one paragraph and miss the same exact term in another. Once a correction
    has passed validation, repeating that exact find/replace within the same
    eligible body range makes the output more consistent without asking the LLM
    to make broader or fuzzier edits.
    """
    propagated = list(edits)
    seen = {
        (edit["paragraph_index"], edit["find"], edit["replace"])
        for edit in propagated
    }
    accepted_by_phrase: dict[tuple[str, str], str] = {}
    for edit in edits:
        key = (edit["find"], edit["replace"])
        accepted_by_phrase.setdefault(key, edit.get("reason", ""))

    for (find_text, replace_text), reason in accepted_by_phrase.items():
        for paragraph in body_paragraphs:
            if find_text not in paragraph.text:
                continue
            key = (paragraph.index, find_text, replace_text)
            if key in seen:
                continue
            candidate = {
                "find": find_text,
                "replace": replace_text,
                "reason": reason,
            }
            if not _validate_edit(candidate, paragraph.text):
                continue
            propagated.append({
                "paragraph_index": paragraph.index,
                "find": find_text,
                "replace": replace_text,
                "reason": reason,
            })
            seen.add(key)
    return propagated


def _llm_edits_for_paragraph(paragraph_text: str) -> list[dict]:
    user_prompt = (
        "Review this paragraph and return surgical corrections per the rules in the "
        "system message. Paragraph:\n\n" + paragraph_text
    )
    try:
        response = call_llm_json(
            system_prompt=BODY_EDIT_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            response_schema=BODY_EDIT_SCHEMA,
        )
    except LLMError as exc:
        log.warning("Body LLM edit pass failed: %s", exc)
        return []

    raw_edits = response.get("content", {}).get("edits", [])
    if not isinstance(raw_edits, list):
        return []

    accepted = []
    for edit in raw_edits:
        if not isinstance(edit, dict):
            continue
        if not _validate_edit(edit, paragraph_text):
            continue
        if (edit["find"].lower(), edit["replace"].lower()) in _BLOCKED_PAIRS:
            continue  # program↔programme — both valid, leave as-is
        replace = _fix_au_spellings(edit["replace"])
        if replace.lower() == edit["find"].lower():
            continue  # pure AU→US flip — discard
        reason = (edit.get("reason") or "").strip()[:200]
        if not _reason_identifies_change(reason, edit["find"], replace):
            continue
        accepted.append({
            "find": edit["find"],
            "replace": replace,
            "reason": reason,
        })
        if len(accepted) >= MAX_EDITS_PER_PARAGRAPH:
            break
    return _dedupe_edits(accepted)


def build_body_edit_plan(docx_path: str) -> dict:
    paragraphs = load_paragraphs(docx_path)
    body = _body_paragraphs(paragraphs)

    all_edits = []
    for paragraph in body:
        paragraph_edits = _llm_edits_for_paragraph(paragraph.text)
        for edit in paragraph_edits:
            all_edits.append({
                "paragraph_index": paragraph.index,
                "find": edit["find"],
                "replace": edit["replace"],
                "reason": edit["reason"],
            })

    all_edits = _propagate_repeated_edits(all_edits, body)

    if not all_edits:
        return {
            "action": "none",
            "reason": "No qualifying body copy-edits identified",
            "edits": [],
        }

    return {
        "action": "apply_body_edits",
        "reason": f"{len(all_edits)} surgical body edit(s) suggested by LLM",
        "edits": all_edits,
    }
