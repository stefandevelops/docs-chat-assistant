from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

from docs_chat.models import Answer, Hit
from docs_chat.answer import ABSTAIN_TEXT, citations_from_hits

SYSTEM_PROMPT = """You are the VoltPath internal help assistant.
Answer only from the numbered sources. If they do not contain the answer, reply exactly:
I don't know — that isn't covered in the VoltPath help centre.
Keep answers to 3–6 short sentences. Do not invent policy, prices, or dates.
After the answer, add a line that starts with Sources: and lists the source numbers you used, like Sources: 1, 3
"""


def llm_mode_name() -> str | None:
    if os.getenv("OPENAI_API_KEY"):
        return "openai"
    if os.getenv("GEMINI_API_KEY"):
        return "gemini"
    return None


def generate_llm_answer(question: str, hits: list[Hit]) -> Answer:
    if not hits:
        return Answer(text=ABSTAIN_TEXT, citations=[], mode="llm", abstained=True)

    context = _format_sources(hits)
    provider = llm_mode_name()
    if provider == "openai":
        raw = _openai_complete(question, context)
    elif provider == "gemini":
        raw = _gemini_complete(question, context)
    else:
        raise RuntimeError("No LLM API key is set.")

    text, used_indexes = _parse_llm_output(raw, source_count=len(hits))
    abstained = text.strip().lower().startswith("i don't know")
    used_hits = [hits[i] for i in used_indexes if 0 <= i < len(hits)] or hits[:3]
    citations = [] if abstained else citations_from_hits(used_hits)
    return Answer(text=text.strip(), citations=citations, mode="llm", abstained=abstained)


def _format_sources(hits: list[Hit]) -> str:
    blocks = []
    for index, hit in enumerate(hits, start=1):
        heading = f" — {hit.chunk.heading}" if hit.chunk.heading else ""
        blocks.append(
            f"[{index}] {hit.chunk.title}{heading} ({hit.chunk.source})\n{hit.chunk.text}"
        )
    return "\n\n".join(blocks)


def _openai_complete(question: str, context: str) -> str:
    from openai import OpenAI

    client = OpenAI(
        api_key=os.environ["OPENAI_API_KEY"],
        base_url=os.getenv("OPENAI_BASE_URL") or None,
    )
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    response = client.chat.completions.create(
        model=model,
        temperature=0.1,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": f"Sources:\n{context}\n\nQuestion: {question}",
            },
        ],
    )
    content = response.choices[0].message.content
    if not content:
        raise RuntimeError("The OpenAI-compatible API returned an empty answer.")
    return content


def _gemini_complete(question: str, context: str) -> str:
    model = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
    key = os.environ["GEMINI_API_KEY"]
    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
        f"?key={key}"
    )
    payload = {
        "systemInstruction": {"parts": [{"text": SYSTEM_PROMPT}]},
        "contents": [
            {
                "role": "user",
                "parts": [{"text": f"Sources:\n{context}\n\nQuestion: {question}"}],
            }
        ],
        "generationConfig": {"temperature": 0.1},
    }
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            body = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Gemini request failed: {exc.code} {detail}") from exc

    candidates = body.get("candidates") or []
    parts = candidates[0].get("content", {}).get("parts", []) if candidates else []
    text = "".join(part.get("text", "") for part in parts)
    if not text:
        raise RuntimeError("Gemini returned an empty answer.")
    return text


def _parse_llm_output(raw: str, source_count: int) -> tuple[str, list[int]]:
    lines = [line.rstrip() for line in raw.strip().splitlines()]
    used: list[int] = []
    body_lines: list[str] = []
    for line in lines:
        if line.lower().startswith("sources:"):
            for token in line.split(":", 1)[1].replace("[", " ").replace("]", " ").split(","):
                digits = "".join(ch for ch in token if ch.isdigit())
                if digits:
                    index = int(digits) - 1
                    if 0 <= index < source_count:
                        used.append(index)
            continue
        body_lines.append(line)
    return "\n".join(body_lines).strip(), used
