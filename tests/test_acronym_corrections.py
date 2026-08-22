"""Tests for acronym detection + consolidated comment + tracked-change rewrites."""

from __future__ import annotations

import zipfile
from pathlib import Path

from lxml import etree

from app.services.acronym_corrections import (
    _format_author_query_text,
    _matches_definition,
    apply_acronym_corrections,
)

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
WQ = f"{{{W}}}"


def test_acronym_author_query_comment_text_is_numbered():
    assert _format_author_query_text(5, "Please check use of acronyms.") == (
        "Author Query 5. Please check use of acronyms."
    )


_MIN_CT = (
    b'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    b'<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
    b'<Default Extension="xml" ContentType="application/xml"/>'
    b'<Default Extension="rels" '
    b'ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
    b'<Override PartName="/word/document.xml" '
    b'ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
    b'</Types>'
)
_MIN_RELS_PKG = (
    b'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    b'<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
    b'<Relationship Id="rId1" '
    b'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" '
    b'Target="word/document.xml"/>'
    b'</Relationships>'
)
_MIN_RELS_DOC = (
    b'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    b'<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"></Relationships>'
)


def _build_docx(path: Path, paragraphs: list[str]) -> None:
    """Build a minimal docx with one paragraph per supplied text."""
    body = "".join(
        f'<w:p><w:r><w:t xml:space="preserve">{p}</w:t></w:r></w:p>'
        for p in paragraphs
    )
    doc = (
        f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f'<w:document xmlns:w="{W}"><w:body>{body}</w:body></w:document>'
    ).encode("utf-8")
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", _MIN_CT)
        z.writestr("_rels/.rels", _MIN_RELS_PKG)
        z.writestr("word/_rels/document.xml.rels", _MIN_RELS_DOC)
        z.writestr("word/document.xml", doc)


def _build_zoned_docx(path: Path, entries: list[tuple[str | None, str]]) -> None:
    """Build a docx where each entry is (style or None, text).

    A ``None`` style produces a body paragraph; a string is the paragraph
    style name (e.g. ``"Heading 1"``).
    """
    body_parts = []
    for style, text in entries:
        if style is None:
            ppr = ""
        else:
            ppr = f'<w:pPr><w:pStyle w:val="{style}"/></w:pPr>'
        body_parts.append(
            f'<w:p>{ppr}<w:r><w:t xml:space="preserve">{text}</w:t></w:r></w:p>'
        )
    doc = (
        f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f'<w:document xmlns:w="{W}"><w:body>{"".join(body_parts)}</w:body></w:document>'
    ).encode("utf-8")
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", _MIN_CT)
        z.writestr("_rels/.rels", _MIN_RELS_PKG)
        z.writestr("word/_rels/document.xml.rels", _MIN_RELS_DOC)
        z.writestr("word/document.xml", doc)


def _build_docx_with_inserted_run(path: Path, entries: list[tuple[str | None, str, bool]]) -> None:
    """Build a docx where each entry is ``(style, text, inside_ins)``.

    When ``inside_ins`` is True, the paragraph's run is wrapped in a
    ``<w:ins>`` element (mimicking the state after an earlier pipeline
    pass like Sam's title-case fix has tracked an insertion). When False,
    the run is a plain ``<w:r>``.

    Used to exercise the acronym scanner's behaviour against tracked
    insertions from upstream passes — the scanner should READ inserted
    text so acronyms in the document's final state get flagged.
    """
    body_parts = []
    for style, text, inside_ins in entries:
        ppr = "" if style is None else f'<w:pPr><w:pStyle w:val="{style}"/></w:pPr>'
        run = f'<w:r><w:t xml:space="preserve">{text}</w:t></w:r>'
        if inside_ins:
            run = (
                f'<w:ins w:id="100" w:author="Sam" w:date="2026-05-18T00:00:00Z">'
                f'{run}</w:ins>'
            )
        body_parts.append(f'<w:p>{ppr}{run}</w:p>')
    doc = (
        f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f'<w:document xmlns:w="{W}"><w:body>{"".join(body_parts)}</w:body></w:document>'
    ).encode("utf-8")
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", _MIN_CT)
        z.writestr("_rels/.rels", _MIN_RELS_PKG)
        z.writestr("word/_rels/document.xml.rels", _MIN_RELS_DOC)
        z.writestr("word/document.xml", doc)


