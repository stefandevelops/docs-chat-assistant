from pathlib import Path

from eval import evaluate, load_cases, summarize
from docs_chat.pipeline import DocsAssistant

ROOT = Path(__file__).resolve().parent.parent


def test_golden_set_meets_bar() -> None:
    assistant = DocsAssistant(wiki_dir=ROOT / "data" / "wiki")
    results = evaluate(assistant, load_cases(ROOT / "evals" / "questions.json"), use_llm=False)
    stats = summarize(results)
    failed = [item.case_id for item in results if not item.passed]
    assert stats["accuracy"] >= 0.8, failed
    assert stats["citation_hit_rate"] >= 0.8, failed
