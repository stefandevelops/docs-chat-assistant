from __future__ import annotations

from rank_bm25 import BM25Okapi

from docs_chat.models import Chunk, Hit
from docs_chat.textutil import tokenize


class Bm25Index:
    def __init__(self, chunks: list[Chunk]):
        if not chunks:
            raise ValueError("Cannot index an empty wiki.")
        self.chunks = chunks
        self._tokens = [tokenize(chunk.text) for chunk in chunks]
        self._bm25 = BM25Okapi(self._tokens)

    def search(self, query: str, k: int = 5) -> list[Hit]:
        tokens = tokenize(query)
        if not tokens:
            return []
        scores = self._bm25.get_scores(tokens)
        ranked = sorted(
            zip(self.chunks, scores),
            key=lambda item: item[1],
            reverse=True,
        )
        hits: list[Hit] = []
        for chunk, score in ranked[:k]:
            if score <= 0:
                continue
            hits.append(Hit(chunk=chunk, score=float(score)))
        return hits