def _read_doc_root(path: Path) -> etree._Element:
    with zipfile.ZipFile(path, "r") as z:
        return etree.fromstring(z.read("word/document.xml"))


def _read_comments_root(path: Path) -> etree._Element | None:
    with zipfile.ZipFile(path, "r") as z:
        names = z.namelist()
        if "word/comments.xml" not in names:
            return None
        return etree.fromstring(z.read("word/comments.xml"))


def _comment_visible_text(comments_root: etree._Element) -> str:
    """Concatenate every ``<w:t>`` text under the comments root."""
    return "".join(t.text or "" for t in comments_root.iter(f"{WQ}t"))


# ── _matches_definition (logic unchanged) ─────────────────────────────────


def test_matches_definition_simple_initialism():
    assert _matches_definition(
        ["Subject", "Matter", "Expert"], "SME"
    ) == "Subject Matter Expert"


def test_matches_definition_with_skipped_small_words():
    # SoTL = Scholarship of Teaching and Learning: 'and' is skipped, 'of' fits 'o'.
    result = _matches_definition(
        ["Scholarship", "of", "Teaching", "and", "Learning"], "SoTL"
    )
    assert result == "Scholarship of Teaching and Learning"


def test_matches_definition_rejects_non_initialism():
    # GenAI is not a clean initialism of "Generative Artificial Intelligence".
    assert _matches_definition(
        ["Generative", "Artificial", "Intelligence"], "GenAI"
    ) is None


def test_matches_definition_short_acronym_rejected():
    assert _matches_definition(["Word"], "W") is None


# ── End-to-end behaviour ──────────────────────────────────────────────────


_EMPTY_ALLOW: dict[str, list[str]] = {}
_LMS_ALLOW = {"LMS": ["learning management system"]}


def test_only_one_comment_added_regardless_of_issue_count(tmp_path):
    """Five problematic acronyms still produce exactly one Word comment."""
    inp = tmp_path / "in.docx"
    out = tmp_path / "out.docx"
    _build_zoned_docx(
        inp,
        [
            ("Heading 1", "Introduction"),
            (None, "We tested ABCDE methodology with FGHIJ inputs."),
            (None, "Then KLMNO and PQRST were combined with UVWXY."),
        ],
    )

    _, actions = apply_acronym_corrections(
        str(inp), str(out), next_change_id=1, accepted_acronyms=_EMPTY_ALLOW,
    )

    assert len(actions) == 5
    comments = _read_comments_root(out)
    assert comments is not None
    # Only one consolidated comment in comments.xml.
    assert len(comments.findall(f"{WQ}comment")) == 1
    # Only one anchor in the document body.
    root = _read_doc_root(out)
    starts = root.findall(f".//{WQ}commentRangeStart")
    assert len(starts) == 1


def test_consolidated_comment_lists_all_issues_as_bullets(tmp_path):
    inp = tmp_path / "in.docx"
    out = tmp_path / "out.docx"
    _build_zoned_docx(
        inp,
        [
            ("Heading 1", "Introduction"),
            (None, "We tested ABCDE methodology with FGHIJ inputs."),
        ],
    )

    _, _ = apply_acronym_corrections(
        str(inp), str(out), next_change_id=1, accepted_acronyms=_EMPTY_ALLOW,
    )

    comments = _read_comments_root(out)
    assert comments is not None
    txt = _comment_visible_text(comments)
    assert "Author Query" in txt
    assert "ABCDE" in txt
    assert "FGHIJ" in txt


def test_allow_listed_acronym_in_body_flagged_when_not_introduced(tmp_path):
    """Allow-listed acronyms still need a first-use introduction in the body.

    A tracked change rewrites the first bare use to ``full term (ACRO)``.
    """
    inp = tmp_path / "in.docx"
    out = tmp_path / "out.docx"
    _build_zoned_docx(
        inp,
        [
            ("Heading 1", "Introduction"),
            (None, "Our LMS recorded all activity that semester."),
        ],
    )

    _, actions = apply_acronym_corrections(
        str(inp), str(out), next_change_id=1, accepted_acronyms=_LMS_ALLOW,
    )

    assert len(actions) == 1
    assert actions[0]["acronym"] == "LMS"
    assert actions[0]["zone"] == "body"
    assert actions[0]["needs_track_change"] is True

    # The tracked change replaces "LMS" with "learning management system (LMS)".
    root = _read_doc_root(out)
    ins = root.findall(f".//{WQ}ins")
    dels = root.findall(f".//{WQ}del")
    assert len(ins) == 1 and len(dels) == 1
    ins_text = "".join(t.text or "" for t in ins[0].iter(f"{WQ}t"))
    del_text = "".join(t.text or "" for t in dels[0].iter(f"{WQ}delText"))
    assert ins_text == "learning management system (LMS)"
    assert del_text == "LMS"


