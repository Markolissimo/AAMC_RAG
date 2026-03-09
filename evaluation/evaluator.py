"""
Evaluation runner for the MCAT AI Tutor system.

Runs the full evaluation suite against all Q&A pairs and produces a
summary report (printed + saved as JSON/CSV).

Usage:
    python -m evaluation.evaluator
    python -m evaluation.evaluator --use-llm-judge
    python -m evaluation.evaluator --qa-id exp_001
"""

from __future__ import annotations

import argparse
import json
import os
import time
from dataclasses import asdict
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from loguru import logger

from evaluation.metrics import (
    AggregateScore,
    GenerationMetrics,
    MCQMetrics,
    RetrievalMetrics,
    aggregate_scores,
    compute_generation_metrics,
    compute_mcq_metrics,
    compute_retrieval_metrics,
    llm_judge,
)
from evaluation.qa_pairs import (
    EXPLANATION_QA_PAIRS,
    MCAT_GENERATION_PAIRS,
    QAPair,
    MCATQAPair,
)
from src.rag_pipeline import RAGPipeline

load_dotenv()

_RESULTS_DIR = Path(__file__).parent.parent / "data" / "eval_results"


# ===========================================================================
# Single-sample evaluators
# ===========================================================================

def evaluate_explanation(
    pipeline: RAGPipeline,
    pair: QAPair,
    use_llm_judge: bool = False,
    llm_client=None,
) -> dict:
    """Run one explanation Q&A pair through the pipeline and score it."""
    start = time.perf_counter()
    result = pipeline.explain(pair.question)
    elapsed = time.perf_counter() - start

    # Retrieval metrics
    ret_metrics = compute_retrieval_metrics(
        retrieved_chunks=result.sources,
        retrieval_keywords=pair.retrieval_keywords,
    )

    # Generation metrics
    gen_metrics = compute_generation_metrics(
        answer=result.answer,
        expected_sections=pair.expected_sections,
        expected_concepts=pair.expected_concepts,
        reference_answer=pair.reference_answer,
    )

    # Optional LLM judge
    if use_llm_judge and llm_client and pair.reference_answer:
        score, reason = llm_judge(
            generated=result.answer,
            reference=pair.reference_answer,
            llm_client=llm_client,
        )
        gen_metrics.llm_correctness = score
        gen_metrics.details["llm_judge_reason"] = reason

    agg = aggregate_scores(ret_metrics, gen_metrics)

    return {
        "id": pair.id,
        "topic": pair.topic,
        "question": pair.question,
        "difficulty": pair.difficulty,
        "latency_s": round(elapsed, 2),
        "hit_at_k": ret_metrics.hit_at_k,
        "mrr": round(ret_metrics.mrr, 3),
        "precision_at_k": round(ret_metrics.precision_at_k, 3),
        "keyword_coverage": round(ret_metrics.keyword_coverage, 3),
        "section_coverage": round(gen_metrics.section_coverage, 3),
        "concept_coverage": round(gen_metrics.concept_coverage, 3),
        "style_score": round(gen_metrics.style_score, 3),
        "answer_length_ok": gen_metrics.answer_length_ok,
        "llm_correctness": round(gen_metrics.llm_correctness, 3) if gen_metrics.llm_correctness is not None else None,
        "aggregate_retrieval": round(agg.retrieval, 3),
        "aggregate_generation": round(agg.generation, 3),
        "overall_score": round(agg.overall, 3),
        "answer_preview": result.answer[:200] + "…",
        "retrieval_details": ret_metrics.details,
        "generation_details": gen_metrics.details,
    }


