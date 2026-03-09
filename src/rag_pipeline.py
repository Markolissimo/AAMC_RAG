"""
RAG Pipeline — top-level orchestrator.

Responsible for:
  1. Ingesting PDFs (parse → chunk → embed → store)
  2. Loading an existing vector store from disk
  3. Routing requests to ExplanationEngine or QuestionGenerator
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from loguru import logger

from src.ingestion.chunker import PDFChunker
from src.ingestion.pdf_parser import PDFParser
from src.retrieval.embeddings import get_embedder
from src.retrieval.vector_store import VectorStore
from src.generation.explanation_engine import ExplanationEngine, ExplanationResult, ExplanationMode
from src.generation.question_generator import QuestionGenerator, MCATQuestion

load_dotenv()

_DEFAULT_DOCS_DIR    = Path(__file__).parent.parent / "docs"
_DEFAULT_STORE_PATH  = Path(__file__).parent.parent / "data" / "vector_store"


class RAGPipeline:
    """
    Single entry point for the MCAT AI Tutor system.

    Quick start:
        pipeline = RAGPipeline()
        pipeline.ingest()                  # first run only
        answer = pipeline.explain("Explain Bernoulli's principle")
        question = pipeline.generate_question("buoyancy")
    """

    def __init__(
        self,
        docs_dir: str | Path | None = None,
        store_path: str | Path | None = None,
        llm_model: str | None = None,
        embedding_backend: str | None = None,
        top_k: int | None = None,
    ):
        self.docs_dir   = Path(docs_dir   or _DEFAULT_DOCS_DIR)
        self.store_path = Path(store_path or os.getenv("VECTOR_STORE_PATH", str(_DEFAULT_STORE_PATH)))
        self._llm_model = llm_model or os.getenv("LLM_MODEL", "gpt-4o-mini")
        self._top_k     = top_k or int(os.getenv("TOP_K_RETRIEVAL", "4"))

        embedder = get_embedder(embedding_backend)
        self._vector_store = VectorStore(
            embedder=embedder,
            persist_directory=self.store_path,
        )

        self._explanation_engine: ExplanationEngine | None = None
        self._question_generator: QuestionGenerator | None = None

    # ------------------------------------------------------------------
    # Ingestion
    # ------------------------------------------------------------------

    def ingest(self, force: bool = False) -> None:
        """
        Parse PDFs, chunk them, embed, and save to disk.
        Skips if vector store already exists unless force=True.
        """
        chroma_db = self.store_path / "chroma.sqlite3"
        if chroma_db.exists() and not force:
            logger.info("ChromaDB store already exists. Loading from disk (use force=True to re-ingest).")
            try:
                self.load()
                return
            except RuntimeError as exc:
                logger.warning(
                    f"Existing ChromaDB store could not be loaded cleanly: {exc}. Re-ingesting from source PDFs."
                )

        logger.info(f"Starting ingestion from {self.docs_dir}")

        parser  = PDFParser(normalize_math=True)
        chunker = PDFChunker(
            chunk_size=int(os.getenv("CHUNK_SIZE", "500")),
            chunk_overlap=int(os.getenv("CHUNK_OVERLAP", "50")),
        )

        pages  = parser.parse_directory(self.docs_dir)
        chunks = chunker.chunk_pages(pages)

        self._vector_store.build_from_chunks(chunks)
        self._vector_store.save(self.store_path)

        self._init_engines()
        logger.info("Ingestion complete.")

    def load(self) -> None:
        """Load pre-built vector store from disk."""
        self._vector_store.load(self.store_path)
        self._init_engines()

    def _init_engines(self) -> None:
        self._explanation_engine = ExplanationEngine(
            vector_store=self._vector_store,
            model=self._llm_model,
            top_k=self._top_k,
        )
        self._question_generator = QuestionGenerator(
            vector_store=self._vector_store,
            model=self._llm_model,
            top_k=self._top_k,
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def explain(
        self,
        question: str,
        mode: ExplanationMode | str = ExplanationMode.STANDARD,
    ) -> ExplanationResult:
        """Generate a tutor-style explanation for a question."""
        self._require_ready()
        if isinstance(mode, str):
            mode = ExplanationMode(mode)
        return self._explanation_engine.explain(question, mode=mode)

    def explain_auto(self, raw_question: str) -> ExplanationResult:
        """
        Auto-detect explanation mode from the phrasing of the question.
        E.g. "Explain in simpler terms" → SIMPLER mode.
        """
        self._require_ready()
        clean_q, mode = self._explanation_engine.detect_mode(raw_question)
        return self._explanation_engine.explain(clean_q, mode=mode)

    def generate_question(self, topic: str) -> MCATQuestion:
        """Generate an MCAT-style question for a given topic."""
        self._require_ready()
        return self._question_generator.generate(topic)

    def is_ready(self) -> bool:
        return self._vector_store.is_loaded()

    def _require_ready(self) -> None:
        if not self.is_ready():
            raise RuntimeError(
                "Pipeline is not ready. Call pipeline.ingest() or pipeline.load() first."
            )
