from __future__ import annotations

from pathlib import Path

from docs_chat.answer import compose_extractive_answer
from docs_chat.index import Bm25Index
from docs_chat.ingest import chunk_documents, load_documents
from docs_chat.llm import generate_llm_answer, llm_mode_name
from docs_chat.models import Answer, Chunk, Document, Hit

DEFAULT_WIKI = Path(__file__).resolve().parent.parent / "data" / "wiki"


class DocsAssistant:
    def __init__(self, wiki_dir: Path | None = None, top_k: int = 5):
        self.wiki_dir = Path(wiki_dir) if wiki_dir else DEFAULT_WIKI
        self.top_k = top_k
        self.documents: list[Document] = load_documents(self.wiki_dir)
        self.chunks: list[Chunk] = chunk_documents(self.documents)
        self.index = Bm25Index(self.chunks)

    @property
    def mode(self) -> str:
        return llm_mode_name() or "demo"

    def retrieve(self, question: str, k: int | None = None) -> list[Hit]:
        return self.index.search(question, k=k or self.top_k)

    def ask(self, question: str, use_llm: bool | None = None) -> Answer:
        hits = self.retrieve(question)
        should_use_llm = self.mode != "demo" if use_llm is None else use_llm
        if should_use_llm:
            return generate_llm_answer(question, hits)
        return compose_extractive_answer(question, hits)
