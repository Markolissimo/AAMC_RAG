"""
Evaluation metrics for the MCAT AI Tutor RAG system.

Metrics implemented:

RETRIEVAL METRICS
-----------------
1. hit_at_k         — is at least one relevant chunk in top-K results?
2. mrr              — Mean Reciprocal Rank (rank of first relevant chunk)
3. precision_at_k   — fraction of top-K chunks that are relevant
4. keyword_coverage — fraction of expected retrieval keywords found in context

GENERATION METRICS
------------------
5. section_coverage     — fraction of expected structural sections present
6. concept_coverage     — fraction of expected concepts found in answer
7. answer_length_ok     — answer is within acceptable length bounds
8. llm_correctness      — LLM-as-judge score (0-4) comparing to reference answer
9. style_score          — composite (section_coverage + concept_coverage)

MCAT QUESTION METRICS
----------------------
10. mcq_structure_ok    — all required sections present and choices A-D exist
11. correct_answer_valid — correct answer is one of A/B/C/D
12. distractor_coverage — expected misconception concepts in answer choices
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Sequence


# ===========================================================================
# Data structures
# ===========================================================================

@dataclass
class RetrievalMetrics:
    hit_at_k: bool
    mrr: float
    precision_at_k: float
    keyword_coverage: float
    details: dict = field(default_factory=dict)


@dataclass
class GenerationMetrics:
    section_coverage: float           # 0.0 – 1.0
    concept_coverage: float           # 0.0 – 1.0
    style_score: float                # average of above two
    answer_length_ok: bool
    llm_correctness: float | None     # 0.0 – 1.0 (None if not computed)
    details: dict = field(default_factory=dict)


@dataclass
class MCQMetrics:
    structure_ok: bool
    correct_answer_valid: bool
    distractor_coverage: float        # 0.0 – 1.0
    section_coverage: float           # 0.0 – 1.0
    details: dict = field(default_factory=dict)


# ===========================================================================
# Retrieval metrics
# ===========================================================================

def _text_contains_any(text: str, keywords: Sequence[str]) -> bool:
    text_lower = text.lower()
    return any(kw.lower() in text_lower for kw in keywords)


def compute_retrieval_metrics(
    retrieved_chunks: list[dict],
    retrieval_keywords: Sequence[str],
    top_k: int = 4,
) -> RetrievalMetrics:
    """
    Args:
        retrieved_chunks: list of {"text": ..., "metadata": ..., "score": ...}
        retrieval_keywords: ground-truth keywords expected to be in chunks
        top_k: number of chunks returned by the retriever
    """
    # Relevance: a chunk is "relevant" if it contains any expected keyword
    relevances = [
        _text_contains_any(c["text"], retrieval_keywords)
        for c in retrieved_chunks[:top_k]
    ]

    hit = any(relevances)

    # MRR: reciprocal rank of the first relevant result
    mrr = 0.0
    for rank, is_relevant in enumerate(relevances, start=1):
        if is_relevant:
            mrr = 1.0 / rank
            break

    precision = sum(relevances) / len(relevances) if relevances else 0.0

    # Keyword coverage: fraction of expected keywords found anywhere in retrieved context
    all_context = " ".join(c["text"] for c in retrieved_chunks[:top_k])
    keywords_found = [
        kw for kw in retrieval_keywords
        if kw.lower() in all_context.lower()
    ]
    kw_coverage = len(keywords_found) / len(retrieval_keywords) if retrieval_keywords else 0.0

    return RetrievalMetrics(
        hit_at_k=hit,
        mrr=mrr,
        precision_at_k=precision,
        keyword_coverage=kw_coverage,
        details={
            "relevances_per_rank": relevances,
            "keywords_found": keywords_found,
            "keywords_missing": [kw for kw in retrieval_keywords if kw not in keywords_found],
        },
    )


# ===========================================================================
# Generation metrics
# ===========================================================================

_MIN_ANSWER_WORDS = 60
_MAX_ANSWER_WORDS = 800


def compute_generation_metrics(
    answer: str,
    expected_sections: Sequence[str],
    expected_concepts: Sequence[str],
    reference_answer: str | None = None,
) -> GenerationMetrics:
    """
    Args:
        answer: the generated explanation text
        expected_sections: list of section headers that should appear (e.g. "Toolkit")
        expected_concepts: list of concept keywords that should appear
        reference_answer: gold-standard short answer (used only if llm_judge is called separately)
    """
    # Section coverage
    sections_found = [
        s for s in expected_sections
        if re.search(re.escape(s), answer, re.IGNORECASE)
    ]
    section_cov = len(sections_found) / len(expected_sections) if expected_sections else 1.0

    # Concept coverage
    concepts_found = [
        c for c in expected_concepts
        if c.lower() in answer.lower()
    ]
    concept_cov = len(concepts_found) / len(expected_concepts) if expected_concepts else 1.0

    # Length check
    word_count = len(answer.split())
    length_ok = _MIN_ANSWER_WORDS <= word_count <= _MAX_ANSWER_WORDS

    return GenerationMetrics(
        section_coverage=section_cov,
        concept_coverage=concept_cov,
        style_score=(section_cov + concept_cov) / 2,
        answer_length_ok=length_ok,
        llm_correctness=None,  # populated separately by LLMJudge
        details={
            "sections_found": sections_found,
            "sections_missing": [s for s in expected_sections if s not in sections_found],
            "concepts_found": concepts_found,
            "concepts_missing": [c for c in expected_concepts if c not in concepts_found],
            "word_count": word_count,
        },
    )


# ===========================================================================
# MCQ metrics
# ===========================================================================

def compute_mcq_metrics(
    question_stem: str,
    choices: dict[str, str],
    correct_answer: str,
    explanation: str,
    raw_output: str,
    must_have_sections: Sequence[str],
    correct_answer_must_mention: Sequence[str],
    distractors_should_test: Sequence[str],
) -> MCQMetrics:
    # Structure: all 4 choices present
    has_all_choices = all(k in choices and choices[k].strip() for k in ["A", "B", "C", "D"])

    # Required sections present
    sections_found = [
        s for s in must_have_sections
        if re.search(re.escape(s), raw_output, re.IGNORECASE)
    ]
    section_cov = len(sections_found) / len(must_have_sections) if must_have_sections else 1.0

    # Correct answer is valid letter
    correct_valid = correct_answer.strip().upper() in {"A", "B", "C", "D"}

    # Correct answer rationale mentions expected concepts
    rationale_text = explanation + " " + choices.get(correct_answer.upper(), "")
    mentions = [kw for kw in correct_answer_must_mention if kw.lower() in rationale_text.lower()]

    # Distractor coverage: do wrong answers probe expected misconceptions?
    distractor_texts = " ".join(
        v for k, v in choices.items() if k != correct_answer.upper()
    ) + " " + explanation
    distractor_hits = [kw for kw in distractors_should_test if kw.lower() in distractor_texts.lower()]
    distractor_cov = len(distractor_hits) / len(distractors_should_test) if distractors_should_test else 1.0

    return MCQMetrics(
        structure_ok=has_all_choices and correct_valid,
        correct_answer_valid=correct_valid,
        distractor_coverage=distractor_cov,
        section_coverage=section_cov,
        details={
            "choices_present": list(choices.keys()),
            "sections_found": sections_found,
            "correct_mentions": mentions,
            "correct_mentions_missing": [kw for kw in correct_answer_must_mention if kw not in mentions],
            "distractor_hits": distractor_hits,
        },
    )


# ===========================================================================
# LLM-as-judge
# ===========================================================================

LLM_JUDGE_PROMPT = """\
You are a strict expert evaluator for an MCAT AI tutoring system.

