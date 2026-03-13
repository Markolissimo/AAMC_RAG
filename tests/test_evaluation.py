"""
Tests for the evaluation layer (metrics + Q&A pairs).

All tests are purely local — no API calls, no pipeline needed.
"""

from __future__ import annotations

import pytest

from evaluation.metrics import (
    AggregateScore,
    GenerationMetrics,
    MCQMetrics,
    RetrievalMetrics,
    aggregate_scores,
    compute_generation_metrics,
    compute_mcq_metrics,
    compute_retrieval_metrics,
)
from evaluation.qa_pairs import (
    EXPLANATION_QA_PAIRS,
    MCAT_GENERATION_PAIRS,
    TUTOR_SECTIONS,
    MCAT_Q_SECTIONS,
    QAPair,
    MCATQAPair,
    ALL_EXPLANATION_QUESTIONS,
    ALL_MCQ_TOPICS,
    ID_TO_EXPLANATION_QA,
    ID_TO_MCQ_PAIR,
)


# ===========================================================================
# Q&A pairs dataset integrity
# ===========================================================================

class TestQAPairsDataset:
    def test_explanation_pairs_not_empty(self):
        assert len(EXPLANATION_QA_PAIRS) >= 10

    def test_mcat_pairs_not_empty(self):
        assert len(MCAT_GENERATION_PAIRS) >= 5

    def test_all_explanation_ids_unique(self):
        ids = [p.id for p in EXPLANATION_QA_PAIRS]
        assert len(ids) == len(set(ids))

    def test_all_mcat_ids_unique(self):
        ids = [p.id for p in MCAT_GENERATION_PAIRS]
        assert len(ids) == len(set(ids))

    def test_explanation_pairs_have_required_fields(self):
        for pair in EXPLANATION_QA_PAIRS:
            assert pair.id, f"Missing id"
            assert pair.question, f"Missing question in {pair.id}"
            assert pair.expected_concepts, f"Missing expected_concepts in {pair.id}"
            assert pair.reference_answer, f"Missing reference_answer in {pair.id}"
            assert pair.retrieval_keywords, f"Missing retrieval_keywords in {pair.id}"

    def test_mcat_pairs_have_required_fields(self):
        for pair in MCAT_GENERATION_PAIRS:
            assert pair.id
            assert pair.topic
            assert pair.required_concepts
            assert pair.must_have_sections
            assert pair.correct_answer_must_mention

    def test_explanation_sections_subset_of_tutor_sections(self):
        for pair in EXPLANATION_QA_PAIRS:
            for s in pair.expected_sections:
                assert s in TUTOR_SECTIONS or s in ["Another analogy"], \
                    f"Unexpected section {s!r} in {pair.id}"

    def test_mcat_sections_contain_required(self):
        for pair in MCAT_GENERATION_PAIRS:
            for s in ["Question", "Answer Choices", "Correct Answer", "Explanation"]:
                assert s in pair.must_have_sections, \
                    f"Missing {s!r} in {pair.id}.must_have_sections"

    def test_id_lookup_works(self):
        assert "exp_001" in ID_TO_EXPLANATION_QA
        assert "mcq_001" in ID_TO_MCQ_PAIR

    def test_all_questions_list_matches_pairs(self):
        assert len(ALL_EXPLANATION_QUESTIONS) == len(EXPLANATION_QA_PAIRS)

    def test_all_topics_list_matches_pairs(self):
        assert len(ALL_MCQ_TOPICS) == len(MCAT_GENERATION_PAIRS)

    def test_difficulty_values_valid(self):
        valid = {"easy", "medium", "hard"}
        for pair in EXPLANATION_QA_PAIRS:
            assert pair.difficulty in valid, f"Invalid difficulty {pair.difficulty!r} in {pair.id}"


# ===========================================================================
# compute_retrieval_metrics
# ===========================================================================

_GOOD_CHUNKS = [
    {"text": "Bernoulli's principle: faster fluid has lower pressure.", "metadata": {}, "score": 0.1},
    {"text": "The continuity equation A1*v1 = A2*v2.", "metadata": {}, "score": 0.2},
    {"text": "Archimedes principle: buoyant force = weight of displaced fluid.", "metadata": {}, "score": 0.3},
]

_BAD_CHUNKS = [
    {"text": "Totally unrelated content about geology.", "metadata": {}, "score": 0.5},
    {"text": "Nothing useful here.", "metadata": {}, "score": 0.6},
]


