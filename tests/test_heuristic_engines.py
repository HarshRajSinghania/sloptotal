"""The regex/statistics engines need no model weights, so they can be pinned
down exactly. The neural engines are measured in tests/eval/ instead."""

import pytest

from app.engines.formulaic import FormulaicEngine
from app.engines.linguistic import LinguisticEngine
from app.engines.readability import ReadabilityEngine
from app.engines.sentiment import SentimentEngine
from app.engines.structural import StructuralEngine
from app.engines.vocabulary import VocabularyEngine
from tests.samples import AI_TEXT, HUMAN_TEXT

ENGINES = [
    LinguisticEngine,
    FormulaicEngine,
    StructuralEngine,
    VocabularyEngine,
    ReadabilityEngine,
    SentimentEngine,
]


@pytest.mark.parametrize("engine_cls", ENGINES)
@pytest.mark.parametrize("text", [AI_TEXT, HUMAN_TEXT, "Too short."])
def test_engine_returns_valid_result(engine_cls, text):
    engine = engine_cls()
    result = engine.analyze(text)
    assert 0.0 <= result.score <= 1.0
    assert result.engine_name == engine.name
    assert engine.engine_type in {
        "neural",
        "statistical",
        "linguistic",
        "embedding",
        "classifier",
    }


@pytest.mark.parametrize("engine_cls", [LinguisticEngine, FormulaicEngine])
def test_stock_phrases_score_higher_than_plain_prose(engine_cls):
    engine = engine_cls()
    assert engine.analyze(AI_TEXT).score > engine.analyze(HUMAN_TEXT).score
