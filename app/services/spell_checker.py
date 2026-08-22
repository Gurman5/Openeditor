"""General spell-checking for academic manuscripts.

Two-tier behaviour:

* **Auto-fix path** — high-confidence typos like ``studentss → students``
  are emitted as Word tracked changes (``<w:del>old</w:del><w:ins>new</w:ins>``)
  so the editor accepts or rejects each one in Word the same way they
  handle the AU/US spelling fixes from ``language_corrections``.
* **Comment path** — anything pyspellchecker thinks is wrong but where
  the candidate isn't unambiguous gets a single ``Possible typo`` comment
  for editor review, not an auto-rewrite.

AU/US spelling variants are handled separately by
``language_corrections.py`` — this module only flags genuine misspellings
not covered by that dictionary.
"""

from __future__ import annotations

import os
import re
import zipfile
from collections import Counter

from lxml import etree
from spellchecker import SpellChecker

from app.services.acronym_corrections import (
    _make_comment_element,
    _patch_content_types,
    _patch_rels,
    _split_run_for_action,
    _split_run_for_track_change_only,
)
from app.services.document_analysis_services import load_paragraphs
from app.services.grammar_corrections import _is_au_to_us_replacement
from app.services.language_corrections import (
    AU_CORRECTIONS,
    WQ,
    W,
    _merge_adjacent_runs,
)
from app.services.quotation_utils import find_quote_spans

_SKIP_STYLES = {
    "Heading 1", "Heading 2", "Heading 3", "Heading 4",
    "APA 7 Reference List Entry",
    "APA7ReferenceListEntry",
    "Article Title", "Authors", "Author Affiliations",
    "Heading Front Page", "Front Page Text",
    "Caption", "Table Number", "Table Title", "Figure Number", "Figure Title",
    "Figure/Table Number", "Figure/Table Title",
    "FigureTableNumber", "FigureTableTitle",
}

# Patterns to skip at the token level: all-caps acronyms, anything with a
# digit, single chars, or any token containing apostrophes / hyphens
# (names like O'Hagan, multi-word compounds — too risky to auto-fix).
_SKIP_RE = re.compile(r"^[A-Z]{2,}$|[0-9]|^.$|['’\-]")

# Build spell checker and teach it both AU and US forms so neither flags.
_spell = SpellChecker()
_spell.word_frequency.load_words(AU_CORRECTIONS.keys())
_spell.word_frequency.load_words(AU_CORRECTIONS.values())

# Domain terms that recur in this and similar JUTLP submissions but aren't
# in the en_US dictionary. Better to extend this list than to let the
# checker auto-fix them into nonsense.
_ACADEMIC_WHITELIST = {
    "al", "et", "eg", "ie", "vs", "cf", "ibid", "op", "cit",
    "doi", "url", "isbn", "issn",
    "quantitative", "qualitative", "methodology", "pedagogical",
    "epistemological", "ontological", "sociocultural", "metacognitive",
    "constructivist", "behaviourism", "behaviourist",
    "pre", "post", "non", "co", "multi", "inter", "intra",
    # Translation-studies and academic terms that recur in manuscripts
    # but aren't in pyspellchecker's en_US frequency list.
    "translatology", "crowdsourcing", "crowdsourced",
    "subcompetence", "subcompetences",
    "untranslatability", "lexicogrammatical",
    "commodification", "commoditisation", "commoditised",
    "commoditization", "commoditized",  # US variants — AU pass converts these
    "minoritized", "minoritised",  # critical-pedagogy term
    "roadmap", "inclusivity", "demotivation",
    "knowledges", "yarning", "yarnings", "mob", "mobs",
    "songline", "songlines", "dadirri",
    "koori", "murri", "noongar", "nyoongar", "nyungar", "yolngu", "yol\u014bu",
    # Latin / borrowed phrases — single-word fragments that pyspellchecker
    # doesn't know but are part of well-known multi-word terms.
    "socio", "franca", "versa", "lingua",
    # Common compound nouns that pyspellchecker rejects.
    "stakeholders", "stakeholder", "workflow", "workflows",
}

# US `-ize`/`-ization` spellings the AU pass should handle. If a word
# matches this pattern AND isn't in the dictionary, we skip rather than
# risk a wrong auto-fix to an unrelated word.
_US_IZE_SUFFIX_RE = re.compile(r"(iz(?:e|ed|es|ing|ation|ations)?)$", re.IGNORECASE)

