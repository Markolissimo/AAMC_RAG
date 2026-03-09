"""
Explanation Engine — Task 1.

Given a student question + explanation mode, retrieves relevant passages and
generates a tutor-style explanation via the LLM.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from loguru import logger

from src.generation.prompts import (
    ExplanationMode,
    EXPLANATION_USER_TEMPLATE,
    build_system_prompt,
)
from src.retrieval.vector_store import VectorStore


@dataclass
class ExplanationResult:
    question: str
    mode: ExplanationMode
    answer: str
    sources: list[dict]   # list of {"text": ..., "metadata": ..., "score": ...}
    model: str


class ExplanationEngine:
    """
    Orchestrates retrieval + generation for explanation requests.

    Usage:
        engine = ExplanationEngine(vector_store)
        result = engine.explain("Explain Bernoulli's principle", mode=ExplanationMode.SIMPLER)
        print(result.answer)
    """

    def __init__(
        self,
        vector_store: VectorStore,
        model: str | None = None,
        top_k: int = 4,
        temperature: float = 0.4,
    ):
        self._store = vector_store
        self._model_name = model or os.getenv("LLM_MODEL", "gpt-4o-mini")
        self._top_k = top_k
        self._llm = ChatOpenAI(
            model=self._model_name,
            temperature=temperature,
            api_key=os.environ["OPENAI_API_KEY"],
        )

    def explain(
        self,
        question: str,
        mode: ExplanationMode = ExplanationMode.STANDARD,
    ) -> ExplanationResult:
        # 1. Retrieve relevant chunks
        sources = self._store.search(question, top_k=self._top_k)
        context = self._format_context(sources)

        # 2. Build messages
        system_msg = SystemMessage(content=build_system_prompt(mode))
        user_content = EXPLANATION_USER_TEMPLATE.format(
            context=context,
            question=question,
        )
        human_msg = HumanMessage(content=user_content)

        logger.info(
            f"Generating explanation | mode={mode.value} | model={self._model_name}"
        )

        # 3. Call LLM
        response = self._llm.invoke([system_msg, human_msg])
        answer = response.content.strip()

        return ExplanationResult(
            question=question,
            mode=mode,
            answer=answer,
            sources=sources,
            model=self._model_name,
        )

    @staticmethod
    def _format_context(sources: list[dict]) -> str:
        """Format retrieved chunks into a readable context block."""
        parts: list[str] = []
        for i, src in enumerate(sources, 1):
            meta = src["metadata"]
            source_label = f"{meta.get('source', 'unknown')}, p.{meta.get('page', '?')}"
            parts.append(f"[{i}] ({source_label})\n{src['text']}")
        return "\n\n".join(parts)

    def detect_mode(self, raw_question: str) -> tuple[str, ExplanationMode]:
        """
        Parse natural-language phrasing to detect the requested mode.

        Returns (clean_question, mode).
        """
        q = raw_question.strip().lower()

        if any(kw in q for kw in ["simpler", "simple", "easier", "eli5"]):
            return raw_question, ExplanationMode.SIMPLER
        if any(kw in q for kw in ["tight", "brief", "concise", "short"]):
            return raw_question, ExplanationMode.TIGHTER
        if any(kw in q for kw in ["analogy", "another analogy", "different analogy"]):
            return raw_question, ExplanationMode.ANALOGY
        if any(kw in q for kw in ["another way", "different way", "reframe"]):
            return raw_question, ExplanationMode.ANOTHER_WAY

        return raw_question, ExplanationMode.STANDARD