class TestRetrievalMetrics:
    def test_hit_at_k_true_when_keyword_present(self):
        ret = compute_retrieval_metrics(_GOOD_CHUNKS, ["Bernoulli", "pressure"])
        assert ret.hit_at_k is True

    def test_hit_at_k_false_when_keyword_absent(self):
        ret = compute_retrieval_metrics(_BAD_CHUNKS, ["Bernoulli", "pressure"])
        assert ret.hit_at_k is False

    def test_mrr_is_1_when_first_chunk_relevant(self):
        ret = compute_retrieval_metrics(_GOOD_CHUNKS, ["Bernoulli"])
        assert ret.mrr == pytest.approx(1.0)

    def test_mrr_is_0_when_no_relevant_chunk(self):
        ret = compute_retrieval_metrics(_BAD_CHUNKS, ["Bernoulli"])
        assert ret.mrr == pytest.approx(0.0)

    def test_mrr_fractional_when_second_chunk_relevant(self):
        chunks = [
            {"text": "unrelated", "metadata": {}, "score": 0.1},
            {"text": "Bernoulli pressure velocity", "metadata": {}, "score": 0.2},
        ]
        ret = compute_retrieval_metrics(chunks, ["Bernoulli"])
        assert ret.mrr == pytest.approx(0.5)

    def test_precision_at_k_all_relevant(self):
        ret = compute_retrieval_metrics(
            [{"text": "Bernoulli velocity pressure", "metadata": {}, "score": 0.1}] * 3,
            ["Bernoulli"],
            top_k=3,
        )
        assert ret.precision_at_k == pytest.approx(1.0)

    def test_precision_at_k_none_relevant(self):
        ret = compute_retrieval_metrics(_BAD_CHUNKS, ["Bernoulli"], top_k=2)
        assert ret.precision_at_k == pytest.approx(0.0)

    def test_keyword_coverage_full(self):
        ret = compute_retrieval_metrics(
            [{"text": "Bernoulli pressure velocity fluid", "metadata": {}, "score": 0.1}],
            ["Bernoulli", "pressure", "velocity"],
        )
        assert ret.keyword_coverage == pytest.approx(1.0)

    def test_keyword_coverage_partial(self):
        ret = compute_retrieval_metrics(
            [{"text": "Bernoulli is discussed here", "metadata": {}, "score": 0.1}],
            ["Bernoulli", "pressure", "viscosity"],
        )
        assert ret.keyword_coverage == pytest.approx(1 / 3)

    def test_empty_keywords_coverage(self):
        ret = compute_retrieval_metrics(_GOOD_CHUNKS, [])
        assert ret.keyword_coverage == pytest.approx(0.0)

    def test_details_contains_keywords_found(self):
        ret = compute_retrieval_metrics(
            [{"text": "Bernoulli pressure", "metadata": {}, "score": 0.1}],
            ["Bernoulli", "pressure"],
        )
        assert "keywords_found" in ret.details
        assert set(ret.details["keywords_found"]) == {"Bernoulli", "pressure"}


# ===========================================================================
# compute_generation_metrics
# ===========================================================================

_GOOD_ANSWER = """\
**Toolkit**
P + (1/2)*rho*v^2 + rho*g*h = constant
A1*v1 = A2*v2

**Think It Through**
When the pipe narrows, velocity increases. By Bernoulli, pressure decreases.

**Analogy**
Think of a garden hose — put your thumb over the end and water speeds up.

**MCAT Trap**
Students think faster flow = higher pressure. Wrong! Faster = LOWER pressure.

**Memory Rule**
Narrow pipe: faster flow, lower pressure.
"""

_EMPTY_ANSWER = "I don't know."


class TestGenerationMetrics:
    def test_perfect_section_coverage(self):
        gen = compute_generation_metrics(
            _GOOD_ANSWER,
            expected_sections=["Toolkit", "Think It Through", "Analogy", "MCAT Trap", "Memory Rule"],
            expected_concepts=["Bernoulli"],
        )
        assert gen.section_coverage == pytest.approx(1.0)

    def test_zero_section_coverage(self):
        gen = compute_generation_metrics(
            _EMPTY_ANSWER,
            expected_sections=["Toolkit", "Analogy", "MCAT Trap"],
            expected_concepts=[],
        )
        assert gen.section_coverage == pytest.approx(0.0)

    def test_partial_section_coverage(self):
        answer = "**Toolkit**\nsome equations\n**Analogy**\nsome analogy"
        gen = compute_generation_metrics(
            answer,
            expected_sections=["Toolkit", "Analogy", "MCAT Trap"],
            expected_concepts=[],
        )
        assert gen.section_coverage == pytest.approx(2 / 3)

    def test_concept_coverage_full(self):
        gen = compute_generation_metrics(
            "The Bernoulli equation with pressure and velocity is key.",
            expected_sections=[],
            expected_concepts=["Bernoulli", "pressure", "velocity"],
        )
        assert gen.concept_coverage == pytest.approx(1.0)

    def test_concept_coverage_zero(self):
        gen = compute_generation_metrics(
            "This answer is about unrelated things.",
            expected_sections=[],
            expected_concepts=["Bernoulli", "pressure"],
        )
        assert gen.concept_coverage == pytest.approx(0.0)

    def test_style_score_is_average(self):
        gen = compute_generation_metrics(
            _GOOD_ANSWER,
            expected_sections=["Toolkit", "Analogy"],
            expected_concepts=["rho*v^2", "pressure"],
        )
        expected = (gen.section_coverage + gen.concept_coverage) / 2
        assert gen.style_score == pytest.approx(expected)

    def test_answer_length_ok_passes(self):
        long_answer = " ".join(["word"] * 150)
        gen = compute_generation_metrics(long_answer, [], [])
        assert gen.answer_length_ok is True

    def test_answer_length_too_short(self):
        gen = compute_generation_metrics("Too short.", [], [])
        assert gen.answer_length_ok is False

    def test_llm_correctness_none_by_default(self):
        gen = compute_generation_metrics(_GOOD_ANSWER, [], [])
        assert gen.llm_correctness is None

    def test_details_contains_missing_sections(self):
        gen = compute_generation_metrics(
            "Just some text",
            expected_sections=["Toolkit", "Analogy"],
            expected_concepts=[],
        )
        assert "sections_missing" in gen.details
        assert "Toolkit" in gen.details["sections_missing"]


