"""
RAG Pipeline — top-level orchestrator.

Responsible for:
  1. Ingesting PDFs via LlamaCloud OCR (parse → chunk → embed → store)
  2. Loading an existing vector store from disk
  3. Routing requests to ExplanationEngine or QuestionGenerator
"""

from __future__ import annotations

import os
import re
from pathlib import Path

from dotenv import load_dotenv
from loguru import logger

from src.ingestion.chunker import PDFChunker
from src.ingestion.ocr import parse_pdf, OCRResult
from src.ingestion import document_registry
from src.retrieval.embeddings import get_embedder
from src.retrieval.vector_store import VectorStore
from src.generation.explanation_engine import ExplanationEngine, ExplanationResult, ExplanationMode
from src.generation.question_generator import QuestionGenerator, MCATQuestion

load_dotenv()

_DEFAULT_DOCS_DIR   = Path(__file__).parent.parent / "docs"
_DEFAULT_STORE_PATH = Path(__file__).parent.parent / "data" / "vector_store"

# Session-uploaded files have an 8-char alphanumeric suffix: e.g. Source-EK_5bbee15f.md
_SESSION_SUFFIX_RE = re.compile(r'_[a-z0-9]{8}\.md$', re.IGNORECASE)


def _is_session_doc(doc_record: dict) -> bool:
    """Return True if this document was session-uploaded (has 8-char random suffix)."""
    md_path = doc_record.get("md_path") or ""
    return bool(_SESSION_SUFFIX_RE.search(Path(md_path).name))


