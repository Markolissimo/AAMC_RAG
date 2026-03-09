"""
Tests for the generation layer (prompts, explanation engine, question generator).

All tests use mocked LLM calls — no real API calls are made.
"""

from __future__ import annotations

import math
import random
from typing import Sequence
from unittest.mock import MagicMock, patch

import pytest

from src.generation.prompts import (
    ExplanationMode,
    EXPLANATION_USER_TEMPLATE,
    QUESTION_GENERATOR_SYSTEM,
    build_system_prompt,
)
from src.generation.explanation_engine import ExplanationEngine, ExplanationResult
from src.generation.question_generator import QuestionGenerator, MCATQuestion
from src.retrieval.embeddings import BaseEmbedder
from src.retrieval.vector_store import VectorStore
from src.ingestion.chunker import TextChunk


# ===========================================================================
# Mock helpers
# ===========================================================================

class _MockEmbedder(BaseEmbedder):
    def embed_documents(self, texts: Sequence[str]) -> list[list[float]]:
        return [self._vec(t) for t in texts]

    def embed_query(self, text: str) -> list[float]:
        return self._vec(text)

    @property
    def dimension(self) -> int:
        return 8

    def _vec(self, text: str) -> list[float]:
        rng = random.Random(hash(text) % (2**32))
        v = [rng.gauss(0, 1) for _ in range(8)]
        n = math.sqrt(sum(x**2 for x in v)) or 1.0
        return [x / n for x in v]


_SAMPLE_EXPLANATION = """\
**Toolkit**
- P + (1/2)*rho*v^2 + rho*g*h = constant
- A1*v1 = A2*v2 (continuity equation)
- Bernoulli's principle

**Think It Through**
When fluid enters a narrowing pipe it speeds up. By Bernoulli, faster flow means
lower pressure. So pressure drops in the narrow section.

**Analogy**
Think of cars on a highway merging into one lane — they all speed up in the bottleneck.

**MCAT Trap**
Students think faster fluid = higher pressure. Wrong! Faster = lower pressure.

**Memory Rule**
Narrow pipe, fast flow, low pressure. Always.
"""

_SAMPLE_MCQ_RAW = """\
**Question**
A fluid flows through a pipe that narrows from diameter D to D/2. What happens to the
fluid pressure in the narrow section compared to the wide section?

**Answer Choices**
A) Pressure doubles
B) Pressure decreases
C) Pressure stays the same
D) Pressure quadruples

**Correct Answer**
B) Because velocity increases (continuity), Bernoulli requires pressure to decrease.

**Explanation**
**Toolkit**
- A1*v1 = A2*v2
- P + (1/2)*rho*v^2 = constant

**Think It Through**
Area decreases by factor 4, so velocity increases by 4. By Bernoulli, higher
velocity means lower pressure.

**Analogy**
Garden hose with thumb over opening — water speeds up, but doesn't push harder sideways.

**MCAT Trap**
Confusing flow speed with pressure. High speed = low pressure (Bernoulli).

**Memory Rule**
Narrow → fast → low pressure. Every time.
"""


@pytest.fixture
def mock_vector_store():
    chunks = [
        TextChunk(
            text="Bernoulli's equation: P + (1/2)*rho*v^2 + rho*g*h = constant. "
                 "Faster flow means lower pressure.",
            metadata={"source": "princeton", "page": 10, "chunk_index": 0, "section": "Bernoulli"},
        ),
        TextChunk(
            text="Continuity equation: A1*v1 = A2*v2. Flow rate Q is conserved.",
            metadata={"source": "examkrackers", "page": 5, "chunk_index": 0, "section": "Continuity"},
        ),
    ]
    store = VectorStore(embedder=_MockEmbedder())
    store.build_from_chunks(chunks)
    return store


# ===========================================================================
# Prompts
# ===========================================================================

class TestPrompts:
    def test_system_prompt_contains_toolkit(self):
        prompt = build_system_prompt(ExplanationMode.STANDARD)
        assert "Toolkit" in prompt

    def test_system_prompt_contains_all_sections(self):
        prompt = build_system_prompt(ExplanationMode.STANDARD)
        for section in ["Toolkit", "Think It Through", "Analogy", "MCAT Trap", "Memory Rule"]:
            assert section in prompt, f"Missing section: {section}"

    def test_simpler_mode_adds_instruction(self):
        prompt = build_system_prompt(ExplanationMode.SIMPLER)
        assert "SIMPLER" in prompt.upper() or "simpler" in prompt.lower()

    def test_tighter_mode_adds_instruction(self):
        prompt = build_system_prompt(ExplanationMode.TIGHTER)
        assert "TIGHTER" in prompt.upper() or "concise" in prompt.lower()

    def test_analogy_mode_adds_instruction(self):
        prompt = build_system_prompt(ExplanationMode.ANALOGY)
        assert "ANALOGY" in prompt.upper()

    def test_explanation_user_template_interpolation(self):
        formatted = EXPLANATION_USER_TEMPLATE.format(
            context="some context",
            question="Explain Bernoulli.",
        )
        assert "some context" in formatted
        assert "Explain Bernoulli." in formatted

    def test_all_explanation_modes_defined(self):
        for mode in ExplanationMode:
            prompt = build_system_prompt(mode)
            assert isinstance(prompt, str)
            assert len(prompt) > 100


