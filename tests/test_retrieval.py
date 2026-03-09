"""
Tests for the retrieval layer (embeddings + vector store).

Uses a mock embedder so no API key is required.
"""

from __future__ import annotations

import math
import random
from typing import Sequence
from unittest.mock import MagicMock, patch

import pytest

from src.ingestion.chunker import TextChunk
from src.retrieval.embeddings import BaseEmbedder, get_embedder
from src.retrieval.vector_store import VectorStore


# ===========================================================================
# Mock embedder — produces deterministic, reproducible 8-dim embeddings
# ===========================================================================

class MockEmbedder(BaseEmbedder):
    """
    Produces embeddings by hashing text to a fixed-length vector.
    Semantically related queries will NOT be close (it's just for testing plumbing).
    """

    def __init__(self, dim: int = 8):
        self._dim = dim

    def embed_documents(self, texts: Sequence[str]) -> list[list[float]]:
        return [self._embed(t) for t in texts]

    def embed_query(self, text: str) -> list[float]:
        return self._embed(text)

    @property
    def dimension(self) -> int:
        return self._dim

    def _embed(self, text: str) -> list[float]:
        rng = random.Random(hash(text) % (2**32))
        vec = [rng.gauss(0, 1) for _ in range(self._dim)]
        norm = math.sqrt(sum(x**2 for x in vec)) or 1.0
        return [x / norm for x in vec]


# ===========================================================================
# Fixtures
# ===========================================================================

@pytest.fixture
def sample_chunks() -> list[TextChunk]:
    return [
        TextChunk(
            text="Bernoulli's principle: faster fluid has lower pressure. P + rho*v^2/2 = constant.",
            metadata={"source": "princeton", "page": 10, "chunk_index": 0, "section": "Bernoulli"},
        ),
        TextChunk(
            text="The continuity equation A1*v1 = A2*v2 conserves flow rate.",
            metadata={"source": "princeton", "page": 12, "chunk_index": 0, "section": "Continuity"},
        ),
        TextChunk(
            text="Archimedes' principle: buoyant force = weight of displaced fluid. F_b = rho*V*g.",
            metadata={"source": "examkrackers", "page": 5, "chunk_index": 0, "section": "Buoyancy"},
        ),
        TextChunk(
            text="Poiseuille's law: Q = pi*r^4*DeltaP / (8*eta*L). Fourth power of radius!",
            metadata={"source": "examkrackers", "page": 8, "chunk_index": 0, "section": "Poiseuille"},
        ),
        TextChunk(
            text="Pascal's principle: pressure applied to an enclosed fluid is transmitted equally.",
            metadata={"source": "princeton", "page": 7, "chunk_index": 0, "section": "Pascal"},
        ),
    ]


@pytest.fixture
def vector_store(sample_chunks) -> VectorStore:
    store = VectorStore(embedder=MockEmbedder())
    store.build_from_chunks(sample_chunks)
    return store


# ===========================================================================
# VectorStore.build_from_chunks
# ===========================================================================

class TestVectorStoreBuild:
    def test_builds_without_error(self, sample_chunks):
        store = VectorStore(embedder=MockEmbedder())
        store.build_from_chunks(sample_chunks)
        assert store.is_loaded()

    def test_is_not_loaded_before_build(self):
        store = VectorStore(embedder=MockEmbedder())
        assert not store.is_loaded()

    def test_requires_store_raises(self):
        store = VectorStore(embedder=MockEmbedder())
        with pytest.raises(RuntimeError, match="not initialized"):
            store.search("test query")


# ===========================================================================
# VectorStore.search
# ===========================================================================

class TestVectorStoreSearch:
    def test_returns_list(self, vector_store):
        results = vector_store.search("Bernoulli pressure", top_k=3)
        assert isinstance(results, list)

    def test_returns_top_k(self, vector_store):
        results = vector_store.search("fluid flow", top_k=3)
        assert len(results) <= 3

    def test_result_structure(self, vector_store):
        results = vector_store.search("fluid dynamics")
        for r in results:
            assert "text" in r
            assert "metadata" in r
            assert "score" in r

    def test_result_text_is_string(self, vector_store):
        results = vector_store.search("pressure")
        for r in results:
            assert isinstance(r["text"], str)

    def test_metadata_has_source_and_page(self, vector_store):
        results = vector_store.search("buoyancy")
        for r in results:
            assert "source" in r["metadata"]
            assert "page" in r["metadata"]

    def test_search_texts_returns_strings(self, vector_store):
        texts = vector_store.search_texts("Bernoulli", top_k=2)
        assert all(isinstance(t, str) for t in texts)
        assert len(texts) <= 2

    def test_returns_fewer_than_k_when_small_corpus(self, sample_chunks):
        # Build store with only 2 chunks
        store = VectorStore(embedder=MockEmbedder())
        store.build_from_chunks(sample_chunks[:2])
        results = store.search("anything", top_k=10)
        assert len(results) <= 2


# ===========================================================================
# VectorStore persistence (save/load)
# ===========================================================================

class TestVectorStorePersistence:
    def _build_persistent(self, chunks, tmp_path) -> VectorStore:
        """Helper: build a VectorStore with a persist_directory so ChromaDB writes to disk."""
        store = VectorStore(embedder=MockEmbedder(), persist_directory=tmp_path)
        store.build_from_chunks(chunks)
        return store

    def test_save_creates_chroma_db(self, sample_chunks, tmp_path):
        store = self._build_persistent(sample_chunks, tmp_path)
        store.save(tmp_path)  # no-op, but should not raise
        assert (tmp_path / "chroma.sqlite3").exists()

    def test_load_after_build(self, sample_chunks, tmp_path):
        self._build_persistent(sample_chunks, tmp_path)

        # Load into a fresh store
        new_store = VectorStore(embedder=MockEmbedder())
        new_store.load(tmp_path)
        assert new_store.is_loaded()

    def test_loaded_store_can_search(self, sample_chunks, tmp_path):
        self._build_persistent(sample_chunks, tmp_path)
        new_store = VectorStore(embedder=MockEmbedder())
        new_store.load(tmp_path)
        results = new_store.search("fluid pressure", top_k=2)
        assert len(results) > 0

    def test_load_nonexistent_raises(self, tmp_path):
        store = VectorStore(embedder=MockEmbedder())
        with pytest.raises(FileNotFoundError):
            store.load(tmp_path / "does_not_exist")


# ===========================================================================
# get_embedder factory
# ===========================================================================

class TestGetEmbedderFactory:
    def test_unknown_backend_raises(self, monkeypatch):
        monkeypatch.setenv("EMBEDDING_BACKEND", "foobar")
        with pytest.raises(ValueError, match="Unknown embedding backend"):
            get_embedder("foobar")

    def test_valid_backends_listed_in_error(self, monkeypatch):
        with pytest.raises(ValueError) as exc_info:
            get_embedder("bad_backend")
        msg = str(exc_info.value)
        assert "openai" in msg
        assert "local" in msg
        assert "qwen3" in msg
