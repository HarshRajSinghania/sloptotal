from types import SimpleNamespace

from app.cache import compute_text_hash, is_cacheable_report, normalize_text


def test_hash_ignores_case_and_whitespace():
    assert compute_text_hash("Hello   World\n") == compute_text_hash("hello world")


def test_hash_differs_for_different_text():
    assert compute_text_hash("one text") != compute_text_hash("another text")


def test_normalize_applies_nfkc():
    assert normalize_text("ﬁne") == "fine"


def _report(*details):
    return SimpleNamespace(engine_results=[SimpleNamespace(details=d) for d in details])


def test_reports_with_engine_failures_are_not_cached():
    assert is_cacheable_report(_report("score 0.4", "fine"))
    assert not is_cacheable_report(_report("ok", "Model loading failed: OOM"))
    assert not is_cacheable_report(_report("Engine error: timeout"))
