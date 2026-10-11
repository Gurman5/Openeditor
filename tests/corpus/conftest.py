"""Shared pytest setup for tests/corpus."""


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "pipeline: runs the engine's doc_analysis_pipeline (slow, ~3 s per document); "
        'skip with -m "not pipeline"',
    )
