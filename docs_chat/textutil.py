from __future__ import annotations

import re

STOPWORDS = {
    "a",
    "about",
    "after",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "can",
    "do",
    "does",
    "for",
    "from",
    "get",
    "got",
    "had",
    "has",
    "have",
    "how",
    "i",
    "if",
    "in",
    "is",
    "it",
    "many",
    "me",
    "much",
    "my",
    "of",
    "on",
    "or",
    "our",
    "the",
    "their",
    "them",
    "this",
    "to",
    "we",
    "what",
    "when",
    "where",
    "which",
    "who",
    "with",
    "you",
    "your",
}


def tokenize(text: str) -> list[str]:
    tokens = re.findall(r"[a-z0-9]+", text.lower())
    return [stem(tok) for tok in tokens if tok not in STOPWORDS and len(tok) > 1]


def stem(token: str) -> str:
    if len(token) <= 3:
        return token
    if token.endswith("ies") and len(token) > 4:
        return token[:-3] + "y"
    if token.endswith(("ses", "xes", "zes", "ches", "shes")) and len(token) > 4:
        return token[:-2]
    if token.endswith("s") and not token.endswith("ss"):
        return token[:-1]
    return token


def split_sentences(text: str) -> list[str]:
    cleaned = re.sub(r"\s+", " ", text).strip()
    if not cleaned:
        return []
    parts = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9])", cleaned)
    return [part.strip() for part in parts if part.strip()]


def candidate_sentences(text: str) -> list[str]:
    """Turn wiki text into answer candidates, skipping tables and headings."""
    sentences: list[str] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.count("|") >= 2 or line.startswith("#"):
            continue
        line = re.sub(r"^[-*]\s+", "", line)
        if re.search(r"[.!?]", line):
            sentences.extend(split_sentences(line))
        else:
            sentences.append(line)
    return sentences


def snippet(text: str, limit: int = 220) -> str:
    collapsed = re.sub(r"\s+", " ", text).strip()
    if len(collapsed) <= limit:
        return collapsed
    return collapsed[: limit - 1].rsplit(" ", 1)[0] + "…"
