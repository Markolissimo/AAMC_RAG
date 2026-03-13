"""
ChromaDB-backed vector store with automatic persistence.

Replaces FAISS with ChromaDB for:
  - Built-in persistent storage via sqlite3 (no explicit save step needed)
  - Cosine similarity by default (score: 1.0 = identical, 0.0 = unrelated)
  - Metadata filtering support for future extension (source, page, section)

Persistence layout (inside store_path/):
  chroma.sqlite3      — ChromaDB index + metadata
  <uuid>/             — embedding data shards
"""

from __future__ import annotations

import uuid
from pathlib import Path
from typing import Sequence

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from loguru import logger

from src.ingestion.chunker import TextChunk
from src.retrieval.embeddings import BaseEmbedder, get_embedder


class _LangChainEmbedderAdapter(Embeddings):
    """Adapter: our BaseEmbedder → LangChain Embeddings interface."""

    def __init__(self, embedder: BaseEmbedder):
        self._embedder = embedder

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return self._embedder.embed_documents(texts)

    def embed_query(self, text: str) -> list[float]:
        return self._embedder.embed_query(text)


class VectorStore:
    """
    ChromaDB-backed vector store:
    - Build from TextChunk list (auto-persists if persist_directory is set)
    - Similarity search returning (chunk_text, metadata, score)
    - load() re-opens an existing persisted collection
    - save() is a no-op kept for API compatibility (ChromaDB auto-persists)
    """

    _COLLECTION_NAME = "mcat_fluid_dynamics"

    def __init__(
        self,
        embedder: BaseEmbedder | None = None,
        persist_directory: str | Path | None = None,
    ):
        self._embedder = embedder or get_embedder()
        self._adapter = _LangChainEmbedderAdapter(self._embedder)
        self._persist_dir: str | None = (
            str(persist_directory) if persist_directory else None
        )
        self._collection_name = (
            self._COLLECTION_NAME
            if self._persist_dir
            else f"{self._COLLECTION_NAME}_{uuid.uuid4().hex}"
        )
        self._store: Chroma | None = None

    # ------------------------------------------------------------------
    # Build
    # ------------------------------------------------------------------

    def build_from_chunks(self, chunks: Sequence[TextChunk]) -> None:
        """Embed all chunks and build ChromaDB collection."""
        logger.info(f"Building ChromaDB collection from {len(chunks)} chunks…")
        if not chunks:
            raise ValueError(
                "No chunks were produced for ingestion. Check PDF parsing/chunking or your docs directory."
            )

        documents = [
            Document(page_content=c.text, metadata=c.metadata) for c in chunks
        ]

        kwargs: dict = dict(
            collection_name=self._collection_name,
            collection_metadata={"hnsw:space": "cosine"},
        )
        if self._persist_dir:
            Path(self._persist_dir).mkdir(parents=True, exist_ok=True)
            kwargs["persist_directory"] = self._persist_dir

        self._store = Chroma.from_documents(
            documents,
            embedding=self._adapter,
            **kwargs
        )
        logger.info(
            f"ChromaDB collection built"
            + (f" and persisted at {self._persist_dir}" if self._persist_dir else " (in-memory)")
        )

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------

    def search(self, query: str, top_k: int = 4) -> list[dict]:
        """
        Return top_k results as list of dicts:
        [{"text": ..., "metadata": ..., "score": ...}, ...]
        Score is Chroma's raw distance-style score; lower is more similar.
        """
        self._require_store()
        results = self._store.similarity_search_with_score(query, k=top_k)
        return [
            {
                "text": doc.page_content,
                "metadata": doc.metadata,
                "score": float(score),
            }
            for doc, score in results
        ]

    def search_texts(self, query: str, top_k: int = 4) -> list[str]:
        """Convenience method returning only the text strings."""
        return [r["text"] for r in self.search(query, top_k=top_k)]

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def add_chunks(self, chunks: Sequence[TextChunk]) -> None:
        """Add new chunks to an already-loaded ChromaDB collection."""
        self._require_store()
        if not chunks:
            return
        documents = [
            Document(page_content=c.text, metadata=c.metadata) for c in chunks
        ]
        self._store.add_documents(documents)
        logger.info(f"Added {len(chunks)} chunks to existing ChromaDB collection.")

    def remove_chunks_by_doc_id(self, doc_id: str) -> int:
        """
        Remove all chunks with metadata.doc_id == doc_id from ChromaDB.
        Returns the number of chunks removed.
        """
        self._require_store()
        
        # Get all chunks with this doc_id
        results = self._store._collection.get(
            where={"doc_id": doc_id},
            include=["metadatas"]
        )
        
        chunk_ids = results.get("ids", [])
        if not chunk_ids:
            logger.info(f"No chunks found for doc_id={doc_id}")
            return 0
        
        # Delete by IDs
        self._store._collection.delete(ids=chunk_ids)
        logger.info(f"Removed {len(chunk_ids)} chunk(s) for doc_id={doc_id}")
        return len(chunk_ids)

    def save(self, directory: str | Path) -> None:
        """
        No-op: ChromaDB auto-persists during build_from_chunks() when
        persist_directory is set. Kept for API compatibility.
        """
        self._require_store()
        logger.info(
            f"ChromaDB auto-persists; collection is at {self._persist_dir or '(in-memory)'}"
        )

    def load(self, directory: str | Path) -> None:
        """Re-open an existing persisted ChromaDB collection."""
        directory = Path(directory)
        db_file = directory / "chroma.sqlite3"
        if not db_file.exists():
            raise FileNotFoundError(
                f"No ChromaDB store found at {directory}. "
                "Run ingestion first (chroma.sqlite3 not present)."
            )
        self._collection_name = self._COLLECTION_NAME
        self._store = Chroma(
            collection_name=self._collection_name,
            embedding_function=self._adapter,
            persist_directory=str(directory),
            collection_metadata={"hnsw:space": "cosine"},
        )
        if self._store._collection.count() == 0:
            raise RuntimeError(
                f"ChromaDB store at {directory} is empty. Delete it and re-ingest the PDFs."
            )
        logger.info(f"ChromaDB collection loaded from {directory}")

    def is_loaded(self) -> bool:
        return self._store is not None

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _require_store(self) -> None:
        if self._store is None:
            raise RuntimeError(
                "Vector store is not initialized. Call build_from_chunks() or load()."
            )