# ===========================================================================
# ExplanationEngine
# ===========================================================================

class TestExplanationEngine:
    @pytest.fixture
    def engine(self, mock_vector_store):
        with patch("src.generation.explanation_engine.ChatOpenAI") as MockLLM:
            instance = MagicMock()
            instance.invoke.return_value = MagicMock(content=_SAMPLE_EXPLANATION)
            MockLLM.return_value = instance

            import os
            os.environ.setdefault("OPENAI_API_KEY", "test-key")
            eng = ExplanationEngine(
                vector_store=mock_vector_store,
                model="gpt-4o-mini",
            )
            eng._llm = instance
            return eng

    def test_returns_explanation_result(self, engine):
        result = engine.explain("Explain Bernoulli's principle")
        assert isinstance(result, ExplanationResult)

    def test_result_has_answer(self, engine):
        result = engine.explain("Explain Bernoulli's principle")
        assert len(result.answer) > 0

    def test_result_has_sources(self, engine):
        result = engine.explain("Explain Bernoulli's principle")
        assert isinstance(result.sources, list)

    def test_result_answer_contains_toolkit(self, engine):
        result = engine.explain("Explain Bernoulli's principle")
        assert "Toolkit" in result.answer

    def test_result_stores_mode(self, engine):
        result = engine.explain("Explain Bernoulli's principle", mode=ExplanationMode.SIMPLER)
        assert result.mode == ExplanationMode.SIMPLER

    def test_detect_mode_simpler(self, engine):
        _, mode = engine.detect_mode("Explain in simpler terms")
        assert mode == ExplanationMode.SIMPLER

    def test_detect_mode_analogy(self, engine):
        _, mode = engine.detect_mode("Give another analogy for Bernoulli's principle")
        assert mode == ExplanationMode.ANALOGY

    def test_detect_mode_tighter(self, engine):
        _, mode = engine.detect_mode("Give a tighter explanation")
        assert mode == ExplanationMode.TIGHTER

    def test_detect_mode_another_way(self, engine):
        _, mode = engine.detect_mode("Explain another way")
        assert mode == ExplanationMode.ANOTHER_WAY

    def test_detect_mode_standard_default(self, engine):
        _, mode = engine.detect_mode("Explain Bernoulli's principle")
        assert mode == ExplanationMode.STANDARD


# ===========================================================================
# QuestionGenerator
# ===========================================================================

class TestQuestionGenerator:
    @pytest.fixture
    def generator(self, mock_vector_store):
        with patch("src.generation.question_generator.ChatOpenAI") as MockLLM:
            instance = MagicMock()
            instance.invoke.return_value = MagicMock(content=_SAMPLE_MCQ_RAW)
            MockLLM.return_value = instance

            import os
            os.environ.setdefault("OPENAI_API_KEY", "test-key")
            gen = QuestionGenerator(
                vector_store=mock_vector_store,
                model="gpt-4o-mini",
            )
            gen._llm = instance
            return gen

    def test_returns_mcat_question(self, generator):
        q = generator.generate("Bernoulli's principle")
        assert isinstance(q, MCATQuestion)

    def test_question_stem_not_empty(self, generator):
        q = generator.generate("Bernoulli's principle")
        assert len(q.question_stem) > 0

    def test_four_choices(self, generator):
        q = generator.generate("Bernoulli's principle")
        assert len(q.choices) == 4
        for letter in ["A", "B", "C", "D"]:
            assert letter in q.choices

    def test_correct_answer_valid_letter(self, generator):
        q = generator.generate("Bernoulli's principle")
        assert q.correct_answer.upper() in {"A", "B", "C", "D"}

    def test_explanation_not_empty(self, generator):
        q = generator.generate("Bernoulli's principle")
        assert len(q.explanation) > 0

    def test_topic_stored(self, generator):
        q = generator.generate("buoyancy")
        assert q.topic == "buoyancy"

    def test_sources_list(self, generator):
        q = generator.generate("Bernoulli's principle")
        assert isinstance(q.sources, list)

    def test_parse_choices_all_four(self, generator):
        """Unit test the internal _parse_choices method."""
        block = "A) Pressure doubles\nB) Pressure decreases\nC) Same\nD) Triples"
        choices = QuestionGenerator._parse_choices(block)
        assert choices == {
            "A": "Pressure doubles",
            "B": "Pressure decreases",
            "C": "Same",
            "D": "Triples",
        }

    def test_parse_correct_answer(self, generator):
        letter, rationale = QuestionGenerator._parse_correct("B) Because velocity increases")
        assert letter == "B"
        assert "velocity" in rationale