# Confidence thresholds for the auto-fix gate.
_MIN_WORD_LEN = 4                  # shorter words are too risky to auto-fix
_AUTOFIX_MAX_DISTANCE = 1          # auto-fix only single-edit typos (e.g. `studentss` → `students`)
_FLAG_MAX_DISTANCE = 2             # flag (comment) up to two-edit suggestions
_MIN_FREQ_RATIO = 5.0              # candidate must be ≥5× more common than the typo
_MIN_RECURRENCE_FOR_SKIP = 3       # word seen ≥3 times in body is assumed correct


def _classify_word(
    word: str,
    word_counts: Counter,
) -> tuple[str, str | None]:
    """Return ``(verdict, candidate)`` for a single suspect word.

    Verdict is one of:
    * ``"skip"``: not a typo, or too risky to do anything with
      (returns ``candidate=None``).
    * ``"autofix"``: high-confidence single candidate — emit tracked
      change.
    * ``"flag"``: low-confidence — emit a comment with the best
      suggestion.
    """
    if not word or len(word) < _MIN_WORD_LEN:
        return ("skip", None)
    if _SKIP_RE.search(word):
        return ("skip", None)
    lower = word.lower()
    if lower in _ACADEMIC_WHITELIST:
        return ("skip", None)
    if lower in AU_CORRECTIONS or lower in AU_CORRECTIONS.values():
        # AU/US handled elsewhere.
        return ("skip", None)
    if word_counts.get(lower, 0) >= _MIN_RECURRENCE_FOR_SKIP:
        # Recurrent token — probably intentional (domain term, proper noun).
        return ("skip", None)
    if word[0].isupper():
        # Proper nouns: we can't tell ``Kiraly`` from a misspelt common word.
        # Skip auto-fix; also skip flag because false positives here are
        # mostly names and create noise without value.
        return ("skip", None)

    if _spell.known([lower]):
        # Already a known word.
        return ("skip", None)

    # US-ize spelling variants (e.g. ``commoditized``, ``minoritized``) often
    # aren't in pyspellchecker's frequency list, so the checker returns a
    # nearby unrelated word (``commodities``). Let the AU spelling pass
    # handle these — never auto-fix or flag here.
    if _US_IZE_SUFFIX_RE.search(lower):
        return ("skip", None)

    candidates = _spell.candidates(lower) or set()
    correction = _spell.correction(lower)
    if not correction or correction == lower:
        return ("skip", None)
    if _is_au_to_us_replacement(lower, correction):
        return ("skip", None)

    alpha_candidates = [c for c in candidates if c.isalpha()]
    if correction not in alpha_candidates or len(alpha_candidates) != 1:
        # Multiple plausible candidates or the suggested correction is
        # punctuated. Too ambiguous for either auto-fix or comment —
        # surfacing both would just create noise.
        return ("skip", None)

    distance = _levenshtein(lower, correction)
    freq_ratio = _freq_ratio(correction, lower)

    # Auto-fix gate: single edit (catches doubled letters like ``studentss``
    # → ``students`` and transposition typos) and the candidate is a far
    # more common English word. Distance-1 substantially reduces the risk
    # of swapping ``commoditized`` for ``commodities`` (distance 3).
    if distance <= _AUTOFIX_MAX_DISTANCE and freq_ratio >= _MIN_FREQ_RATIO:
        return ("autofix", correction)

    # Comment gate: up to two edits away, and the candidate is still much
    # more common than the source. Anything further is more likely a
    # different word than a typo — skip entirely.
    if distance <= _FLAG_MAX_DISTANCE and freq_ratio >= _MIN_FREQ_RATIO:
        return ("flag", correction)

    return ("skip", None)


def _levenshtein(a: str, b: str) -> int:
    """Cheap Levenshtein implementation — we only ever compare short
    words so the O(len(a)*len(b)) cost is trivial."""
    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, start=1):
        curr = [i]
        for j, cb in enumerate(b, start=1):
            cost = 0 if ca == cb else 1
            curr.append(min(curr[-1] + 1, prev[j] + 1, prev[j - 1] + cost))
        prev = curr
    return prev[-1]


def _freq_ratio(candidate: str, word: str) -> float:
    """Ratio of dictionary frequency between candidate and source word.

    Both pyspellchecker's ``word_usage_frequency`` and ``word_probability``
    return floats in [0, 1]. A high ratio means the candidate is a far
    more common English word than the typo, which is a good sign the
    candidate is the right correction.
    """
    try:
        candidate_freq = _spell.word_usage_frequency(candidate)
        word_freq = _spell.word_usage_frequency(word)
    except Exception:
        return 0.0
    if word_freq <= 0:
        # Suspect word doesn't appear in the dictionary at all (good — it's
        # genuinely unknown). Treat as a high ratio so the gate passes on
        # frequency.
        return float("inf")
    return candidate_freq / word_freq


