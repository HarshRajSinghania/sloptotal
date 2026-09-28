"""The ensemble calibration is pure arithmetic over engine scores, so its
contract can be checked without running a single model."""

from app.analyzer import _calculate_full_calibrated_score, _engines
from app.config import ENGINE_WEIGHTS, SCORE_CLEAN, SCORE_LIKELY_AI
from app.schemas import EngineResult, score_to_engine_verdict
from tests.samples import AI_TEXT, HUMAN_TEXT


def _results(score: float) -> dict[str, EngineResult]:
    return {
        key: EngineResult(
            engine_name=key,
            score=score,
            verdict=score_to_engine_verdict(score),
            details="",
        )
        for key, _ in _engines
    }


def test_every_weighted_engine_is_registered():
    registered = {key for key, _ in _engines}
    assert set(ENGINE_WEIGHTS) <= registered


def test_unanimous_low_scores_are_clean():
    score, _ = _calculate_full_calibrated_score(_results(0.02), HUMAN_TEXT)
    assert score <= SCORE_CLEAN


def test_unanimous_high_scores_on_ai_text_are_flagged():
    score, confidence = _calculate_full_calibrated_score(_results(0.97), AI_TEXT)
    assert score > SCORE_LIKELY_AI
    assert confidence in {"high", "medium"}


def test_score_is_monotonic_in_engine_scores():
    scores = [
        _calculate_full_calibrated_score(_results(s), AI_TEXT)[0]
        for s in (0.1, 0.4, 0.7, 0.95)
    ]
    assert scores == sorted(scores)


def test_score_stays_in_range():
    for s in (0.0, 1.0):
        score, _ = _calculate_full_calibrated_score(_results(s), HUMAN_TEXT)
        assert 0.0 <= score <= 100.0
