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
      @import url("https://fonts.googleapis.com/css2?family=Source+Sans+3:wght@400;600;700&display=swap");
      html, body, [data-testid="stAppViewContainer"], [data-testid="stMarkdown"] {
        font-family: "Source Sans 3", "Liberation Sans", "Noto Sans", Arial, sans-serif;
      }
      .stApp { background: #f7f5f2; }
      .stAppDeployButton, #MainMenu { display: none; }
      .cite {
        background: #fff;
        border: 1px solid #e7e0d4;
        border-left: 4px solid #0f6e56;
        border-radius: 8px;
        padding: 0.7rem 0.85rem;
        margin-top: 0.5rem;
      }
      .cite .src { font-weight: 700; color: #0f6e56; font-size: 0.92rem; }
      .cite .head { color: #57534e; font-size: 0.82rem; }
      .cite .sn { color: #44403c; font-size: 0.88rem; margin-top: 0.3rem; }
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
        heading = ""
        if citation.heading and citation.heading.lower() != citation.title.lower():
            heading = f" · {citation.heading}"
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

with st.sidebar:
    st.header("VoltPath CX")
    if mode:
        st.success(f"LLM mode · {mode}", icon="✅")
    else:
        st.info("Demo mode · no API key", icon="📄")
    st.write(
        f"Indexed **{len(assistant.documents)} pages** / "
        f"**{len(assistant.chunks)} chunks** from the internal help centre."
    )
    st.subheader("Sample questions")
    for question in SAMPLE_QUESTIONS:
        if st.button(question, key=f"sample-{question}", use_container_width=True):
            st.session_state["pending_question"] = question
            st.rerun()
    st.subheader("Indexed pages")
    for document in assistant.documents:
        st.markdown(f"**{document.title}**  \n`{document.source}`")
    st.caption(
        "Demo data only. Not a real retailer. Set OPENAI_API_KEY or GEMINI_API_KEY "
        "to switch on generated answers."
    )

st.title("Chat with the VoltPath help centre")
st.caption(
    "Ask a policy question. Answers come from the indexed wiki and cite the source page."
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
    st.session_state.messages.append(
        {"role": "assistant", "content": answer.text, "answer": answer}
    )
