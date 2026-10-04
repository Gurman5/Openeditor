"""Contract tests for reporting ownership (D-01 remediation, Phase 1).

Every validator rule id must have exactly one reporting home, and the
Sam-fixed exclusion must be a single shared object — not a copy-pasted set
in each consumer. These tests guard the contract, not individual verdicts:
they pass regardless of whether a given check passes or fails on a fixture.
"""
import glob
import os
import re

from app.domain import reporting_ownership as ro
from app.services.jutlp_validator import validate

_PACK = os.path.join(
    os.path.dirname(__file__), "jutlp_sample_docx_test_pack", "*.docx"
)


def _all_emitted_rule_ids() -> set[str]:
    ids: set[str] = set()
    for path in sorted(glob.glob(_PACK)):
        report = validate(path)
        ids.update(r["rule_id"] for r in report["results"])
    assert ids, "sample pack produced no rule ids — fixtures or validate() broken"
    return ids


def _family(rule_id: str) -> str:
    return re.match(r"[A-Z]+", rule_id).group(0)


class TestSamFixedIdsAreReal:
    def test_every_sam_fixed_id_is_emitted_by_the_validator(self):
        # Source-based, not fixture-based: conditional rules (e.g. TAB001,
        # STY004) only emit when the triggering content exists, so absence
        # across fixtures does not mean a dead id. What must hold is that
        # every filtered id is a rule the validator *can* emit.
        source = open("app/services/jutlp_validator.py").read()
        # Any quoted STABLE id: direct _result("FP007") calls AND tuple-table
        # entries like ("FP004", ...) in check_front_page.
        literal_ids = set(re.findall(r'"([A-Z]{2,6}\d{3})"', source))
        generated_families = set(
            re.findall(r'f"([A-Z]+)\{', source)
        )  # SEC/MET/DIS/STY/ANDOR/ETC/DOTPT via f-string
        for rule_id in ro.SAM_FIXED_RULE_IDS:
            family = _family(rule_id)
            assert (
                rule_id in literal_ids or family in generated_families
            ), f"{rule_id} is filtered but the validator can never emit it"

    def test_no_per_occurrence_id_in_sam_fixed(self):
        # ANDOR{n}/ETC{n}/DOTPT{n} are per-occurrence ids; a fixed set can only
        # hold stable rule ids. The base forms (ANDOR000 etc.) are pass-only
        # sentinels and must never be filtered either.
        for rule_id in ro.SAM_FIXED_RULE_IDS:
            assert re.fullmatch(r"[A-Z]+\d{3}", rule_id), (
                f"{rule_id} is not a stable rule id"
            )


class TestFamilyVerdictsCoverEverything:
    def test_every_emitted_family_has_a_verdict(self):
        emitted = _all_emitted_rule_ids()
        families = {_family(r) for r in emitted}
        missing = sorted(f for f in families if f not in ro.FAMILY_VERDICTS)
        assert not missing, (
            f"validator emits families with no reporting verdict: {missing}. "
            "Add them to FAMILY_VERDICTS with an explicit verdict."
        )

    def test_verdicts_use_known_values(self):
        allowed = {"tracked-change", "comment", "ref-section", "neither"}
        for family, verdict in ro.FAMILY_VERDICTS.items():
            assert verdict[0] in allowed, (
                f"{family}: unknown verdict {verdict[0]!r}"
            )

    def test_sam_fixed_ids_agree_with_family_table(self):
        # Each Sam-fixed id must appear as a listed exception under its
        # family's entry, so the table and the set cannot drift apart.
        for rule_id in ro.SAM_FIXED_RULE_IDS:
            family = _family(rule_id)
            entry = ro.FAMILY_VERDICTS[family]
            exceptions = entry[2] if len(entry) > 2 else []
            assert rule_id in exceptions, (
                f"{rule_id} is Sam-fixed but not listed under FAMILY_VERDICTS[{family!r}]"
            )


class TestSingleSource:
    def test_pipeline_and_api_share_the_same_set_object(self):
        import app.main as main
        import app.pipelines.feedback_gen_pipeline as pipe

        assert main.is_sam_fixed is ro.is_sam_fixed
        # The pipeline must filter doc comments with the shared set: no local
        # copy of the literal ids may remain in either consumer.
        for module in (main, pipe):
            source = open(module.__file__).read()
            assert "_SAM_FIXED_RULE_IDS" not in source, (
                f"{module.__name__} still defines a local copy of the id set"
            )