def test_allow_listed_acronym_in_body_silent_when_introduced(tmp_path):
    """When the author DID introduce the acronym in the body, no issue fires."""
    inp = tmp_path / "in.docx"
    out = tmp_path / "out.docx"
    _build_zoned_docx(
        inp,
        [
            ("Heading 1", "Introduction"),
            (None, "We used a learning management system (LMS) for delivery."),
            (None, "The LMS recorded engagement metrics across the cohort."),
        ],
    )

    _, actions = apply_acronym_corrections(
        str(inp), str(out), next_change_id=1, accepted_acronyms=_LMS_ALLOW,
    )

    assert actions == []
    assert _read_comments_root(out) is None


def test_body_needs_its_own_introduction(tmp_path):
    """An introduction in the abstract does NOT satisfy the body's first-use rule."""
    inp = tmp_path / "in.docx"
    out = tmp_path / "out.docx"
    _build_zoned_docx(
        inp,
        [
            (None, "Abstract: this study uses a learning management system (LMS)."),
            ("Heading 1", "Introduction"),
            (None, "The LMS recorded all activity that semester."),
        ],
    )

    _, actions = apply_acronym_corrections(
        str(inp), str(out), next_change_id=1, accepted_acronyms=_EMPTY_ALLOW,
    )

    # Exactly one issue — the body's first use of LMS needs its own intro.
    body_issues = [a for a in actions if a["zone"] == "body"]
    assert len(body_issues) == 1
    assert body_issues[0]["acronym"] == "LMS"
    assert body_issues[0]["expansion"] == "learning management system"


def test_abstract_allow_listed_silent(tmp_path):
    """Allow-listed acronyms in the abstract are silent — no flagging."""
    inp = tmp_path / "in.docx"
    out = tmp_path / "out.docx"
    _build_zoned_docx(
        inp,
        [
            # Front zone (before Introduction).
            (None, "Abstract: this study examines LMS adoption."),
            (None, "Keywords: pedagogy, LMS, online learning."),
            # Marks the abstract/body boundary so the front zone is real.
            ("Heading 1", "Introduction"),
            (None, "Body text with no acronyms."),
        ],
    )

    _, actions = apply_acronym_corrections(
        str(inp), str(out), next_change_id=1, accepted_acronyms=_LMS_ALLOW,
    )

    assert actions == []
    assert _read_comments_root(out) is None


def test_abstract_unknown_acronym_flagged(tmp_path):
    """Truly unknown acronyms in the abstract (no allow-list, no inline def
    anywhere) are flagged."""
    inp = tmp_path / "in.docx"
    out = tmp_path / "out.docx"
    _build_zoned_docx(
        inp,
        [
            (None, "Abstract: this study examines XYZQQ adoption."),
            ("Heading 1", "Introduction"),
            (None, "Body text with no acronyms."),
        ],
    )

    _, actions = apply_acronym_corrections(
        str(inp), str(out), next_change_id=1, accepted_acronyms=_EMPTY_ALLOW,
    )

    assert len(actions) == 1
    assert actions[0]["acronym"] == "XYZQQ"
    assert actions[0]["zone"] == "front"
    # No track change in abstract (only body issues with known expansion get one).
    assert actions[0]["needs_track_change"] is False


