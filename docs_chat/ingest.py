from __future__ import annotations

import re
from pathlib import Path

from pypdf import PdfReader

from docs_chat.models import Chunk, Document

WIKI_SUFFIXES = {".md", ".markdown", ".pdf"}
TARGET_CHUNK_CHARS = 900
CHUNK_OVERLAP_CHARS = 120


def load_documents(wiki_dir: Path) -> list[Document]:
    if not wiki_dir.is_dir():
        raise FileNotFoundError(f"Wiki folder not found: {wiki_dir}")

    documents: list[Document] = []
    for path in sorted(wiki_dir.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in WIKI_SUFFIXES:
            continue
        text = _read_file(path)
        if not text.strip():
            continue
        title = _title_from_text(text) or path.stem.replace("-", " ").title()
        documents.append(
            Document(
                doc_id=path.stem,
                title=title,
                source=path.name,
                text=text.strip(),
            )
        )
    return documents


def chunk_documents(documents: list[Document]) -> list[Chunk]:
    chunks: list[Chunk] = []
    for document in documents:
        for index, (heading, body) in enumerate(_split_sections(document.text)):
            for piece_index, piece in enumerate(_window(body)):
                chunk_id = f"{document.doc_id}:{index}:{piece_index}"
                chunks.append(
                    Chunk(
                        chunk_id=chunk_id,
                        doc_id=document.doc_id,
                        title=document.title,
                        source=document.source,
                        heading=heading,
                        text=piece,
                    )
                )
    return chunks


def _read_file(path: Path) -> str:
    if path.suffix.lower() == ".pdf":
        return _read_pdf(path)
    return path.read_text(encoding="utf-8")


def _read_pdf(path: Path) -> str:
    reader = PdfReader(str(path))
    pages = [(page.extract_text() or "") for page in reader.pages]
    return "\n\n".join(pages)


def _title_from_text(text: str) -> str:
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("# "):
            return stripped[2:].strip()
        if stripped:
            return stripped[:80]
    return ""


def _split_sections(text: str) -> list[tuple[str, str]]:
    heading = "Overview"
    buffer: list[str] = []
    sections: list[tuple[str, str]] = []

    def flush() -> None:
        body = "\n".join(buffer).strip()
        if body:
            sections.append((heading, body))

    for line in text.splitlines():
        match = re.match(r"^(#{1,3})\s+(.+)$", line.strip())
        if match:
            flush()
            heading = match.group(2).strip()
            buffer = []
            continue
        buffer.append(line)
    flush()
    return sections or [("Overview", text.strip())]


def _window(text: str) -> list[str]:
    text = text.strip()
    if len(text) <= TARGET_CHUNK_CHARS:
        return [text]

    paragraphs = [part.strip() for part in re.split(r"\n\s*\n", text) if part.strip()]
    chunks: list[str] = []
    current = ""
    for paragraph in paragraphs:
        candidate = f"{current}\n\n{paragraph}".strip() if current else paragraph
        if len(candidate) <= TARGET_CHUNK_CHARS:
            current = candidate
            continue
        if current:
            chunks.append(current)
        if len(paragraph) <= TARGET_CHUNK_CHARS:
            current = paragraph
        else:
            chunks.extend(_hard_split(paragraph))
            current = ""
    if current:
        chunks.append(current)
    return _apply_overlap(chunks)


def _hard_split(text: str) -> list[str]:
    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = min(start + TARGET_CHUNK_CHARS, len(text))
        chunks.append(text[start:end].strip())
        if end == len(text):
            break
        start = max(end - CHUNK_OVERLAP_CHARS, start + 1)
    return [chunk for chunk in chunks if chunk]


def _apply_overlap(chunks: list[str]) -> list[str]:
    if len(chunks) <= 1:
        return chunks
    overlapped = [chunks[0]]
    for previous, current in zip(chunks, chunks[1:]):
        tail = previous[-CHUNK_OVERLAP_CHARS:]
        overlapped.append(f"{tail}\n\n{current}".strip() if tail else current)
    return overlapped
