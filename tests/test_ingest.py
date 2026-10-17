from pathlib import Path

from docs_chat.ingest import chunk_documents, load_documents

WIKI = Path(__file__).resolve().parent.parent / "data" / "wiki"


def test_wiki_loads_markdown_and_pdf() -> None:
    documents = load_documents(WIKI)
    sources = {document.source for document in documents}
    assert len(documents) >= 14
    assert "01-returns-policy.md" in sources
    assert "13-store-credit-terms.pdf" in sources
    pdf = next(document for document in documents if document.source.endswith(".pdf"))
    assert "never expire" in pdf.text.lower()


def test_chunks_keep_source_and_heading() -> None:
    chunks = chunk_documents(load_documents(WIKI))
    assert len(chunks) >= 20
    returns = [chunk for chunk in chunks if chunk.source == "01-returns-policy.md"]
    assert returns
    assert any("30 days" in chunk.text for chunk in returns)
    assert all(chunk.title and chunk.source for chunk in chunks)