def test_acronyms_inside_inserted_runs_are_detected(tmp_path):
    """The scanner must read text inside ``<w:ins>`` runs — that's what
    upstream pipeline passes (Sam's title-case fix, LLM body edits, added
    Practitioner-Notes paragraphs) produce for content that should appear
    in the final document. Skipping ins runs silently hides every acronym
    those passes touched."""
    inp = tmp_path / "in.docx"
    out = tmp_path / "out.docx"
    _build_docx_with_inserted_run(
        inp,
        [
            (None, "Abstract intro paragraph.", False),
            ("Heading 1", "Introduction", False),
            # Body paragraph whose content sits inside <w:ins> — mimics what
            # happens when Sam's body-LLM-edit wraps a corrected run.
            (None, "We measured LMS adoption in TEQSA-aligned schools.", True),
        ],
    )

    _, actions = apply_acronym_corrections(
        str(inp), str(out), next_change_id=1,
        accepted_acronyms={
            "LMS": ["learning management system"],
            "TEQSA": ["Tertiary Education Quality and Standards Authority"],
        },
    )

    flagged = {a["acronym"] for a in actions}
    assert "LMS" in flagged, (
        "LMS sits inside a <w:ins> run from an upstream pass; the acronym "
        f"scanner must still flag it. Got actions={actions}"
    )
    assert "TEQSA" in flagged, (
        "TEQSA sits inside the same <w:ins> run; both acronyms in the "
        f"insertion should be flagged. Got actions={actions}"
    )