def evaluate_mcq_generation(
    pipeline: RAGPipeline,
    pair: MCATQAPair,
) -> dict:
    """Run one MCQ generation pair through the pipeline and score it."""
    start = time.perf_counter()
    mcq = pipeline.generate_question(pair.topic)
    elapsed = time.perf_counter() - start

    mcq_metrics = compute_mcq_metrics(
        question_stem=mcq.question_stem,
        choices=mcq.choices,
        correct_answer=mcq.correct_answer,
        explanation=mcq.explanation,
        raw_output=mcq.raw_output,
        must_have_sections=pair.must_have_sections,
        correct_answer_must_mention=pair.correct_answer_must_mention,
        distractors_should_test=pair.distractors_should_test,
    )

    # Retrieval metrics for MCQ context
    ret_metrics = compute_retrieval_metrics(
        retrieved_chunks=mcq.sources,
        retrieval_keywords=pair.required_concepts,
    )

    return {
        "id": pair.id,
        "topic": pair.topic,
        "difficulty": pair.difficulty,
        "latency_s": round(elapsed, 2),
        "structure_ok": mcq_metrics.structure_ok,
        "correct_answer_valid": mcq_metrics.correct_answer_valid,
        "distractor_coverage": round(mcq_metrics.distractor_coverage, 3),
        "section_coverage": round(mcq_metrics.section_coverage, 3),
        "hit_at_k": ret_metrics.hit_at_k,
        "keyword_coverage": round(ret_metrics.keyword_coverage, 3),
        "question_preview": mcq.question_stem[:150] + "…" if len(mcq.question_stem) > 150 else mcq.question_stem,
        "correct_answer": mcq.correct_answer,
        "details": mcq_metrics.details,
    }


# ===========================================================================
# Full evaluation suite
# ===========================================================================