Score the GENERATED ANSWER against the REFERENCE ANSWER on a scale of 0 to 4:

4 = Factually correct, covers all key concepts, clear and well-structured.
3 = Mostly correct, minor omissions or small imprecision.
2 = Partially correct, missing important concepts or has one factual error.
1 = Mostly incorrect, significant factual errors or major omissions.
0 = Completely wrong or irrelevant.

Reference Answer:
{reference}

Generated Answer:
{generated}

Respond with ONLY a JSON object: {{"score": <0-4>, "reason": "<one sentence>"}}
"""


def llm_judge(
    generated: str,
    reference: str,
    llm_client,          # openai.OpenAI instance
    model: str = "gpt-5-nano",
) -> tuple[float, str]:
    """
    Returns (normalized_score: 0.0-1.0, reason: str).
    Normalize: raw_score / 4.
    """
    import json as _json

    prompt = LLM_JUDGE_PROMPT.format(reference=reference, generated=generated)
    response = llm_client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=1,
        response_format={"type": "json_object"},
    )
    raw = response.choices[0].message.content.strip()

    try:
        data = _json.loads(raw)
        score = float(data.get("score", 0))
        reason = data.get("reason", "")
        return min(max(score / 4.0, 0.0), 1.0), reason
    except Exception:
        return 0.0, f"Parse error: {raw[:100]}"


# ===========================================================================
# Aggregate score
# ===========================================================================

@dataclass
class AggregateScore:
    retrieval: float      # 0-1
    generation: float     # 0-1
    overall: float        # weighted average


def aggregate_scores(
    ret: RetrievalMetrics,
    gen: GenerationMetrics,
    weights: tuple[float, float] = (0.4, 0.6),
) -> AggregateScore:
    ret_score = (ret.hit_at_k * 0.4 + ret.mrr * 0.3 + ret.keyword_coverage * 0.3)
    gen_score = gen.style_score if gen.llm_correctness is None else (
        gen.style_score * 0.4 + gen.llm_correctness * 0.6
    )
    overall = weights[0] * ret_score + weights[1] * gen_score
    return AggregateScore(retrieval=ret_score, generation=gen_score, overall=overall)