def test_deleted_runs_are_not_flagged(tmp_path):
    """Conversely, text inside ``<w:del>`` represents tracked deletions —
    content the document is dropping — so the scanner must NOT flag
    acronyms there. Otherwise the consolidated comment would list ghost
    issues for text that won't be present after accept-all."""
    inp = tmp_path / "in.docx"
    out = tmp_path / "out.docx"
    # Build a docx with one paragraph that has BOTH a <w:del> run (old
    # content with an acronym) and a plain run (new content without one).
    body = (
        '<w:p>'
        '<w:del w:id="50" w:author="Sam" w:date="2026-05-18T00:00:00Z">'
        '<w:r><w:delText xml:space="preserve">Old text mentioning LMS.</w:delText></w:r>'
        '</w:del>'
        '<w:r><w:t xml:space="preserve"> Some replacement prose.</w:t></w:r>'
        '</w:p>'
    )
    doc = (
        f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f'<w:document xmlns:w="{W}"><w:body>'
        f'<w:p><w:r><w:t>Abstract.</w:t></w:r></w:p>'
        f'<w:p><w:pPr><w:pStyle w:val="Heading 1"/></w:pPr><w:r><w:t>Introduction</w:t></w:r></w:p>'
        f'{body}'
        f'</w:body></w:document>'
    ).encode("utf-8")
    with zipfile.ZipFile(inp, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", _MIN_CT)
        z.writestr("_rels/.rels", _MIN_RELS_PKG)
        z.writestr("word/_rels/document.xml.rels", _MIN_RELS_DOC)
        z.writestr("word/document.xml", doc)

    _, actions = apply_acronym_corrections(
        str(inp), str(out), next_change_id=1,
        accepted_acronyms={"LMS": ["learning management system"]},
    )

    flagged = {a["acronym"] for a in actions}
    assert "LMS" not in flagged, (
        "LMS sits inside a <w:del> — the deletion will remove that text "
        f"from the document, so flagging it would produce a phantom issue. Got actions={actions}"
    )


def test_block_listed_tokens_are_never_flagged(tmp_path):
    """Block-listed tokens (USA, OK, NASA, iOS, …) never produce issues even
    when bare in the body without an inline introduction."""
    inp = tmp_path / "in.docx"
    out = tmp_path / "out.docx"
    _build_zoned_docx(
        inp,
        [
            (None, "Abstract intro paragraph."),
            ("Heading 1", "Introduction"),
            (None, "Participants from the USA and UK used iOS devices."),
            (None, "NASA published their results on TV. OK?"),
        ],
    )

    _, actions = apply_acronym_corrections(
        str(inp), str(out), next_change_id=1, accepted_acronyms=_EMPTY_ALLOW,
    )

    flagged = {a["acronym"] for a in actions}
    for token in ("USA", "UK", "iOS", "NASA", "TV", "OK"):
        assert token not in flagged, (
            f"{token} should be on the block-list and not flagged; got actions={actions}"
        )


def test_allow_list_takes_precedence_over_block_list(tmp_path):
    """If the editor adds a well-known org (e.g. NASA) to the allow-list, the
    block-list must NOT silence it — the allow-list always wins so the
    first-use check still fires and the comment supplies an expansion."""
    inp = tmp_path / "in.docx"
    out = tmp_path / "out.docx"
    _build_zoned_docx(
        inp,
        [
            (None, "Abstract intro paragraph."),
            ("Heading 1", "Introduction"),
            (None, "NASA partnered with the team on the launch."),
        ],
    )

    _, actions = apply_acronym_corrections(
        str(inp),
        str(out),
        next_change_id=1,
        accepted_acronyms={"NASA": ["National Aeronautics and Space Administration"]},
    )

    flagged = [a for a in actions if a["acronym"] == "NASA"]
    assert len(flagged) == 1, (
        "NASA was on both the allow-list and the block-list; allow-list "
        f"should win and produce one body issue. Got actions={actions}"
    )
    assert flagged[0]["zone"] == "body"


def test_client_acronyms_oecd_and_unesco_still_follow_first_use(tmp_path):
    """OECD and UNESCO are on the client's approved-acronyms list — bare
    body use without an introduction must still be flagged (and given the
    suggested expansion from the allow-list)."""
    inp = tmp_path / "in.docx"
    out = tmp_path / "out.docx"
    _build_zoned_docx(
        inp,
        [
            (None, "Abstract intro paragraph."),
            ("Heading 1", "Introduction"),
            (None, "The OECD and UNESCO published guidance last year."),
        ],
    )

    _, actions = apply_acronym_corrections(
        str(inp),
        str(out),
        next_change_id=1,
        accepted_acronyms={
            "OECD": ["Organisation for Economic Co-operation and Development"],
            "UNESCO": ["United Nations Educational, Scientific and Cultural Organization"],
        },
    )

    flagged = {a["acronym"] for a in actions}
    assert "OECD" in flagged
    assert "UNESCO" in flagged


def test_block_list_does_not_swallow_real_acronyms(tmp_path):
    """A novel acronym sitting next to block-listed tokens still fires."""
    inp = tmp_path / "in.docx"
    out = tmp_path / "out.docx"
    _build_zoned_docx(
        inp,
        [
            (None, "Abstract intro paragraph."),
            ("Heading 1", "Introduction"),
            (None, "The USA-based team used XYZQQ for their study."),
        ],
    )

    _, actions = apply_acronym_corrections(
        str(inp), str(out), next_change_id=1, accepted_acronyms=_EMPTY_ALLOW,
    )

    flagged = {a["acronym"] for a in actions}
    assert "XYZQQ" in flagged
    assert "USA" not in flagged


def test_abstract_flagged_when_only_defined_in_body(tmp_path):
    """The abstract is an independent zone and needs its OWN introduction. An
    acronym defined only in the body (e.g. 'machine translation (MT)' in the
    Introduction) does NOT satisfy a bare 'MT' in the abstract, so the abstract
    use is flagged — with the body's expansion surfaced as a suggestion."""
    inp = tmp_path / "in.docx"
    out = tmp_path / "out.docx"
    _build_zoned_docx(
        inp,
        [
            (None, "Abstract: MT is now widespread."),
            ("Heading 1", "Introduction"),
            (None, "Recent work has advanced machine translation (MT) systems."),
            (None, "Modern MT relies on neural networks."),
        ],
    )

    _, actions = apply_acronym_corrections(
        str(inp), str(out), next_change_id=1, accepted_acronyms=_EMPTY_ALLOW,
    )

    # Abstract MT is now flagged (front zone); the body's inline def silences
    # the body uses, so the only issue is the abstract one.
    front_issues = [a for a in actions if a["zone"] == "front"]
    assert len(front_issues) == 1
    assert front_issues[0]["acronym"] == "MT"
    # The known expansion (from the body def) is offered as a suggestion.
    assert front_issues[0]["expansion"] == "machine translation"
    assert front_issues[0]["needs_track_change"] is False
    assert [a for a in actions if a["zone"] == "body"] == []


def test_abstract_silent_when_introduced_in_abstract(tmp_path):
    """Regression: an introduction WITHIN the abstract silences later abstract
    uses (front zone is satisfied by its own def)."""
    inp = tmp_path / "in.docx"
    out = tmp_path / "out.docx"
    _build_zoned_docx(
        inp,
        [
            (None, "Abstract: machine translation (MT) is widespread. MT is fast."),
            ("Heading 1", "Introduction"),
            (None, "Body text with no acronyms."),
        ],
    )

    _, actions = apply_acronym_corrections(
        str(inp), str(out), next_change_id=1, accepted_acronyms=_EMPTY_ALLOW,
    )

    assert [a for a in actions if a["zone"] == "front"] == []


def test_track_change_replaces_with_full_form_and_acronym(tmp_path):
    """First body use is rewritten as 'full term (ACRO)', not just 'full term'."""
    inp = tmp_path / "in.docx"
    out = tmp_path / "out.docx"
    _build_zoned_docx(
        inp,
        [
            ("Heading 1", "Introduction"),
            (None, "Each SME reviewed the draft thoroughly."),
            ("Heading 1", "Method"),
            (None, "The Subject Matter Expert (SME) gave detailed feedback."),
        ],
    )

    _, _ = apply_acronym_corrections(
        str(inp), str(out), next_change_id=1, accepted_acronyms=_EMPTY_ALLOW,
    )

    root = _read_doc_root(out)
    ins_runs = root.findall(f".//{WQ}ins")
    assert len(ins_runs) == 1
    ins_text = "".join(t.text or "" for t in ins_runs[0].iter(f"{WQ}t"))
    assert ins_text == "Subject Matter Expert (SME)"


def test_anchor_attaches_to_first_problematic_occurrence(tmp_path):
    """The single comment range wraps the first issue's location."""
    inp = tmp_path / "in.docx"
    out = tmp_path / "out.docx"
    _build_zoned_docx(
        inp,
        [
            ("Heading 1", "Introduction"),
            (None, "Earlier text mentions ABCDE for the first time."),
            (None, "Later text mentions FGHIJ as well."),
        ],
    )

    _, _ = apply_acronym_corrections(
        str(inp), str(out), next_change_id=1, accepted_acronyms=_EMPTY_ALLOW,
    )

    root = _read_doc_root(out)
    body_paras = [el for el in root.find(f"{WQ}body") if el.tag == f"{WQ}p"]
    # The anchor must be in the first body paragraph that contains an issue,
    # i.e. the paragraph mentioning ABCDE (paragraph index 1; 0 is the heading).
    para_with_anchor = next(
        (p for p in body_paras if p.find(f".//{WQ}commentRangeStart") is not None),
        None,
    )
    assert para_with_anchor is not None
    text = "".join(t.text or "" for t in para_with_anchor.iter(f"{WQ}t"))
    assert "ABCDE" in text and "FGHIJ" not in text


def test_acronyms_in_acknowledgements_or_references_are_ignored(tmp_path):
    """Anything from Acknowledgements onwards is outside the bot's scope."""
    inp = tmp_path / "in.docx"
    out = tmp_path / "out.docx"
    _build_zoned_docx(
        inp,
        [
            ("Heading 1", "Introduction"),
            (None, "We deployed XYZQQ in field trials."),
            ("Heading 1", "Acknowledgements"),
            (None, "Thanks to the XYZQQ team for support."),
            ("Heading 1", "References"),
            (None, "Smith, J. ABCDE journal article."),
        ],
    )

    _, actions = apply_acronym_corrections(
        str(inp), str(out), next_change_id=1, accepted_acronyms=_EMPTY_ALLOW,
    )

    # Only the body XYZQQ fires; ack and references are ignored.
    assert [a["acronym"] for a in actions] == ["XYZQQ"]


def test_inline_def_in_body_silences_subsequent_body_uses(tmp_path):
    """Once introduced in the body, later body uses are correct journal style."""
    inp = tmp_path / "in.docx"
    out = tmp_path / "out.docx"
    _build_zoned_docx(
        inp,
        [
            ("Heading 1", "Introduction"),
            (None, "Recent work advanced machine translation (MT) systems."),
            (None, "MT is now widely deployed in industry."),
            (None, "Modern MT pipelines depend on attention."),
        ],
    )

    _, actions = apply_acronym_corrections(
        str(inp), str(out), next_change_id=1, accepted_acronyms=_EMPTY_ALLOW,
    )

    assert actions == []


def test_bare_use_before_inline_def_still_flagged(tmp_path):
    """Bare use before the inline def is 'used before defined' and gets a
    track-change rewrite using the (later-discovered) expansion."""
    inp = tmp_path / "in.docx"
    out = tmp_path / "out.docx"
    _build_zoned_docx(
        inp,
        [
            ("Heading 1", "Introduction"),
            (None, "Each SME reviewed the draft thoroughly."),
            (None, "The Subject Matter Expert (SME) gave detailed feedback."),
            (None, "Later, every SME signed off on the manuscript."),
        ],
    )

    _, actions = apply_acronym_corrections(
        str(inp), str(out), next_change_id=1, accepted_acronyms=_EMPTY_ALLOW,
    )

    # One body issue on the early bare use; later bare uses (after the def)
    # are silent.
    assert len(actions) == 1
    assert actions[0]["acronym"] == "SME"
    assert actions[0]["expansion"] == "Subject Matter Expert"
    assert actions[0]["needs_track_change"] is True


def test_acronym_inside_parentheses_is_skipped(tmp_path):
    """Acronyms inside `(...)` are definitions or citations — never flag."""
    inp = tmp_path / "in.docx"
    out = tmp_path / "out.docx"
    _build_zoned_docx(
        inp,
        [
            ("Heading 1", "Introduction"),
            (None, "The deployment (see XYZ for details) succeeded."),
        ],
    )

    _, actions = apply_acronym_corrections(
        str(inp), str(out), next_change_id=1, accepted_acronyms=_EMPTY_ALLOW,
    )

    assert actions == []


def test_skips_heading_paragraphs(tmp_path):
    """Heading paragraphs don't contribute issues even though they trigger zone
    transitions."""
    inp = tmp_path / "in.docx"
    out = tmp_path / "out.docx"
    _build_zoned_docx(
        inp,
        [
            ("Heading 1", "Introduction"),
            ("Heading 1", "FOOBR Overview"),
            (None, "The FOOBR module handles ingest."),
        ],
    )

    _, actions = apply_acronym_corrections(
        str(inp), str(out), next_change_id=1, accepted_acronyms=_EMPTY_ALLOW,
    )

    # Heading paragraph occurrence skipped via _SKIP_STYLES; body paragraph
    # produces a single issue.
    assert len(actions) == 1
    assert actions[0]["acronym"] == "FOOBR"


def test_zone_transition_handles_numbered_heading_prefix(tmp_path):
    """`1. Introduction` / `II. Acknowledgements` are valid zone boundaries."""
    inp = tmp_path / "in.docx"
    out = tmp_path / "out.docx"
    _build_zoned_docx(
        inp,
        [
            (None, "Abstract: FOOBR is unfamiliar."),
            ("Heading 1", "1. Introduction"),
            (None, "FOOBR is the framework under study."),
            ("Heading 1", "II. Acknowledgements"),
            (None, "Thanks to the FOOBR contributors."),
        ],
    )

    _, actions = apply_acronym_corrections(
        str(inp), str(out), next_change_id=1, accepted_acronyms=_EMPTY_ALLOW,
    )

    zones = [a["zone"] for a in actions]
    # One front issue (abstract FOOBR) and one body issue (numbered
    # Introduction transition). Acknowledgements is outside.
    assert zones == ["front", "body"]


def test_comment_id_continues_from_existing_comments(tmp_path):
    """If the docx already has comments from earlier passes, the new one gets
    the next free id."""
    inp = tmp_path / "in.docx"
    out = tmp_path / "out.docx"

    existing_comments = (
        f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f'<w:comments xmlns:w="{W}">'
        f'<w:comment w:id="7" w:author="Prev" w:date="2024-01-01T00:00:00Z" w:initials="P">'
        f'<w:p><w:r><w:t>Previous comment</w:t></w:r></w:p>'
        f'</w:comment>'
        f'</w:comments>'
    ).encode("utf-8")
    body = (
        '<w:p><w:pPr><w:pStyle w:val="Heading 1"/></w:pPr>'
        '<w:r><w:t>Introduction</w:t></w:r></w:p>'
        '<w:p><w:r><w:t>The XYZ scheme was tested.</w:t></w:r></w:p>'
    )
    doc = (
        f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f'<w:document xmlns:w="{W}"><w:body>{body}</w:body></w:document>'
    ).encode("utf-8")
    rels_doc = (
        b'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        b'<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        b'<Relationship Id="rIdComments" '
        b'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/comments" '
        b'Target="comments.xml"/>'
        b'</Relationships>'
    )
    ct_with_comments = _MIN_CT.replace(
        b"</Types>",
        b'<Override PartName="/word/comments.xml" '
        b'ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.comments+xml"/>'
        b"</Types>",
    )
    with zipfile.ZipFile(inp, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", ct_with_comments)
        z.writestr("_rels/.rels", _MIN_RELS_PKG)
        z.writestr("word/_rels/document.xml.rels", rels_doc)
        z.writestr("word/document.xml", doc)
        z.writestr("word/comments.xml", existing_comments)

    _, actions = apply_acronym_corrections(
        str(inp), str(out), next_change_id=1, accepted_acronyms=_EMPTY_ALLOW,
    )

    assert len(actions) == 1
    # All issues share the same consolidated comment id, which is 7 + 1 = 8.
    assert actions[0]["comment_id"] == 8


def test_consolidated_comment_includes_track_change_note(tmp_path):
    """When a track change is proposed, the bullet mentions it so the editor
    knows what to accept/reject."""
    inp = tmp_path / "in.docx"
    out = tmp_path / "out.docx"
    _build_zoned_docx(
        inp,
        [
            ("Heading 1", "Introduction"),
            (None, "We used the LMS for the entire course."),
        ],
    )

    _, _ = apply_acronym_corrections(
        str(inp), str(out), next_change_id=1, accepted_acronyms=_LMS_ALLOW,
    )

    comments = _read_comments_root(out)
    assert comments is not None
    txt = _comment_visible_text(comments)
    assert "LMS" in txt
    assert "tracked change" in txt.lower()


def test_title_style_acronyms_are_completely_ignored(tmp_path):
    """Acronyms in the manuscript title produce NO issue at all — no bullet
    in the consolidated comment, no tracked-change rewrite. The title is
    Sam's territory (title case only); the acronym pass only operates from
    the abstract onwards."""
    inp = tmp_path / "in.docx"
    out = tmp_path / "out.docx"
    _build_zoned_docx(
        inp,
        [
            ("Article Title", "Using LMS in Higher Education"),
            ("Heading 1", "Introduction"),
            (None, "Body text without acronym issues."),
        ],
    )

    _, actions = apply_acronym_corrections(
        str(inp), str(out), next_change_id=1, accepted_acronyms=_LMS_ALLOW,
    )

    # No issues anywhere — the only acronym in the doc is in the title.
    assert actions == []

    root = _read_doc_root(out)
    assert root.findall(f".//{WQ}ins") == []
    assert root.findall(f".//{WQ}del") == []
    # No consolidated comment either.
    assert _read_comments_root(out) is None


def test_title_acronym_does_not_silence_body_acronym(tmp_path):
    """Crucially, ignoring the title must NOT cause the title's acronym to
    pre-introduce the same acronym for the body. A bare LMS in body still
    needs its own inline introduction — the title doesn't count."""
    inp = tmp_path / "in.docx"
    out = tmp_path / "out.docx"
    _build_zoned_docx(
        inp,
        [
            ("Article Title", "Using LMS in Higher Education"),
            ("Heading 1", "Introduction"),
            (None, "The LMS supports weekly formative feedback."),
        ],
    )

    _, actions = apply_acronym_corrections(
        str(inp), str(out), next_change_id=1, accepted_acronyms=_LMS_ALLOW,
    )

    # Body's LMS still fires; title's LMS does not.
    flagged_zones = [a["zone"] for a in actions]
    assert "title" not in flagged_zones
    assert flagged_zones == ["body"]
    assert actions[0]["acronym"] == "LMS"

    # Body gets its tracked-change introduction.
    root = _read_doc_root(out)
    assert len(root.findall(f".//{WQ}ins")) == 1
    assert len(root.findall(f".//{WQ}del")) == 1


def test_fallback_title_detection_also_silences_first_front_paragraph(tmp_path):
    """If the doc uses no explicit Article Title style, the first non-empty
    front paragraph is treated as the title and skipped the same way."""
    inp = tmp_path / "in.docx"
    out = tmp_path / "out.docx"
    _build_zoned_docx(
        inp,
        [
            (None, "Using LMS in Higher Education"),  # fallback title (no style)
            ("Authors", "A. Author"),
            ("Heading 1", "Introduction"),
            (None, "The LMS supports weekly formative feedback."),
        ],
    )

    _, actions = apply_acronym_corrections(
        str(inp), str(out), next_change_id=1, accepted_acronyms=_LMS_ALLOW,
    )

    flagged_zones = [a["zone"] for a in actions]
    # Title (paragraph 0, fallback-detected) is silenced; body still fires.
    assert "title" not in flagged_zones
    assert flagged_zones == ["body"]