def _iter_text_runs(para_el: etree._Element):
    """Yield (run, text) for body runs not inside tracked-change wrappers."""
    for r in para_el.iter(f"{WQ}r"):
        parent = r.getparent()
        if parent is not None and parent.tag in (f"{WQ}del", f"{WQ}ins"):
            continue
        t_el = r.find(f"{WQ}t")
        if t_el is None:
            continue
        yield r, t_el.text or ""


def _get_para_style(para_el: etree._Element) -> str:
    pPr = para_el.find(f"{WQ}pPr")
    if pPr is None:
        return ""
    pStyle = pPr.find(f"{WQ}pStyle")
    if pStyle is None:
        return ""
    return pStyle.get(f"{WQ}val", "") or ""


def get_spell_corrections(docx_path: str) -> list[dict]:
    """Return list of {original, replacement, reason, verdict} dicts.

    Kept for backwards compatibility — earlier code consumed the
    list directly. ``verdict`` is one of ``"autofix"`` / ``"flag"`` so
    callers can decide rendering.
    """
    para_records = load_paragraphs(docx_path)
    word_counts = _build_word_counts(para_records)

    seen: set[str] = set()
    corrections: list[dict] = []

    in_references = False
    for para in para_records:
        if para.style in ("Heading 1", "Heading1") and para.text.strip().lower() in ("references", "reference list"):
            in_references = True
        if in_references:
            continue
        if para.style in _SKIP_STYLES or para.is_empty or len(para.text) < 10:
            continue

        # Direct-quotation protection: a typo inside `"..."` retains the
        # source's original spelling. We skip a word only when EVERY
        # occurrence of it in this paragraph sits inside a quote span;
        # if the same word also appears outside a quote, the editor
        # will still see the flag anchored at the outside occurrence.
        quote_spans = find_quote_spans(para.text)

        for word in _spell.split_words(para.text):
            lower = word.lower()
            if lower in seen:
                continue
            if quote_spans and _word_only_in_quote(para.text, word, quote_spans):
                continue
            verdict, candidate = _classify_word(word, word_counts)
            if verdict == "skip":
                continue
            seen.add(lower)
            corrections.append({
                "original": word,
                "replacement": candidate,
                "reason": "Possible spelling error",
                "verdict": verdict,
            })
    return corrections


def _word_only_in_quote(
    para_text: str,
    word: str,
    quote_spans: list[tuple[int, int]],
) -> bool:
    """Return True iff every word-bounded occurrence of ``word`` in
    ``para_text`` falls inside one of the given quote spans.

    Used by the spell-checker to suppress flags that ONLY apply to
    quoted text. If the word also appears outside any quote, return
    False so the correction stays — it will anchor at the unquoted
    occurrence.
    """
    pattern = re.compile(r"\b" + re.escape(word) + r"\b")
    occurrences = list(pattern.finditer(para_text))
    if not occurrences:
        return False
    for m in occurrences:
        if not any(m.start() < e and s < m.end() for s, e in quote_spans):
            return False
    return True


def _build_word_counts(para_records) -> Counter:
    counts: Counter = Counter()
    for para in para_records:
        if para.is_empty:
            continue
        for word in _spell.split_words(para.text):
            counts[word.lower()] += 1
    return counts


# ---------------------------------------------------------------------------
# Apply-pass entry point — mirrors apply_acronym_corrections / siblings.
# ---------------------------------------------------------------------------


def _find_word_anchor(para_el: etree._Element, word: str) -> tuple[etree._Element, int, int] | None:
    """Locate the first occurrence of ``word`` (case-sensitive, word-bounded)
    in the paragraph's runs and return ``(run_el, start_in_run, end_in_run)``.

    Word boundaries are honoured so a search for ``the`` doesn't anchor on
    the inside of ``their``.
    """
    run_offset = 0
    full_text_parts: list[tuple[etree._Element, str, int]] = []
    for r, t in _iter_text_runs(para_el):
        full_text_parts.append((r, t, run_offset))
        run_offset += len(t)

    full_text = "".join(t for _, t, _ in full_text_parts)
    pattern = re.compile(r"\b" + re.escape(word) + r"\b")
    m = pattern.search(full_text)
    if m is None:
        return None
    start, end = m.start(), m.end()

    for run_el, run_text, offset in full_text_parts:
        run_end = offset + len(run_text)
        if offset <= start and end <= run_end:
            return (run_el, start - offset, end - offset)
    # Word spans multiple runs — give up rather than splice across.
    return None


