"""
FlashRank-based reranker for Advanced RAG.

Takes initial vector-search results (over-retrieved at top_k * 3) and
re-scores them with a cross-encoder, returning only the most relevant top_k.
"""

from __future__ import annotations

from loguru import logger


class Reranker:
    """
    Wraps FlashRank cross-encoder reranking.

    Usage:
        reranker = Reranker()
        top_chunks = reranker.rerank(query, initial_results, top_k=4)
    """

    _DEFAULT_MODEL = "ms-marco-MiniLM-L-12-v2"

    def __init__(self, model_name: str | None = None):
        self._model_name = model_name or self._DEFAULT_MODEL
        self._ranker = None  # lazy init on first use

    def _get_ranker(self):
        if self._ranker is None:
            from flashrank import Ranker  # type: ignore
            logger.info(f"Loading FlashRank reranker: {self._model_name}")
            self._ranker = Ranker(model_name=self._model_name)
        return self._ranker

    def rerank(self, query: str, results: list[dict], top_k: int = 4) -> list[dict]:
        """
        Rerank a list of retrieval results using a cross-encoder.

        Args:
            query:   The user's query string.
            results: Initial retrieval results from VectorStore.search().
                     Each dict must have at least "text", "metadata", "score".
            top_k:   Number of results to return after reranking.

        Returns:
            Re-ranked list of dicts (same format as input), length <= top_k.
        """
        if not results:
            return results

        if len(results) <= top_k:
            return results

        from flashrank import RerankRequest  # type: ignore

        passages = [{"id": i, "text": r["text"]} for i, r in enumerate(results)]
        request = RerankRequest(query=query, passages=passages)

        try:
            reranked = self._get_ranker().rerank(request)
        except Exception as exc:
            logger.warning(f"Reranking failed ({exc}); falling back to original order.")
            return results[:top_k]

        id_to_result = {i: results[i] for i in range(len(results))}
        out: list[dict] = []
        for item in reranked[:top_k]:
            orig = dict(id_to_result[item["id"]])
            orig["rerank_score"] = float(item["score"])
            out.append(orig)

        logger.info(
            f"Reranked {len(results)} → {len(out)} chunks "
            f"(top score: {out[0]['rerank_score']:.4f} if out else 'n/a')"
        )
        return out
