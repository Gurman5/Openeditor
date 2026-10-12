"""Guards against the two OOXML defects that made the download unopenable.

Word rejects a .docx whose XML is well-formed but violates ECMA-376, offering
to "repair" it instead. Neither python-docx nor lxml notices, which is why the
existing suite stayed green while every download was broken.
"""
import shutil
import zipfile
from pathlib import Path

import pytest
from lxml import etree

from app.pipelines.feedback_gen_pipeline import (
    _patch_settings_show_markup,
    _reconcile_comment_sidecars,
)
from app.services.output_generation import _inject_comment_markers
from tools.docx_ooxml_validator import validate

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
WQ = f"{{{W}}}"

REPO_ROOT = Path(__file__).resolve().parents[1]


def _read_part(path, name):
    with zipfile.ZipFile(path) as zf:
        return zf.read(name)


def _write_part(path, name, data):
    with zipfile.ZipFile(path) as zin:
        items = [(i, zin.read(i.filename)) for i in zin.infolist()]
    tmp = str(path) + ".rewrite"
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
        for info, payload in items:
            zout.writestr(info, data if info.filename == name else payload)
    shutil.move(tmp, path)


@pytest.fixture
def seed_docx(tmp_path):
    seed = REPO_ROOT / "tests" / "corpus" / "seed" / "seed-01.docx"
    if not seed.exists():  # pragma: no cover - fixture missing
        pytest.skip("seed-01.docx fixture not present")
    target = tmp_path / "seed.docx"
    shutil.copy(seed, target)
    return target


class TestSettingsPatch:
    def test_emits_only_schema_valid_elements(self, seed_docx):
        _patch_settings_show_markup(str(seed_docx))
        root = etree.fromstring(_read_part(seed_docx, "word/settings.xml"))
        tags = [c.tag.split("}")[-1] for c in root if c.tag.startswith(WQ)]
        assert "showDel" not in tags
        assert "showInsMarkup" not in tags

    def test_revision_view_uses_valid_attributes(self, seed_docx):
        _patch_settings_show_markup(str(seed_docx))
        root = etree.fromstring(_read_part(seed_docx, "word/settings.xml"))
        rev = root.find(f"{WQ}revisionView")
        assert rev is not None
        attrs = {k.split("}")[-1] for k in rev.attrib}
        assert attrs <= {"markup", "comments", "insDel", "formatting", "inkAnnotations"}

    def test_is_idempotent(self, seed_docx):
        _patch_settings_show_markup(str(seed_docx))
        first = _read_part(seed_docx, "word/settings.xml")
        _patch_settings_show_markup(str(seed_docx))
        assert _read_part(seed_docx, "word/settings.xml") == first

    def test_output_passes_validator(self, seed_docx):
        _patch_settings_show_markup(str(seed_docx))
        assert validate(str(seed_docx)) == []

    def test_legacy_output_is_repaired_in_place(self, tmp_path, seed_docx):
        """A file written by the old code must be cleaned up, not just avoided."""
        root = etree.fromstring(_read_part(seed_docx, "word/settings.xml"))
        show_del = etree.Element(f"{WQ}showDel")
        show_ins = etree.Element(f"{WQ}showInsMarkup")
        root.insert(0, show_ins)
        root.insert(0, show_del)
        _write_part(
            seed_docx,
            "word/settings.xml",
            etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True),
        )
        assert validate(str(seed_docx)) != []

        _patch_settings_show_markup(str(seed_docx))
        assert validate(str(seed_docx)) == []


class TestCommentAnchorPlacement:
    def test_range_start_goes_after_pPr(self):
        para = etree.Element(f"{WQ}p", nsmap={"w": W})
        p_pr = etree.SubElement(para, f"{WQ}pPr")
        etree.SubElement(p_pr, f"{WQ}pStyle")
        run = etree.SubElement(para, f"{WQ}r")
        etree.SubElement(run, f"{WQ}t").text = "body"

        _inject_comment_markers(para, 7)

        kids = list(para)
        assert kids[0] is p_pr, "w:pPr must stay first"
        assert kids[1].tag == f"{WQ}commentRangeStart"
        assert kids[1].get(f"{WQ}id") == "7"

    def test_range_start_after_existing_range(self):
        para = etree.Element(f"{WQ}p", nsmap={"w": W})
        p_pr = etree.SubElement(para, f"{WQ}pPr")
        existing = etree.Element(f"{WQ}commentRangeStart")
        existing.set(f"{WQ}id", "1")
        para.insert(1, existing)

        _inject_comment_markers(para, 2)

        kids = list(para)
        assert kids[0] is p_pr
        assert kids[1] is existing
        assert kids[2].tag == f"{WQ}commentRangeStart"
        assert kids[2].get(f"{WQ}id") == "2"

    def test_paragraph_without_pPr(self):
        para = etree.Element(f"{WQ}p", nsmap={"w": W})
        _inject_comment_markers(para, 3)
        assert list(para)[0].tag == f"{WQ}commentRangeStart"

    def test_samfix_variant_also_respects_pPr(self):
        from app.services.output_generation_samfix import (
            _inject_comment_markers as samfix_inject,
        )

        para = etree.Element(f"{WQ}p", nsmap={"w": W})
        etree.SubElement(para, f"{WQ}pPr")
        samfix_inject(para, 11)
        kids = list(para)
        assert kids[0].tag == f"{WQ}pPr"
        assert kids[1].tag == f"{WQ}commentRangeStart"