def apply_spell_corrections(
    input_path: str,
    output_path: str,
    next_change_id: int = 1,
) -> tuple[int, list[dict]]:
    """Apply spell-checker autofixes and flags to ``input_path``.

    Returns ``(next_change_id, actions)`` with the same shape as sibling
    correction passes. Each action records the verdict so the caller can
    surface a summary if needed.
    """
    corrections = get_spell_corrections(input_path)
    if not corrections:
        if input_path != output_path:
            with zipfile.ZipFile(input_path, "r") as zin, zipfile.ZipFile(
                output_path, "w", zipfile.ZIP_DEFLATED
            ) as zout:
                for item in zin.infolist():
                    zout.writestr(item, zin.read(item.filename))
        return next_change_id, []

    with zipfile.ZipFile(input_path, "r") as z:
        names = z.namelist()
        doc_xml = z.read("word/document.xml")
        rels_xml = z.read("word/_rels/document.xml.rels")
        ct_xml = z.read("[Content_Types].xml")
        has_comments = "word/comments.xml" in names
        comments_xml = z.read("word/comments.xml") if has_comments else None

    doc_root = etree.fromstring(doc_xml)
    if comments_xml:
        comments_root = etree.fromstring(comments_xml)
        existing = [int(el.get(f"{WQ}id", 0)) for el in comments_root.findall(f"{WQ}comment")]
        next_comment_id = max(existing, default=0) + 1
    else:
        comments_root = etree.Element(f"{WQ}comments", nsmap={"w": W})
        next_comment_id = 1

    actions: list[dict] = []

    # For each correction, find its first body anchor in the document and
    # emit either an auto-fix tracked change or a low-confidence comment.
    for c in corrections:
        word = c["original"]
        candidate = c["replacement"]
        verdict = c["verdict"]

        anchor = None
        for para_el in doc_root.iter(f"{WQ}p"):
            style = _get_para_style(para_el)
            if style in _SKIP_STYLES:
                continue
            # Some manuscripts split a single word across multiple runs
            # (e.g. spell-checker corrections from the author's earlier
            # passes). Merge first so the word lives in one run and the
            # anchor mapping succeeds.
            _merge_adjacent_runs(para_el)
            hit = _find_word_anchor(para_el, word)
            if hit is not None:
                anchor = (para_el, hit)
                break

        if anchor is None:
            continue
        para_el, (run_el, start, end) = anchor

        if verdict == "autofix" and candidate:
            # Preserve the original token's leading-cap shape (Studentss →
            # Students) — common for sentence-start typos.
            replacement = candidate
            if word[:1].isupper() and candidate[:1].islower():
                replacement = candidate[:1].upper() + candidate[1:]
            next_change_id = _split_run_for_track_change_only(
                run_el, start, end, replacement, next_change_id
            )
            actions.append({
                "rule": "SPELL_AUTOFIX",
                "original": word,
                "replacement": replacement,
            })
        else:
            message = (
                f"Possible typo: '{word}'."
                + (f" Did you mean '{candidate}'? Please verify." if candidate else " Please verify.")
            )
            comments_root.append(_make_comment_element(next_comment_id, message))
            _split_run_for_action(
                run_el, start, end,
                expansion=None,
                comment_id=next_comment_id,
                change_id=0,
            )
            actions.append({
                "rule": "SPELL_FLAG",
                "original": word,
                "suggestion": candidate,
                "comment_id": next_comment_id,
            })
            next_comment_id += 1

    new_doc_xml = etree.tostring(doc_root, xml_declaration=True, encoding="UTF-8", standalone=True)
    new_comments_xml = etree.tostring(comments_root, xml_declaration=True, encoding="UTF-8", standalone=True)
    new_rels_xml = _patch_rels(rels_xml)
    new_ct_xml = _patch_content_types(ct_xml)

    tmp = output_path + ".spell.tmp"
    try:
        with zipfile.ZipFile(input_path, "r") as zin, zipfile.ZipFile(
            tmp, "w", zipfile.ZIP_DEFLATED
        ) as zout:
            for item in zin.infolist():
                if item.filename == "word/document.xml":
                    zout.writestr(item, new_doc_xml)
                elif item.filename == "word/_rels/document.xml.rels":
                    zout.writestr(item, new_rels_xml)
                elif item.filename == "[Content_Types].xml":
                    zout.writestr(item, new_ct_xml)
                elif item.filename == "word/comments.xml":
                    zout.writestr(item, new_comments_xml)
                else:
                    zout.writestr(item, zin.read(item.filename))
            if not has_comments:
                zout.writestr("word/comments.xml", new_comments_xml)
        os.replace(tmp, output_path)
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise

    return next_change_id, actions