class RAGPipeline:
    """
    Single entry point for the MCAT AI Tutor system.

    Quick start:
        pipeline = RAGPipeline()
        pipeline.load()                          # load existing store, or
        pipeline.ingest_pdf("my_doc.pdf")        # OCR → chunk → embed a new PDF
        answer = pipeline.explain("Explain Bernoulli's principle")
    """

    def __init__(
        self,
        docs_dir: str | Path | None = None,
        store_path: str | Path | None = None,
        llm_model: str | None = None,
        top_k: int | None = None,
    ):
        self.docs_dir   = Path(docs_dir   or _DEFAULT_DOCS_DIR)
        self.store_path = Path(store_path or os.getenv("VECTOR_STORE_PATH", str(_DEFAULT_STORE_PATH)))
        self._llm_model = llm_model or os.getenv("LLM_MODEL", "gpt-4o-mini")
        self._top_k     = top_k or int(os.getenv("TOP_K_RETRIEVAL", "4"))

        embedder = get_embedder()
        self._vector_store = VectorStore(
            embedder=embedder,
            persist_directory=self.store_path,
        )
        self._chunker = PDFChunker(
            chunk_size=int(os.getenv("CHUNK_SIZE", "500")),
            chunk_overlap=int(os.getenv("CHUNK_OVERLAP", "50")),
        )

        self._explanation_engine: ExplanationEngine | None = None
        self._question_generator: QuestionGenerator | None = None

    # ------------------------------------------------------------------
    # Ingestion
    # ------------------------------------------------------------------

    def ingest(self, force: bool = False) -> None:
        """
        Load existing vector store from disk, or attempt to build from base
        markdown files in docs/. Also cleans up any session docs left over
        from the previous session.
        """
        chroma_db = self.store_path / "chroma.sqlite3"
        store_loaded = False

        if chroma_db.exists() and not force:
            logger.info("ChromaDB store found. Loading from disk.")
            try:
                self._vector_store.load(self.store_path)
                store_loaded = True
            except RuntimeError as exc:
                logger.warning(f"Store load failed ({exc}). Will rebuild from docs/.")

        # Always remove session docs from previous session
        self._cleanup_session_docs()

        if store_loaded:
            self._init_engines()
            return

        # Build from base md files only (skip session-upload files)
        md_files = [
            f for f in self.docs_dir.glob("*.md")
            if not _SESSION_SUFFIX_RE.search(f.name)
        ]
        if not md_files:
            logger.info("No vector store and no markdown files found. Waiting for PDF upload.")
            return

        logger.info(f"Building store from {len(md_files)} base markdown file(s) in {self.docs_dir}")
        all_chunks = []
        for md_file in md_files:
            text = md_file.read_text(encoding="utf-8")
            chunks = self._chunker.chunk_text(
                text,
                metadata={"source": md_file.stem, "page": 1},
            )
            all_chunks.extend(chunks)

        if all_chunks:
            self._vector_store.build_from_chunks(all_chunks)
            self._vector_store.save(self.store_path)

        self._init_engines()
        logger.info("Ingestion from base markdown files complete.")

    def _cleanup_session_docs(self) -> None:
        """Remove all session-uploaded docs left over from a previous session."""
        docs = document_registry.list_documents()
        session_docs = [d for d in docs if _is_session_doc(d)]
        if not session_docs:
            return
        logger.info(f"Cleaning up {len(session_docs)} leftover session doc(s)…")
        for doc_record in session_docs:
            doc_id = doc_record["doc_id"]
            if self._vector_store.is_loaded():
                try:
                    self._vector_store.remove_chunks_by_doc_id(doc_id)
                except Exception as exc:
                    logger.warning(f"Could not remove Chroma chunks for {doc_id}: {exc}")
            document_registry.remove_document(doc_id)
            md_path_str = doc_record.get("md_path")
            if md_path_str:
                md_path = Path(md_path_str)
                if md_path.exists() and _SESSION_SUFFIX_RE.search(md_path.name):
                    md_path.unlink()
                    logger.info(f"Deleted session file: {md_path.name}")
        logger.info("Session cleanup complete.")

    def ingest_document(
        self,
        file_path: str | Path,
        llama_api_key: str | None = None,
        progress_callback=None,
    ) -> OCRResult:
        """
        Full pipeline for a new document (PDF or markdown):
          - PDF: LlamaCloud OCR → markdown → register → chunk → embed
          - Markdown: skip OCR → register → chunk → embed

        Args:
            file_path:        Path to the PDF or markdown file.
            llama_api_key:    LlamaCloud API key (required for PDF, ignored for .md).
            progress_callback: Optional callable(step: int, total: int, msg: str)
                               called at each stage for progress reporting.

        Returns:
            OCRResult with doc_id, pages, and md_path.
        """
        file_path = Path(file_path)
        total_steps = 5

        def _progress(step: int, msg: str) -> None:
            if progress_callback:
                progress_callback(step, total_steps, msg)
            logger.info(f"[{step}/{total_steps}] {msg}")

        # Handle markdown files (skip OCR)
        if file_path.suffix.lower() == ".md":
            _progress(1, f"Processing markdown file '{file_path.name}'…")
            import uuid
            import shutil
            from src.ingestion.ocr import OCRPage
            
            # Read markdown content
            md_text = file_path.read_text(encoding="utf-8")
            
            # Generate doc_id first so we can use it in the filename
            doc_id = str(uuid.uuid4())
            
            # Copy to docs/ with doc_id suffix — never overwrites pre-existing files
            self.docs_dir.mkdir(parents=True, exist_ok=True)
            clean_stem = file_path.stem.rsplit('_', 1)[0] if '_' in file_path.stem else file_path.stem
            final_md_path = self.docs_dir / f"{clean_stem}_{doc_id[:8]}.md"
            shutil.copy2(file_path, final_md_path)
            logger.info(f"Saved markdown to {final_md_path}")
            
            ocr_result = OCRResult(
                doc_id=doc_id,
                filename=file_path.name,
                full_markdown=md_text,
                pages=[
                    OCRPage(
                        page_number=1,
                        text=md_text,
                    )
                ],
                md_path=final_md_path,
            )
        else:
            # PDF: run OCR
            _progress(1, f"Uploading & OCR-parsing '{file_path.name}'…")
            ocr_result = parse_pdf(
                file_path,
                api_key=llama_api_key,
                save_to=self.docs_dir,
            )

        _progress(2, "Registering document & pages…")
        document_registry.register(ocr_result)

        _progress(3, "Chunking pages…")
        chunks = self._chunker.chunk_ocr_result(ocr_result)

        _progress(4, f"Embedding {len(chunks)} chunks…")
        if self._vector_store.is_loaded():
            self._vector_store.add_chunks(chunks)
        else:
            self._vector_store.build_from_chunks(chunks)

        _progress(5, "Saving vector store…")
        self._vector_store.save(self.store_path)
        self._init_engines()

        logger.info(f"Document '{file_path.name}' ingested successfully.")
        return ocr_result

    def remove_document(self, doc_id: str) -> bool:
        """
        Remove a document from the system:
          1. Delete chunks from vector store
          2. Remove from document registry (JSON)
          3. Delete markdown file if it exists

        Returns True if successful, False if document not found.
        """
        # Get document record to find md_path
        docs = document_registry.list_documents()
        doc_record = next((d for d in docs if d["doc_id"] == doc_id), None)
        
        if not doc_record:
            logger.warning(f"Document not found: doc_id={doc_id}")
            return False
        
        # 1. Remove chunks from vector store
        if self._vector_store.is_loaded():
            self._vector_store.remove_chunks_by_doc_id(doc_id)
        
        # 2. Remove from registry
        document_registry.remove_document(doc_id)
        
        # 3. Delete markdown file
        if doc_record.get("md_path"):
            md_path = Path(doc_record["md_path"])
            if md_path.exists():
                md_path.unlink()
                logger.info(f"Deleted markdown file: {md_path}")
        
        logger.info(f"Document removed: {doc_record['filename']} (doc_id={doc_id})")
        return True

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
        history: list[dict] | None = None,
    ) -> ExplanationResult:
        """Generate a tutor-style explanation for a question."""
        self._require_ready()
        if isinstance(mode, str):
            mode = ExplanationMode(mode)
        return self._explanation_engine.explain(question, mode=mode, history=history)

    def explain_auto(
        self,
        raw_question: str,
        history: list[dict] | None = None,
    ) -> ExplanationResult:
        """
        Auto-detect explanation mode from the phrasing of the question.
        E.g. "Explain in simpler terms" → SIMPLER mode.
        """
        self._require_ready()
        clean_q, mode = self._explanation_engine.detect_mode(raw_question)
        return self._explanation_engine.explain(clean_q, mode=mode, history=history)

    def generate_question(self, topic: str) -> MCATQuestion:
        """Generate an MCAT-style question for a given topic."""
        self._require_ready()
        return self._question_generator.generate(topic)

    def is_ready(self) -> bool:
        return self._vector_store.is_loaded()

    def _require_ready(self) -> None:
        if not self.is_ready():
            raise RuntimeError(
                "Pipeline is not ready. Upload a PDF first to build the knowledge base."
            )
