import os

import requests
import streamlit as st

BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8000")

st.set_page_config(page_title="DoctoBook Support Assistant", page_icon="💬")
st.title("💬 DoctoBook Support Assistant (RAG demo)")
st.caption(
    "Retrieval-augmented chatbot over synthetic support docs, with tool calling "
    "for live-style operational lookups (appointment status, availability)."
)
st.warning(
    "For internal personnel use only. All data (documents, appointments, "
    "practitioners) is fictional — no real patient or company data is used.",
    icon="⚠️",
)

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message.get("meta"):
            st.caption(message["meta"])

question = st.chat_input("Ask about bookings, teleconsultation, billing, GDPR, or an appointment ID...")

if question:
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                response = requests.post(f"{BACKEND_URL}/chat", json={"question": question}, timeout=60)
                response.raise_for_status()
                data = response.json()
            except requests.RequestException as exc:
                st.error(f"Backend request failed: {exc}")
                st.stop()

        st.markdown(data["answer"])

        if data["mode"] == "tool_call":
            meta = f"🔧 Tool used: `{data['tool_used']}` with arguments `{data['tool_arguments']}`"
        elif data["sources"]:
            meta = f"📚 Sources: {', '.join(data['sources'])}"
        else:
            meta = None

        if meta:
            st.caption(meta)

    st.session_state.messages.append(
        {"role": "assistant", "content": data["answer"], "meta": meta}
    )