class Evaluator:
    def __init__(self, pipeline: RAGPipeline, use_llm_judge: bool = False):
        self._pipeline = pipeline
        self._use_llm_judge = use_llm_judge
        self._llm_client = None

        if use_llm_judge:
            from openai import OpenAI
            self._llm_client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

    def run_all(
        self,
        qa_id: str | None = None,
        save: bool = True,
    ) -> dict:
        """
        Run the full evaluation suite.

        Args:
            qa_id: if set, run only the pair with this id
            save: save results to data/eval_results/
        """
        exp_pairs = EXPLANATION_QA_PAIRS
        mcq_pairs = MCAT_GENERATION_PAIRS

        if qa_id:
            exp_pairs = [p for p in exp_pairs if p.id == qa_id]
            mcq_pairs = [p for p in mcq_pairs if p.id == qa_id]

        # --- Explanation evaluation ---
        exp_results: list[dict] = []
        for pair in exp_pairs:
            logger.info(f"Evaluating explanation: {pair.id}")
            try:
                r = evaluate_explanation(
                    self._pipeline, pair,
                    use_llm_judge=self._use_llm_judge,
                    llm_client=self._llm_client,
                )
                exp_results.append(r)
            except Exception as e:
                logger.error(f"Error on {pair.id}: {e}")
                exp_results.append({"id": pair.id, "error": str(e)})

        # --- MCQ evaluation ---
        mcq_results: list[dict] = []
        for pair in mcq_pairs:
            logger.info(f"Evaluating MCQ generation: {pair.id}")
            try:
                r = evaluate_mcq_generation(self._pipeline, pair)
                mcq_results.append(r)
            except Exception as e:
                logger.error(f"Error on {pair.id}: {e}")
                mcq_results.append({"id": pair.id, "error": str(e)})

        # --- Summary ---
        summary = self._compute_summary(exp_results, mcq_results)
        self._print_summary(summary, exp_results, mcq_results)

        results = {
            "explanation_results": exp_results,
            "mcq_results": mcq_results,
            "summary": summary,
        }

        if save:
            self._save_results(results)

        return results

    @staticmethod
    def _compute_summary(exp_results: list[dict], mcq_results: list[dict]) -> dict:
        valid_exp = [r for r in exp_results if "error" not in r]
        valid_mcq = [r for r in mcq_results if "error" not in r]

        def _avg(lst, key):
            vals = [r[key] for r in lst if r.get(key) is not None]
            return round(sum(vals) / len(vals), 3) if vals else None

        return {
            "explanation": {
                "n": len(valid_exp),
                "hit_at_k": _avg(valid_exp, "hit_at_k"),
                "avg_mrr": _avg(valid_exp, "mrr"),
                "avg_keyword_coverage": _avg(valid_exp, "keyword_coverage"),
                "avg_section_coverage": _avg(valid_exp, "section_coverage"),
                "avg_concept_coverage": _avg(valid_exp, "concept_coverage"),
                "avg_style_score": _avg(valid_exp, "style_score"),
                "avg_overall_score": _avg(valid_exp, "overall_score"),
                "avg_latency_s": _avg(valid_exp, "latency_s"),
            },
            "mcq_generation": {
                "n": len(valid_mcq),
                "structure_ok_rate": _avg(valid_mcq, "structure_ok"),
                "avg_distractor_coverage": _avg(valid_mcq, "distractor_coverage"),
                "avg_section_coverage": _avg(valid_mcq, "section_coverage"),
                "avg_keyword_coverage": _avg(valid_mcq, "keyword_coverage"),
                "avg_latency_s": _avg(valid_mcq, "latency_s"),
            },
        }

    @staticmethod
    def _print_summary(summary: dict, exp_results: list[dict], mcq_results: list[dict]) -> None:
        print("\n" + "=" * 60)
        print("MCAT AI TUTOR — EVALUATION SUMMARY")
        print("=" * 60)

        print("\n📘 EXPLANATION ENGINE")
        e = summary["explanation"]
        print(f"  Samples evaluated    : {e['n']}")
        print(f"  Hit@K (retrieval)    : {e['hit_at_k']}")
        print(f"  Avg MRR              : {e['avg_mrr']}")
        print(f"  Avg keyword coverage : {e['avg_keyword_coverage']}")
        print(f"  Avg section coverage : {e['avg_section_coverage']}")
        print(f"  Avg concept coverage : {e['avg_concept_coverage']}")
        print(f"  Avg style score      : {e['avg_style_score']}")
        print(f"  Avg overall score    : {e['avg_overall_score']}")
        print(f"  Avg latency (s)      : {e['avg_latency_s']}")

        print("\n❓ MCQ GENERATOR")
        m = summary["mcq_generation"]
        print(f"  Samples evaluated    : {m['n']}")
        print(f"  Structure OK rate    : {m['structure_ok_rate']}")
        print(f"  Avg distractor cov.  : {m['avg_distractor_coverage']}")
        print(f"  Avg section coverage : {m['avg_section_coverage']}")
        print(f"  Avg keyword coverage : {m['avg_keyword_coverage']}")
        print(f"  Avg latency (s)      : {m['avg_latency_s']}")
        print("=" * 60 + "\n")

    @staticmethod
    def _save_results(results: dict) -> None:
        _RESULTS_DIR.mkdir(parents=True, exist_ok=True)
        ts = int(time.time())

        json_path = _RESULTS_DIR / f"eval_{ts}.json"
        with open(json_path, "w") as f:
            json.dump(results, f, indent=2, default=str)
        logger.info(f"Results saved to {json_path}")

        # CSV for quick analysis
        if results["explanation_results"]:
            df_exp = pd.DataFrame([
                {k: v for k, v in r.items()
                 if not isinstance(v, dict)}
                for r in results["explanation_results"]
            ])
            df_exp.to_csv(_RESULTS_DIR / f"explanation_eval_{ts}.csv", index=False)

        if results["mcq_results"]:
            df_mcq = pd.DataFrame([
                {k: v for k, v in r.items()
                 if not isinstance(v, dict)}
                for r in results["mcq_results"]
            ])
            df_mcq.to_csv(_RESULTS_DIR / f"mcq_eval_{ts}.csv", index=False)


# ===========================================================================
# CLI entry point
# ===========================================================================

def main():
    parser = argparse.ArgumentParser(description="Run MCAT AI Tutor evaluation suite.")
    parser.add_argument("--use-llm-judge", action="store_true", help="Use LLM-as-judge for generation scoring")
    parser.add_argument("--qa-id", type=str, default=None, help="Run only the Q&A pair with this id")
    parser.add_argument("--no-save", action="store_true", help="Do not save results to disk")
    args = parser.parse_args()

    pipeline = RAGPipeline()
    pipeline.ingest()

    evaluator = Evaluator(pipeline, use_llm_judge=args.use_llm_judge)
    evaluator.run_all(qa_id=args.qa_id, save=not args.no_save)


if __name__ == "__main__":
    main()
