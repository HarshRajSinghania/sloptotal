"""Concurrent first requests must never see a half-loaded model.

Regression: requests arriving while the preloader was still loading got a
model without its tokenizer ('NoneType' object has no attribute 'encode'),
so four classifiers silently scored 0.0 and the report came back "Clean".
"""

import threading
import time
from concurrent.futures import ThreadPoolExecutor

import pytest

from app.engines import classifier_tmr
from app.model_pool import ModelPool


@pytest.fixture
def slow_tmr_loader(monkeypatch):
    calls = []

    def fake_replica():
        calls.append(1)
        time.sleep(0.2)
        return object(), object()

    monkeypatch.setattr(classifier_tmr, "_load_one_replica", fake_replica)
    monkeypatch.setattr(classifier_tmr, "_model", None)
    monkeypatch.setattr(classifier_tmr, "_tokenizer", None)
    monkeypatch.setattr(classifier_tmr, "_pool_size", 1)
    return calls


def test_concurrent_first_loads_see_a_complete_model(slow_tmr_loader):
    with ThreadPoolExecutor(max_workers=8) as ex:
        pairs = list(ex.map(lambda _: classifier_tmr._load_model(), range(8)))
    assert all(model is not None and tok is not None for model, tok in pairs)
    assert len({id(model) for model, _ in pairs}) == 1
    assert len(slow_tmr_loader) == 1


def test_pool_acquire_waits_for_initialization():
    pool = ModelPool(lambda: (time.sleep(0.2), "model")[1], pool_size=2, name="t")
    got = []

    def request():
        with pool.acquire(timeout=5) as replica:
            got.append(replica)

    t = threading.Thread(target=request)
    t.start()  # arrives before any replica exists
    pool.initialize()
    pool.initialize()  # idempotent: a second call must not add replicas
    t.join()
    assert got == ["model"]
    assert pool._pool.qsize() == 2
