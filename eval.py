#!/usr/bin/env python3
"""Run the golden-question set and print accuracy / citation hit rate."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path

from docs_chat.pipeline import DocsAssistant

ROOT = Path(__file__).resolve().parent
DEFAULT_QUESTIONS = ROOT / "evals" / "questions.json"


@dataclass
class CaseResult:
    case_id: str
    question: str
    passed: bool
    citation_hit: bool | None
    answer: str
    sources: list[str]
    detail: str


def load_cases(path: Path) -> list[dict]:
    return json.loads(path.read_text(encoding="utf-8"))


def evaluate(
    assistant: DocsAssistant,
    cases: list[dict],
    use_llm: bool | None = False,
) -> list[CaseResult]:
    results: list[CaseResult] = []
    for case in cases:
        answer = assistant.ask(case["question"], use_llm=use_llm)
        sources = [citation.source for citation in answer.citations]
        if case.get("abstain"):
            passed = answer.abstained or answer.text.lower().startswith("i don't know")
            citation_hit = None
            detail = "abstain" if passed else "expected I don't know"
        else:
            blob = answer.text.lower()
            missing = [phrase for phrase in case["must_include"] if phrase.lower() not in blob]
            passed = not missing and not answer.abstained
            expected = set(case.get("expected_sources") or [])
            citation_hit = bool(expected & set(sources))
            passed = passed and citation_hit
            if missing:
                detail = f"missing {missing}"
            elif not citation_hit:
                detail = f"citations {sources} missed {sorted(expected)}"
            else:
                detail = "ok"
        results.append(
            CaseResult(
                case_id=case["id"],
                question=case["question"],
                passed=passed,
                citation_hit=citation_hit,
                answer=answer.text,
                sources=sources,
                detail=detail,
            )
        )
    return results


def summarize(results: list[CaseResult]) -> dict[str, float | int]:
    accuracy = sum(1 for item in results if item.passed) / len(results)
    citation_cases = [item for item in results if item.citation_hit is not None]
    citation_hit_rate = (
        sum(1 for item in citation_cases if item.citation_hit) / len(citation_cases)
        if citation_cases
        else 0.0
    )
    return {
        "total": len(results),
        "passed": sum(1 for item in results if item.passed),
        "accuracy": accuracy,
        "citation_cases": len(citation_cases),
        "citation_hits": sum(1 for item in citation_cases if item.citation_hit),
        "citation_hit_rate": citation_hit_rate,
    }


def render(results: list[CaseResult]) -> str:
    lines = []
    stats = summarize(results)
    for item in results:
        mark = "PASS" if item.passed else "FAIL"
        cite = (
            "n/a"
            if item.citation_hit is None
            else ("hit" if item.citation_hit else "miss")
        )
        lines.append(f"[{mark}] {item.case_id}  citations={cite}  {item.detail}")
        lines.append(f"      Q: {item.question}")
        lines.append(f"      A: {item.answer}")
        if item.sources:
            lines.append(f"      sources: {', '.join(item.sources)}")
        lines.append("")
    lines.append(
        "Accuracy: {passed}/{total} ({accuracy:.0%})".format(**stats)
    )
    lines.append(
        "Citation hit rate: {citation_hits}/{citation_cases} ({citation_hit_rate:.0%})".format(
            **stats
        )
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--questions", type=Path, default=DEFAULT_QUESTIONS)
    parser.add_argument(
        "--llm",
        action="store_true",
        help="Use the configured LLM instead of the extractive demo.",
    )
    parser.add_argument(
        "--min-accuracy",
        type=float,
        default=0.8,
        help="Exit 1 if accuracy falls below this ratio.",
    )
    args = parser.parse_args()

    assistant = DocsAssistant(wiki_dir=ROOT / "data" / "wiki")
    results = evaluate(assistant, load_cases(args.questions), use_llm=args.llm)
    print(render(results))
    stats = summarize(results)
    if stats["accuracy"] < args.min_accuracy:
        print(f"\nBelow --min-accuracy ({args.min_accuracy:.0%}).", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
