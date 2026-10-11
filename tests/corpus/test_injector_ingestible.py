"""K-I4: every injected document must be ingestible by the CURRENT engine.

Each injected doc is run through the real in-process pipeline,
app.pipelines.feedback_gen_pipeline.doc_analysis_pipeline, and must:
  1. return without raising,
  2. write an output .docx that passes check_validity (K-H1),
  3. produce no stage error that the clean base doesn't also produce.
(The pipeline catches errors inside its stages, so "no traceback" alone
would miss most failures.)

Runs OFFLINE and LLM-off. Nothing in app/ is edited; for this test run only:
  - llm_client.OPENAI_API_KEY is cleared (app/services/config.py loads .env on
    import, so unsetting the environment variable is not enough)
  - Crossref requests fail instantly instead of using the network
  - the Crossref cache is disabled, so app/services/.crossref_cache.json is
    never written

A document that genuinely fails in the engine is NOT fixed here: it is
marked xfail(strict=True) with the reason, to be reported to Track C.

Slow (~3 s per document). Skip with:  python -m pytest tests/corpus -m "not pipeline"
"""

import pytest
import requests

from tools.corpus.docx_view import check_validity
from tools.corpus.fixtures import build_good_docx
from tools.corpus.inject import RECIPES, inject

pytestmark = pytest.mark.pipeline

TWO_MODE = [r for r in RECIPES.values() if "style" in r.wheres]
FORMAT_COMPOSITE = ["APA-00", "APA-01", "APA-03", "APA-04", "APA-05"]
ONE_PER_ROW = ["APA-00", "APA-01", "APA-02a", "APA-03", "APA-04", "APA-05",
               "APA-08b", "APA-11a", "APA-12b", "APA-18a"]

CASES = (
    [pytest.param([rid], None, id=f"{rid}-default") for rid in RECIPES]
    + [pytest.param([r.id], "style", id=f"{r.id}-style") for r in TWO_MODE]
    + [pytest.param(FORMAT_COMPOSITE, None, id="composite-format"),
       pytest.param(ONE_PER_ROW, None, id="composite-one-per-row")]
)


@pytest.fixture(scope="module")
def engine():
    """doc_analysis_pipeline with the LLM off and the network blocked."""
    import app.services.ai.llm_client as llm_client
    import app.services.reference_checker as reference_checker
    from app.pipelines.feedback_gen_pipeline import doc_analysis_pipeline

    def no_network(*args, **kwargs):
        raise requests.ConnectionError("network blocked in K-I4 tests")

    with pytest.MonkeyPatch.context() as mp:
        mp.delenv("OPENAI_API_KEY", raising=False)
        mp.setattr(llm_client, "OPENAI_API_KEY", None)
        mp.setattr(reference_checker, "_CACHE_ENABLED", False)
        mp.setattr(reference_checker.requests, "get", no_network)
        yield doc_analysis_pipeline


def _run(engine, doc, out):
    result = engine(doc, output_path=out)
    errors = {(e["stage"], e["error"]) for e in result.get("stage_errors") or []}
    return result, errors


@pytest.fixture(scope="module")
def base_run(engine, tmp_path_factory):
    tmp = tmp_path_factory.mktemp("ingest_base")
    base = build_good_docx(tmp / "good.docx")
    _, errors = _run(engine, base, tmp / "good_out.docx")
    return base, errors


def test_clean_base_only_has_the_expected_llm_error(base_run):
    _, errors = base_run
    assert {stage for stage, _ in errors} == {"Editorial review (AI)"}


@pytest.mark.parametrize("defects, where", CASES)
def test_injected_doc_is_ingestible(engine, base_run, tmp_path, defects, where):
    base, base_errors = base_run
    doc = tmp_path / "injected.docx"
    inject(base, defects, doc, where=where)

    out = tmp_path / "engine_out.docx"
    result, errors = _run(engine, doc, out)

    assert out.exists(), f"engine wrote no output for {defects}"
    validity = check_validity(out)
    assert validity["valid"], f"engine output for {defects} is invalid: {validity['reasons']}"
    new_errors = errors - base_errors
    assert not new_errors, f"{defects} caused new engine stage errors: {sorted(new_errors)}"
