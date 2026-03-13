"""
Embedding model — OpenAI backend only (text-embedding-3-small).
"""

from __future__ import annotations

import os
from abc import ABC, abstractmethod
from typing import Sequence

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
# Factory
# ---------------------------------------------------------------------------

def get_embedder(backend: str | None = None) -> BaseEmbedder:
    """Return the OpenAI embedder (only supported backend)."""
    model = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
    logger.info(f"Using OpenAI embedder: {model}")
    return OpenAIEmbedder(model=model)
