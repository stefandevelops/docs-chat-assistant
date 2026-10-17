from __future__ import annotations

from pathlib import Path

import streamlit as st

from docs_chat.llm import llm_mode_name
from docs_chat.models import Answer
from docs_chat.pipeline import DocsAssistant

ROOT = Path(__file__).resolve().parent
SAMPLE_QUESTIONS = [
    "How many days do customers have to return a bike?",
    "Who pays return shipping on a change-of-mind return?",
    "How long is the battery warranty?",
    "How fast do bikes ship to Ontario?",
    "When should a new CX hire escalate a ticket?",
    "How long is a trade-in quote valid?",
    "What is the CEO's salary?",
]

st.set_page_config(
    page_title="VoltPath Docs Assistant",
    page_icon="🚲",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
      .stApp { background: #f7f5f2; }
      .hero {
        padding: 0.2rem 0 0.8rem 0;
        border-bottom: 1px solid #ddd4c6;
        margin-bottom: 1.1rem;
      }
      .hero h1 { font-size: 1.7rem; margin-bottom: 0.25rem; color: #1c1917; }
      .hero p { color: #57534e; margin: 0; }
      .badge {
        display: inline-block;
        padding: 0.15rem 0.55rem;
        border-radius: 999px;
        font-size: 0.78rem;
        font-weight: 600;
        background: #dcfce7;
        color: #14532d;
      }
      .badge-llm { background: #dbeafe; color: #1e3a8a; }
      .cite {
        background: #fff;
        border: 1px solid #e7e0d4;
        border-left: 3px solid #0f6e56;
        border-radius: 8px;
        padding: 0.65rem 0.8rem;
        margin-top: 0.45rem;
      }
      .cite .src { font-weight: 600; color: #0f6e56; font-size: 0.86rem; }
      .cite .head { color: #57534e; font-size: 0.8rem; }
      .cite .sn { color: #44403c; font-size: 0.84rem; margin-top: 0.25rem; }
      .doc-row { font-size: 0.86rem; color: #44403c; padding: 0.15rem 0; }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_resource(show_spinner="Indexing the VoltPath help centre…")
def load_assistant() -> DocsAssistant:
    return DocsAssistant(wiki_dir=ROOT / "data" / "wiki")


def render_answer(answer: Answer) -> None:
    st.markdown(answer.text)
    if answer.abstained or not answer.citations:
        return
    st.caption("Sources")
    for citation in answer.citations:
        heading = f" · {citation.heading}" if citation.heading else ""
        st.markdown(
            f"""
            <div class="cite">
              <div class="src">{citation.title}{heading}</div>
              <div class="head">{citation.source}</div>
              <div class="sn">{citation.snippet}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


assistant = load_assistant()
mode = llm_mode_name()
mode_label = "LLM" if mode else "Demo (extractive, no API key)"
badge_class = "badge badge-llm" if mode else "badge"

with st.sidebar:
    st.markdown("### VoltPath CX")
    st.markdown(
        f'<span class="badge {badge_class}">{mode_label}</span>',
        unsafe_allow_html=True,
    )
    st.write("")
    st.write(
        "Indexed **{} pages** / **{} chunks** from the internal help centre.".format(
            len(assistant.documents),
            len(assistant.chunks),
        )
    )
    st.markdown("#### Sample questions")
    for question in SAMPLE_QUESTIONS:
        if st.button(question, key=f"sample-{question}", use_container_width=True):
            st.session_state["pending_question"] = question
            st.rerun()
    st.markdown("#### Indexed pages")
    for document in assistant.documents:
        st.markdown(
            f'<div class="doc-row">{document.title}<br><em>{document.source}</em></div>',
            unsafe_allow_html=True,
        )
    st.caption(
        "Demo data only. Not a real retailer. Set OPENAI_API_KEY or GEMINI_API_KEY to switch on generated answers."
    )

st.markdown(
    """
    <div class="hero">
      <h1>Chat with the VoltPath help centre</h1>
      <p>Ask a policy question. Answers come from the indexed wiki and cite the source page.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        if message["role"] == "assistant":
            render_answer(message["answer"])
        else:
            st.markdown(message["content"])

pending = st.session_state.pop("pending_question", None)
prompt = st.chat_input("Ask about returns, shipping, warranty, onboarding…")
question = pending or prompt

if question:
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)
    with st.chat_message("assistant"):
        with st.spinner("Searching the help centre…"):
            answer = assistant.ask(question)
        render_answer(answer)
    st.session_state.messages.append({"role": "assistant", "content": answer.text, "answer": answer})
