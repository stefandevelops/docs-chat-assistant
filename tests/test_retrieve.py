from pathlib import Path

from docs_chat.pipeline import DocsAssistant

WIKI = Path(__file__).resolve().parent.parent / "data" / "wiki"


def test_return_question_ranks_returns_policy() -> None:
    assistant = DocsAssistant(wiki_dir=WIKI)
    hits = assistant.retrieve("How many days do customers have to return a bike?")
    assert hits
    assert hits[0].chunk.source == "01-returns-policy.md"
    assert hits[0].score > 1


def test_unknown_question_has_weak_overlap() -> None:
    assistant = DocsAssistant(wiki_dir=WIKI)
    hits = assistant.retrieve("What is the CEO's salary?")
    blob = " ".join(hit.chunk.text.lower() for hit in hits)
    assert "salary" not in blob
    assert "ceo" not in blob
