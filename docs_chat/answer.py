from __future__ import annotations

from collections import defaultdict

from docs_chat.models import Answer, Citation, Hit
from docs_chat.textutil import candidate_sentences, snippet, tokenize

ABSTAIN_TEXT = (
    "I don't know — that isn't covered in the VoltPath help centre. "
    "Try a policy question (returns, shipping, warranty), or escalate if this is a live case."
)

MIN_SCORE = 1.15
MIN_TERM_COVERAGE = 0.4
MAX_ANSWER_SENTENCES = 4


def compose_extractive_answer(question: str, hits: list[Hit]) -> Answer:
    if not hits or hits[0].score < MIN_SCORE or _term_coverage(question, hits) < MIN_TERM_COVERAGE:
        return Answer(text=ABSTAIN_TEXT, citations=[], mode="extractive", abstained=True)

    sentences = _pick_sentences(question, hits)
    if not sentences:
        return Answer(text=ABSTAIN_TEXT, citations=[], mode="extractive", abstained=True)

    answer_text = " ".join(sentence for sentence, _hit in sentences)
    citations = _citations_from_hits([hit for _sentence, hit in sentences] or hits[:3])
    return Answer(text=answer_text, citations=citations, mode="extractive", abstained=False)


def citations_from_hits(hits: list[Hit], limit: int = 3) -> list[Citation]:
    return _citations_from_hits(hits[:limit])


def _term_coverage(question: str, hits: list[Hit]) -> float:
    terms = set(tokenize(question))
    if not terms:
        return 0.0
    blob = " ".join(hit.chunk.text for hit in hits[:3])
    found = set(tokenize(blob))
    return len(terms & found) / len(terms)


def _pick_sentences(question: str, hits: list[Hit]) -> list[tuple[str, Hit]]:
    query_terms = set(tokenize(question))
    scored: list[tuple[float, str, Hit]] = []
    for rank, hit in enumerate(hits):
        for sentence in candidate_sentences(hit.chunk.text):
            cleaned = _clean_sentence(sentence)
            if not _usable_sentence(cleaned):
                continue
            overlap = set(tokenize(cleaned)) & query_terms
            min_overlap = 1 if rank == 0 else 2
            if len(overlap) < min_overlap:
                continue
            density = len(overlap) / max(len(tokenize(cleaned)), 1)
            rank_boost = 1.15 if rank == 0 else 1.0
            prose_boost = 1.2 if cleaned.endswith((".", "!", "?")) else 1.0
            score = hit.score * (1 + len(overlap)) * (1 + density) * rank_boost * prose_boost
            scored.append((score, cleaned, hit))

    scored.sort(key=lambda item: item[0], reverse=True)
    picked: list[tuple[str, Hit]] = []
    seen: set[str] = set()
    for _score, sentence, hit in scored:
        key = sentence.lower()
        if key in seen:
            continue
        seen.add(key)
        picked.append((sentence, hit))
        if len(picked) >= MAX_ANSWER_SENTENCES:
            break
    return picked


def _clean_sentence(sentence: str) -> str:
    stripped = sentence.strip().lstrip("-* ").strip()
    return stripped


def _usable_sentence(sentence: str) -> bool:
    if len(sentence) < 28:
        return False
    if sentence.count("|") >= 2:
        return False
    if sentence.startswith("#"):
        return False
    letters = sum(1 for char in sentence if char.isalpha())
    return letters >= 16


def _citations_from_hits(hits: list[Hit]) -> list[Citation]:
    grouped: dict[str, list[Hit]] = defaultdict(list)
    for hit in hits:
        grouped[hit.chunk.source].append(hit)

    citations: list[Citation] = []
    for source, source_hits in grouped.items():
        best = max(source_hits, key=lambda item: item.score)
        citations.append(
            Citation(
                source=source,
                title=best.chunk.title,
                heading=best.chunk.heading,
                snippet=snippet(best.chunk.text),
                score=best.score,
            )
        )
    citations.sort(key=lambda item: item.score, reverse=True)
    return citations
