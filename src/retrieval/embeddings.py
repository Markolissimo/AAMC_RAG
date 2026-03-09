"""
Embedding model abstraction supporting three backends:
  - "openai"  → text-embedding-3-small   (1536-dim, needs API key)
  - "local"   → all-MiniLM-L6-v2         (384-dim, runs offline, fast)
  - "qwen3"   → Qwen3-Embedding-4B        (2560-dim, runs offline, high quality, ~8GB VRAM)

Selected via EMBEDDING_BACKEND env var.
"""

from __future__ import annotations

import os
from abc import ABC, abstractmethod
from typing import Sequence

import numpy as np
from loguru import logger


class BaseEmbedder(ABC):
    @abstractmethod
    def embed_documents(self, texts: Sequence[str]) -> list[list[float]]:
        ...

    @abstractmethod
    def embed_query(self, text: str) -> list[float]:
        ...

    @property
    @abstractmethod
    def dimension(self) -> int:
        ...


# ---------------------------------------------------------------------------
# OpenAI backend
# ---------------------------------------------------------------------------

class OpenAIEmbedder(BaseEmbedder):
    """Wraps text-embedding-3-small with batching support."""

    def __init__(self, model: str = "text-embedding-3-small", batch_size: int = 100):
        from openai import OpenAI
        self._client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
        self._model = model
        self._batch_size = batch_size
        self._dim = 1536 if "3-small" in model else 3072

    def embed_documents(self, texts: Sequence[str]) -> list[list[float]]:
        texts = list(texts)
        all_embeddings: list[list[float]] = []
        for i in range(0, len(texts), self._batch_size):
            batch = texts[i : i + self._batch_size]
            logger.debug(f"Embedding batch {i // self._batch_size + 1} ({len(batch)} texts)")
            response = self._client.embeddings.create(input=batch, model=self._model)
            all_embeddings.extend([r.embedding for r in response.data])
        return all_embeddings

    def embed_query(self, text: str) -> list[float]:
        response = self._client.embeddings.create(input=[text], model=self._model)
        return response.data[0].embedding

    @property
    def dimension(self) -> int:
        return self._dim


# ---------------------------------------------------------------------------
# Local backend — sentence-transformers (lightweight)
# ---------------------------------------------------------------------------

class LocalEmbedder(BaseEmbedder):
    """sentence-transformers all-MiniLM-L6-v2 — no API key, low VRAM."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        from sentence_transformers import SentenceTransformer
        logger.info(f"Loading local embedding model: {model_name}")
        self._model = SentenceTransformer(model_name)
        self._dim = self._model.get_sentence_embedding_dimension()

    def embed_documents(self, texts: Sequence[str]) -> list[list[float]]:
        embeddings = self._model.encode(list(texts), show_progress_bar=True)
        return embeddings.tolist()

    def embed_query(self, text: str) -> list[float]:
        return self._model.encode([text])[0].tolist()

    @property
    def dimension(self) -> int:
        return self._dim


# ---------------------------------------------------------------------------
# Qwen3-Embedding-4B backend (high quality, local, ~8GB VRAM)
# ---------------------------------------------------------------------------

class Qwen3Embedder(BaseEmbedder):
    """
    Qwen/Qwen3-Embedding-4B — 2560-dim, last-token pooling, cosine-normalized.

    Uses an instruction prefix for queries so the model understands retrieval
    intent; passages are encoded without a prefix.

    Requirements: torch>=2.1.0, transformers>=4.51.0
    Hardware:     ~8 GB VRAM (GPU) or ~12 GB RAM (CPU, slow)
    """

    _DIM = 2560
    _QUERY_INSTRUCTION = (
        "Instruct: Given a question about MCAT Fluid Dynamics, "
        "retrieve the most relevant passage that answers it.\nQuery: "
    )

    def __init__(
        self,
        model_name: str = "Qwen/Qwen3-Embedding-4B",
        device: str | None = None,
        max_length: int = 512,
        batch_size: int = 8,
    ):
        import torch
        from transformers import AutoModel, AutoTokenizer

        self._device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        logger.info(f"Loading Qwen3-Embedding model: {model_name} on {self._device}")

        self._tokenizer = AutoTokenizer.from_pretrained(
            model_name, trust_remote_code=True
        )
        self._model = AutoModel.from_pretrained(
            model_name,
            trust_remote_code=True,
            torch_dtype=torch.float16 if self._device == "cuda" else torch.float32,
        ).to(self._device)
        self._model.eval()
        self._max_length = max_length
        self._batch_size = batch_size

    def embed_documents(self, texts: Sequence[str]) -> list[list[float]]:
        return self._encode(list(texts), is_query=False)

    def embed_query(self, text: str) -> list[float]:
        return self._encode([text], is_query=True)[0]

    def _encode(self, texts: list[str], is_query: bool) -> list[list[float]]:
        import torch
        import torch.nn.functional as F

        if is_query:
            texts = [self._QUERY_INSTRUCTION + t for t in texts]

        all_embeddings: list[list[float]] = []

        for i in range(0, len(texts), self._batch_size):
            batch = texts[i : i + self._batch_size]
            with torch.no_grad():
                encoded = self._tokenizer(
                    batch,
                    padding=True,
                    truncation=True,
                    max_length=self._max_length,
                    return_tensors="pt",
                ).to(self._device)

                output = self._model(**encoded)

                # Last-token pooling: index of last non-padding token per row
                seq_lens = encoded["attention_mask"].sum(dim=1) - 1
                batch_size = output.last_hidden_state.size(0)
                embeddings = output.last_hidden_state[
                    torch.arange(batch_size, device=self._device), seq_lens
                ]
                embeddings = F.normalize(embeddings, p=2, dim=1)
                all_embeddings.extend(embeddings.cpu().float().tolist())

        return all_embeddings

    @property
    def dimension(self) -> int:
        return self._DIM


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

def get_embedder(backend: str | None = None) -> BaseEmbedder:
    """
    Return the appropriate embedder based on env var or explicit argument.
    backend: "openai" | "local" | "qwen3" | None (reads EMBEDDING_BACKEND env var)
    """
    backend = backend or os.getenv("EMBEDDING_BACKEND", "openai")
    backend = backend.lower().strip()

    if backend == "openai":
        model = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
        logger.info(f"Using OpenAI embedder: {model}")
        return OpenAIEmbedder(model=model)
    elif backend == "local":
        model = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2").replace("local:", "")
        logger.info(f"Using local embedder: {model}")
        return LocalEmbedder(model_name=model)
    elif backend == "qwen3":
        model = os.getenv("EMBEDDING_MODEL", "Qwen/Qwen3-Embedding-4B")
        logger.info(f"Using Qwen3 embedder: {model}")
        return Qwen3Embedder(model_name=model)
    else:
        raise ValueError(
            f"Unknown embedding backend: {backend!r}. "
            "Choose 'openai', 'local', or 'qwen3'."
        )
