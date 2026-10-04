"""Reporting ownership: which layer reports each validation finding.

A finding must surface exactly once across the two reporting layers:

1. the reviewed Word document — margin comments via ``generate_commented_docx``
   and tracked changes / silent style edits via Sam's ``build_edited_document``;
2. the Results API payload — ``issues[]`` built in ``app/main.py results()``.

Rules Sam's builder FIXES are excluded from both comment layers, or the author
sees the issue twice (once as a tracked change, once as a comment / issue).
Everything else is comment-only and must never be dropped, or the issue
silently disappears — the old ``{"FP"}`` prefix filter dropped FP008/FP009
this way, which was a correctness bug, not deduplication.

Precedence rule: the Sam-fixed exclusion wins over the LLM false-positive
downgrade (``fp_overrides`` in ``results()``). A fixed issue needs no
false-positive note; the author sees the tracked change, not a verdict.

``SAM_FIXED_RULE_IDS`` membership is an empirical claim, not an axiom: each id
must name a Sam pass that demonstrably fixes it (verified in Phase 2 of the
D-01 remediation). Anything Sam does not fix comes off this set and becomes
comment-only.
"""

# Validator rule ids Sam's build_edited_document fixes as a tracked change or
# silent style edit. Excluded from the document comments (filtered_report) and
# from the payload issues[] (results()). Still counted in changes_made.
SAM_FIXED_RULE_IDS = frozenset({
    "FP001", "FP002", "FP003", "FP004", "FP005", "FP006", "FP007", "FP011",
    "STY003", "STY004", "SPE002", "TAB001", "TAB002",
})


def is_sam_fixed(rule_id: str) -> bool:
    """True when Sam's builder fixes this validator rule, so no other layer
    should report it."""
    return rule_id in SAM_FIXED_RULE_IDS


# Per-family verdict: where each rule family is reported.
# "tracked-change" = fixed by Sam; excluded from issues[] and doc comments,
#                     counted in changes_made.
# "comment"        = reported in issues[] and as a document margin comment.
# "ref-section"    = reported in ref_verifications[], never in issues[].
# "neither"        = deliberately unreported in issues[] (duplicates another
#                    rule's finding).
# Each entry is (verdict, rationale). Rule ids listed after a family verdict
# are the per-rule exceptions to it.
FAMILY_VERDICTS = {
    # Body structure. Sam does not insert or reorder body sections.
    "SEC": ("comment",
            "Section presence/order is check-only; no Sam pass restructures the body."),
    "MET": ("comment",
            "Method subsections are check-only; missing-subsection cascade is "
            "guarded inside the validator itself."),
    "DIS": ("comment",
            "Discussion subsections are check-only, as MET."),
    # Front page. Presence/heading blocks Sam inserts as stubs (tracked
    # changes); length/count rules stay comments.
    "FP": ("comment",
           "Default is comment-only; the Sam-fixed presence rules below are "
           "the exception, not the family verdict.",
           ["FP001", "FP002", "FP003", "FP004", "FP005", "FP006", "FP007", "FP011"]),
    # Page/section breaks. SPE002 (page break before Introduction) is inserted
    # by Sam; the rest are check-only.
    "SPE": ("comment",
            "Default is comment-only; SPE002 is inserted by Sam.",
            ["SPE002"]),
    # Figures / general content / affiliations / prose-pattern rules.
    # Check-only; no Sam pass rewrites these.
    "FIG": ("comment", "Figure structure is check-only."),
    "CON": ("comment", "Conclusion length is check-only."),
    "AFF": ("comment", "Equal-contribution flag is check-only."),
    "ANDOR": ("comment", "Prose-pattern flag is check-only."),
    "ETC": ("comment", "Prose-pattern flag is check-only."),
    "DOTPT": ("comment", "Prose-pattern flag is check-only."),
    # Style. STY003 (body styles) and STY004 (reference styles) are normalised
    # by Sam's style passes; STY002 (forbidden styles) stays a comment.
    "STY": ("comment",
            "Default is comment-only; STY003/STY004 are normalised by Sam.",
            ["STY003", "STY004"]),
    # Tables. TAB001 (title follows number) and TAB002 (sequential numbering)
    # are repaired by Sam's tracked table formatting.
    "TAB": ("comment",
            "Default is comment-only; TAB001/TAB002 are repaired by Sam.",
            ["TAB001", "TAB002"]),
    # Reference verification. Never in issues[]; each row feeds the
    # references section (ref_verifications) with its own status + DOI link.
    "CREF": ("ref-section", "Per-reference verification row, not an issue."),
    "HREF": ("ref-section", "Per-reference hyperlink row, not an issue."),
    "CONS": ("ref-section", "Per-reference consistency row, not an issue."),
    # REF001 duplicates SEC008 (References section presence) and is skipped in
    # both layers; REF003 feeds ref_verifications; other REF* behave as comments.
    "REF": ("comment",
            "Default is comment-only; REF001 is suppressed as a duplicate of "
            "SEC008 and REF003 routes to ref_verifications.",
            ["REF001", "REF003"]),
    "REFE": ("comment", "Reference-format flags are comment-only."),
}
