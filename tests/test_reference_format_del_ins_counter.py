"""Regression test: `_apply_del_ins` (the APS tracked-change surgical rewrite)
must return the updated change-id counter. It previously had no return
statement, so `apply_reference_format_corrections` set `next_change_id = None`
after the first rewritten entry and the second entry crashed with
`TypeError: unsupported operand type(s) for +=: 'NoneType' and 'int'`
(surfaced in traces as a minor "Reference format corrections" stage error).
"""

from lxml import etree

from app.services.reference_format_corrections import _apply_del_ins

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"


def _para(text: str) -> etree._Element:
    xml = f'<w:p xmlns:w="{W}"><w:r><w:t xml:space="preserve">{text}</w:t></w:r></w:p>'
    return etree.fromstring(xml.encode())


def test_apply_del_ins_returns_incremented_counter():
    para = _para("alpha beta")
    end_id = _apply_del_ins(para, "alpha beta", "alpha gamma", 7000)
    # replace = one del + one ins = two ids
    assert end_id == 7002
    assert para.find(f"{{{W}}}del") is not None
    assert para.find(f"{{{W}}}ins") is not None


def test_apply_del_ins_threads_counter_across_entries():
    first_id = _apply_del_ins(_para("alpha beta"), "alpha beta", "alpha gamma", 7000)
    second_id = _apply_del_ins(_para("delta epsilon"), "delta epsilon", "delta zeta", first_id)
    # The counter must thread the incremented value across entries, not reset
    # to None (which used to crash the second entry).
    assert second_id == first_id + 2


def test_apply_del_ins_multi_opcodes_increments_per_change():
    # Three opcodes (equal / del+ins / equal) for a replace in the middle.
    para = _para("one two three five six")
    end_id = _apply_del_ins(para, "one two three five six", "one two four five six", 50)
    assert end_id == 52
    assert para.find(f"{{{W}}}del") is not None