# ===========================================================================
# compute_mcq_metrics
# ===========================================================================

_GOOD_MCQ_CHOICES = {"A": "Pressure doubles", "B": "Pressure decreases", "C": "No change", "D": "Pressure quadruples"}
_GOOD_MCQ_EXPLANATION = "By Bernoulli, velocity increases so pressure decreases. Fluid density matters too."


class TestMCQMetrics:
    def _base_mcq_metrics(self, **overrides):
        defaults = dict(
            question_stem="A fluid flows through a narrow pipe. What happens to pressure?",
            choices=_GOOD_MCQ_CHOICES,
            correct_answer="B",
            explanation=_GOOD_MCQ_EXPLANATION,
            raw_output="**Question**\n...\n**Answer Choices**\n...\n**Correct Answer**\n...\n**Explanation**\n...",
            must_have_sections=["Question", "Answer Choices", "Correct Answer", "Explanation"],
            correct_answer_must_mention=["pressure decreases", "velocity"],
            distractors_should_test=["pressure doubles"],
        )
        defaults.update(overrides)
        return compute_mcq_metrics(**defaults)

    def test_structure_ok_with_all_choices(self):
        m = self._base_mcq_metrics()
        assert m.structure_ok is True

    def test_structure_fails_missing_choice(self):
        bad_choices = {"A": "X", "B": "Y", "C": "Z"}  # missing D
        m = self._base_mcq_metrics(choices=bad_choices)
        assert m.structure_ok is False

    def test_correct_answer_valid(self):
        m = self._base_mcq_metrics(correct_answer="B")
        assert m.correct_answer_valid is True

    def test_correct_answer_invalid(self):
        m = self._base_mcq_metrics(correct_answer="E")
        assert m.correct_answer_valid is False

    def test_distractor_coverage_positive(self):
        m = self._base_mcq_metrics()
        assert m.distractor_coverage > 0.0

    def test_section_coverage_with_all_sections(self):
        m = self._base_mcq_metrics()
        assert m.section_coverage == pytest.approx(1.0)


# ===========================================================================
# aggregate_scores
# ===========================================================================

class TestAggregateScores:
    def _make_ret(self, hit=True, mrr=1.0, precision=1.0, kw_cov=1.0):
        return RetrievalMetrics(
            hit_at_k=hit, mrr=mrr, precision_at_k=precision, keyword_coverage=kw_cov
        )

    def _make_gen(self, sec_cov=1.0, con_cov=1.0, length_ok=True, llm=None):
        gen = GenerationMetrics(
            section_coverage=sec_cov,
            concept_coverage=con_cov,
            style_score=(sec_cov + con_cov) / 2,
            answer_length_ok=length_ok,
            llm_correctness=llm,
        )
        return gen

    def test_perfect_scores(self):
        agg = aggregate_scores(self._make_ret(), self._make_gen())
        assert agg.overall == pytest.approx(1.0, abs=0.05)

    def test_zero_scores(self):
        agg = aggregate_scores(
            self._make_ret(hit=False, mrr=0.0, precision=0.0, kw_cov=0.0),
            self._make_gen(sec_cov=0.0, con_cov=0.0),
        )
        assert agg.overall == pytest.approx(0.0)

    def test_returns_aggregate_score_type(self):
        agg = aggregate_scores(self._make_ret(), self._make_gen())
        assert isinstance(agg, AggregateScore)

    def test_overall_between_0_and_1(self):
        agg = aggregate_scores(
            self._make_ret(hit=True, mrr=0.5, precision=0.5, kw_cov=0.5),
            self._make_gen(sec_cov=0.7, con_cov=0.8),
        )
        assert 0.0 <= agg.overall <= 1.0

    def test_llm_judge_increases_generation_score(self):
        agg_no_llm  = aggregate_scores(self._make_ret(), self._make_gen(sec_cov=0.5, con_cov=0.5))
        agg_with_llm = aggregate_scores(self._make_ret(), self._make_gen(sec_cov=0.5, con_cov=0.5, llm=1.0))
        assert agg_with_llm.generation > agg_no_llm.generation