class TestCommentSidecars:
    """Word 2013+ threaded-comment sidecars must match comments.xml."""

    SIDECARS = ("word/commentsExtended.xml", "word/commentsIds.xml", "word/commentsExtensible.xml")

    REL_TYPE_BASE = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/"
    CT_EXT_BASE = "application/vnd.openxmlformats-officedocument.wordprocessingml."
    CT_MAP = {
        "commentsExtended": f"{CT_EXT_BASE}commentsExtended+xml",
        "commentsIds": f"{CT_EXT_BASE}commentsIds+xml",
        "commentsExtensible": f"{CT_EXT_BASE}commentsExtensible+xml",
    }

    def _make_comments_xml(self, para_ids):
        w = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
        w14 = "http://schemas.microsoft.com/office/word/2010/wordml"
        root = etree.Element(f"{{{w}}}comments", nsmap={"w": w})
        for i, para_id in enumerate(para_ids, start=1):
            c = etree.SubElement(root, f"{{{w}}}comment")
            c.set(f"{{{w}}}id", str(i))
            p = etree.SubElement(c, f"{{{w}}}p")
            if para_id is not None:
                p.set(f"{{{w14}}}paraId", para_id)
        return etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True)

    def _make_sidecar(self, tag_ns, tag_name, attr_ns, attr_name, para_ids):
        root = etree.Element(f"{{{tag_ns}}}{tag_name}", nsmap={tag_name: tag_ns})
        for pid in para_ids:
            el = etree.SubElement(root, f"{{{tag_ns}}}{tag_name}")
            el.set(f"{{{attr_ns}}}{attr_name}", pid)
        return etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True)

    def _inject(self, path, *, comments=True, comment_para_ids=(), sidecar_para_ids=("AAAA0001",)):
        """Add comments.xml and/or sidecar parts, with matching rels + content types."""
        additions = {}
        ct_adds = []
        rel_adds = []

        w15 = "http://schemas.microsoft.com/office/word/2012/wordml"
        w16cid = "http://schemas.microsoft.com/office/word/2016/wordml/cid"
        w16cex = "http://schemas.microsoft.com/office/word/2018/wordml/cex"
        sidecar_specs = {
            "commentsExtended": (w15, "commentEx", w15, "paraId"),
            "commentsIds": (w16cid, "commentId", w16cid, "paraId"),
            "commentsExtensible": (w16cex, "commentExtensible", w16cex, "paraId"),
        }

        if comments:
            additions["word/comments.xml"] = self._make_comments_xml(list(comment_para_ids))
            ct_adds.append(("/word/comments.xml", f"{self.CT_EXT_BASE}comments+xml"))
        for key, (tag_ns, tag_name, attr_ns, attr_name) in sidecar_specs.items():
            additions[f"word/{key}.xml"] = self._make_sidecar(
                tag_ns, tag_name, attr_ns, attr_name, list(sidecar_para_ids)
            )
            ct_adds.append((f"/word/{key}.xml", self.CT_MAP[key]))
            rel_adds.append((key, f"{self.REL_TYPE_BASE}{key}"))

        with zipfile.ZipFile(path) as z:
            items = [(i, z.read(i.filename)) for i in z.infolist()]

        ct = etree.fromstring(dict((i.filename, d) for i, d in items)["[Content_Types].xml"])
        ns = "http://schemas.openxmlformats.org/package/2006/content-types"
        for part_name, ctype in ct_adds:
            o = etree.SubElement(ct, f"{{{ns}}}Override")
            o.set("PartName", part_name)
            o.set("ContentType", ctype)
        ct_bytes = etree.tostring(ct, xml_declaration=True, encoding="UTF-8", standalone=True)

        rels = etree.fromstring(dict((i.filename, d) for i, d in items)["word/_rels/document.xml.rels"])
        rns = "http://schemas.openxmlformats.org/package/2006/relationships"
        for i, (target, rtype) in enumerate(rel_adds, start=900):
            rel = etree.SubElement(rels, f"{{{rns}}}Relationship")
            rel.set("Id", f"rId{i}")
            rel.set("Type", rtype)
            rel.set("Target", f"{target}.xml")
        rels_bytes = etree.tostring(rels, xml_declaration=True, encoding="UTF-8", standalone=True)

        additions["[Content_Types].xml"] = ct_bytes
        additions["word/_rels/document.xml.rels"] = rels_bytes

        with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zout:
            for info, data in items:
                zout.writestr(info, additions.pop(info.filename, data))
            for name, data in additions.items():
                zout.writestr(name, data)

    def _names(self, path):
        with zipfile.ZipFile(path) as z:
            return set(z.namelist()), z.read("word/_rels/document.xml.rels"), z.read("[Content_Types].xml")

    def test_strips_sidecars_when_no_comments_part(self, seed_docx):
        self._inject(str(seed_docx), comments=False)
        assert validate(str(seed_docx)) != []

        _reconcile_comment_sidecars(str(seed_docx))

        names, rels, ct = self._names(str(seed_docx))
        for part in self.SIDECARS:
            assert part not in names
        assert b"commentsIds" not in rels
        assert b"commentsExtensible" not in ct
        assert validate(str(seed_docx)) == []

    def test_strips_sidecars_when_comments_have_no_para_id(self, seed_docx):
        self._inject(str(seed_docx), comments=True, comment_para_ids=[None, None])
        assert any("paraId" in p for p in validate(str(seed_docx)))

        _reconcile_comment_sidecars(str(seed_docx))

        names, _, _ = self._names(str(seed_docx))
        assert not any(p in names for p in self.SIDECARS)
        assert "word/comments.xml" in names, "the comments themselves must survive"
        assert validate(str(seed_docx)) == []

    def test_keeps_sidecars_that_still_match(self, seed_docx):
        self._inject(
            str(seed_docx),
            comments=True,
            comment_para_ids=["AAAA0001", "BBBB0002"],
            sidecar_para_ids=("AAAA0001", "BBBB0002"),
        )
        assert validate(str(seed_docx)) == []

        _reconcile_comment_sidecars(str(seed_docx))

        names, _, _ = self._names(str(seed_docx))
        assert all(p in names for p in self.SIDECARS)

    def test_drops_orphan_sidecar_entries_when_para_ids_match(self, seed_docx):
        self._inject(
            str(seed_docx),
            comments=True,
            comment_para_ids=["AAAA0001"],
            sidecar_para_ids=("AAAA0001", "DEAD0003"),
        )
        assert any("absent from comments.xml" in p for p in validate(str(seed_docx)))

        _reconcile_comment_sidecars(str(seed_docx))

        names, _, _ = self._names(str(seed_docx))
        assert all(p in names for p in self.SIDECARS)
        with zipfile.ZipFile(seed_docx) as z:
            ids = etree.fromstring(z.read("word/commentsIds.xml"))
        assert len(ids) == 1
        assert validate(str(seed_docx)) == []

    def test_no_op_when_no_sidecars(self, seed_docx):
        before = _read_part(seed_docx, "word/settings.xml")
        _reconcile_comment_sidecars(str(seed_docx))
        assert _read_part(seed_docx, "word/settings.xml") == before
        assert validate(str(seed_docx)) == []


class TestValidatorItself:
    def test_flags_sidecars_without_comments_xml(self, seed_docx):
        TestCommentSidecars()._inject(str(seed_docx), comments=False)
        problems = validate(str(seed_docx))
        assert any("no word/comments.xml" in p for p in problems)

    def test_detects_ppr_violation_in_a_docx(self, tmp_path):
        src = REPO_ROOT / "tests" / "corpus" / "seed" / "seed-01.docx"
        if not src.exists():  # pragma: no cover
            pytest.skip("seed-01.docx fixture not present")
        target = tmp_path / "broken.docx"
        shutil.copy(src, target)

        root = etree.fromstring(_read_part(target, "word/document.xml"))
        para = next(root.iter(f"{WQ}p"))
        para.insert(0, etree.Element(f"{WQ}commentRangeStart"))
        _write_part(
            target,
            "word/document.xml",
            etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True),
        )

        problems = validate(str(target))
        assert any("w:pPr" in p for p in problems)

    def test_clean_seed_passes(self, seed_docx):
        assert validate(str(seed_docx)) == []
