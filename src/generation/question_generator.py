"""
MCAT Question Generator — Task 2.

Generates a full MCAT-style multiple-choice question with tutor-style explanation
given a topic. Parses the LLM output into structured fields.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from loguru import logger

from src.generation.prompts import (
    QUESTION_GENERATOR_SYSTEM,
    QUESTION_GENERATOR_USER_TEMPLATE,
)
from src.retrieval.vector_store import VectorStore


@dataclass
class MCATQuestion:
    topic: str
    question_stem: str
    choices: dict[str, str]          # {"A": "...", "B": "...", "C": "...", "D": "..."}
    correct_answer: str              # "A", "B", "C", or "D"
    correct_rationale: str
    explanation: str                 # full tutor-style explanation
    sources: list[dict] = field(default_factory=list)
    raw_output: str = ""
    model: str = ""


class QuestionGenerator:
    """
    Orchestrates retrieval + generation for MCAT question generation.

    Usage:
        gen = QuestionGenerator(vector_store)
        q = gen.generate("buoyancy")
        print(q.question_stem)
    """

    def __init__(
        self,
        vector_store: VectorStore,
        model: str | None = None,
        top_k: int = 4,
        temperature: float = 0.6,
    ):
        self._store = vector_store
        self._model_name = model or os.getenv("LLM_MODEL", "gpt-4o-mini")
        self._top_k = top_k
        self._llm = ChatOpenAI(
            model=self._model_name,
            temperature=temperature,
            api_key=os.environ["OPENAI_API_KEY"],
        )

    def generate(self, topic: str) -> MCATQuestion:
        # 1. Retrieve context
        sources = self._store.search(topic, top_k=self._top_k)
        context = self._format_context(sources)

        # 2. Build messages
        system_msg = SystemMessage(content=QUESTION_GENERATOR_SYSTEM)
        user_content = QUESTION_GENERATOR_USER_TEMPLATE.format(
            context=context,
            topic=topic,
        )
        human_msg = HumanMessage(content=user_content)

        logger.info(f"Generating MCAT question | topic={topic!r} | model={self._model_name}")

        # 3. Call LLM
        response = self._llm.invoke([system_msg, human_msg])
        raw = response.content.strip()

        # 4. Parse structured output
        return self._parse_output(raw, topic=topic, sources=sources)

    # ------------------------------------------------------------------
    # Parsing
    # ------------------------------------------------------------------

    def _parse_output(self, raw: str, topic: str, sources: list[dict]) -> MCATQuestion:
        """Parse the LLM's structured output into MCATQuestion fields."""

        question_stem    = self._extract_section(raw, "Question",       "Answer Choices")
        choices_block    = self._extract_section(raw, "Answer Choices",  "Correct Answer")
        correct_block    = self._extract_section(raw, "Correct Answer",  "Explanation")
        explanation      = self._extract_section(raw, "Explanation",     None)

        choices = self._parse_choices(choices_block)
        correct_letter, correct_rationale = self._parse_correct(correct_block)

        return MCATQuestion(
            topic=topic,
            question_stem=question_stem.strip(),
            choices=choices,
            correct_answer=correct_letter,
            correct_rationale=correct_rationale,
            explanation=explanation.strip(),
            sources=sources,
            raw_output=raw,
            model=self._model_name,
        )

    @staticmethod
    def _extract_section(text: str, start_heading: str, end_heading: str | None) -> str:
        """Extract text between two bold markdown headings."""
        start_pattern = re.escape(f"**{start_heading}**")
        start_match = re.search(start_pattern, text, re.IGNORECASE)
        if not start_match:
            return ""

        start_idx = start_match.end()

        if end_heading:
            end_pattern = re.escape(f"**{end_heading}**")
            end_match = re.search(end_pattern, text[start_idx:], re.IGNORECASE)
            end_idx = start_idx + end_match.start() if end_match else len(text)
        else:
            end_idx = len(text)

        return text[start_idx:end_idx].strip()

    @staticmethod
    def _parse_choices(block: str) -> dict[str, str]:
        """Parse 'A) ...\nB) ...' into {"A": "...", "B": "..."}."""
        choices: dict[str, str] = {}
        for line in block.splitlines():
            m = re.match(r"^([A-D])[).]\s*(.*)", line.strip())
            if m:
                choices[m.group(1)] = m.group(2).strip()
        return choices

    @staticmethod
    def _parse_correct(block: str) -> tuple[str, str]:
        """Return (letter, rationale) from the correct answer block."""
        block = block.strip()
        m = re.match(r"^([A-D])[).:]?\s*(.*)", block, re.DOTALL)
        if m:
            return m.group(1).upper(), m.group(2).strip()
        return block[:1].upper() if block else "?", block

    @staticmethod
    def _format_context(sources: list[dict]) -> str:
        parts: list[str] = []
        for i, src in enumerate(sources, 1):
            meta = src["metadata"]
            label = f"{meta.get('source', 'unknown')}, p.{meta.get('page', '?')}"
            parts.append(f"[{i}] ({label})\n{src['text']}")
        return "\n\n".join(parts)
