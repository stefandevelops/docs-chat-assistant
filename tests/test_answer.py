from pathlib import Path

from docs_chat.pipeline import DocsAssistant

WIKI = Path(__file__).resolve().parent.parent / "data" / "wiki"


def test_extractive_answer_cites_returns_policy() -> None:
    assistant = DocsAssistant(wiki_dir=WIKI)
    answer = assistant.ask("How many days do customers have to return a bike?", use_llm=False)
    assert not answer.abstained
    assert "30 days" in answer.text.lower()
    assert any(citation.source == "01-returns-policy.md" for citation in answer.citations)
    assert answer.mode == "extractive"


def test_unknown_question_abstains() -> None:
    assistant = DocsAssistant(wiki_dir=WIKI)
    answer = assistant.ask("What is the CEO's salary?", use_llm=False)
    assert answer.abstained
    assert answer.text.startswith("I don't know")
    assert answer.citations == []
