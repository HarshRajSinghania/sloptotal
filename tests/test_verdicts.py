import pytest

from app import config
from app.schemas import Verdict, score_to_engine_verdict, score_to_verdict_str


def test_band_edges_come_from_config():
    assert score_to_verdict_str(config.SCORE_CLEAN).startswith("Clean")
    assert score_to_verdict_str(config.SCORE_CLEAN + 0.1) == "Low risk"
    assert score_to_verdict_str(config.SCORE_LOW_RISK + 0.1) == "Suspicious"
    assert score_to_verdict_str(config.SCORE_SUSPICIOUS + 0.1) == "Likely AI-generated"
    assert score_to_verdict_str(config.SCORE_LIKELY_AI + 0.1) == "Slop detected"


def test_bands_are_ordered():
    assert (
        0
        < config.SCORE_CLEAN
        < config.SCORE_LOW_RISK
        < config.SCORE_SUSPICIOUS
        < config.SCORE_LIKELY_AI
        < 100
    )


@pytest.mark.parametrize(
    "score,verdict",
    [
        (0.0, Verdict.CLEAN),
        (0.39, Verdict.CLEAN),
        (0.5, Verdict.SUSPICIOUS),
        (0.9, Verdict.SLOP),
    ],
)
def test_engine_verdict(score, verdict):
    assert score_to_engine_verdict(score) == verdict
