# DoctoBook Support Assistant — RAG Conversational Agent

> ⚠️ **Fictional data · Internal use only**
> All documents, appointments, and practitioners in this project are synthetic. No real
> patient, company, or Doctolib data is used. This assistant is intended solely for
> **internal personnel** (e.g. internal support/ops staff) and is not a patient-facing
> product.

Retrieval-augmented chatbot built with LangChain and ChromaDB: document ingestion,
embedding-based retrieval, and grounded answer generation over a synthetic DoctoBook-style
support knowledge base (booking, teleconsultation, billing, GDPR). Also demonstrates simple
tool-calling for operational lookups (appointment status, practitioner availability) against
a mock internal API.

## Architecture

This is a **client-server (2-tier) architecture**, not microservices: a single FastAPI
backend owns ingestion, retrieval, generation and tool routing as internal modules, and a
Streamlit frontend talks to it over HTTP.

```
backend/          FastAPI app: ingestion, RAG chain, mock tools, API routes
frontend/          Streamlit chat UI
data/docs/          Synthetic DoctoBook-style support FAQ markdown docs
chroma_db/          Persisted vector store (generated, gitignored)
```

## Setup

1. Install [Ollama](https://ollama.com) and pull the models used:
   ```bash
   ollama pull llama3.1
   ollama pull nomic-embed-text
   ```
2. Install Python dependencies:
   ```bash
   python -m venv .venv && source .venv/bin/activate
   pip install -r requirements.txt
   ```
3. Ingest the knowledge base into ChromaDB:
   ```bash
   python -m backend.ingestion
   ```
4. Start the backend:
   ```bash
   uvicorn backend.main:app --reload
   ```
5. Start the frontend (in another terminal):
   ```bash
   streamlit run frontend/streamlit_app.py
   ```

## Setup (Docker)

Runs the backend and frontend in containers, connecting to Ollama on your host machine.

1. Install [Ollama](https://ollama.com) on the host and pull the models used:
   ```bash
   ollama pull llama3.1
   ollama pull nomic-embed-text
   ```
2. Build and start the stack:
   ```bash
   docker compose up --build
   ```
3. Backend: http://localhost:8000 · Frontend: http://localhost:8501

The backend container ingests the knowledge base into a named Docker volume
(`chroma_db`) on startup and talks to Ollama via `host.docker.internal`.

## Example questions

- "Can a patient reschedule an appointment less than an hour before it starts?"
- "Is teleconsultation reimbursed the same way as an in-person visit?"
- "What is APT-1001's status?" → triggers a tool call instead of RAG
- "Find availability for Dr. Dupont" → triggers a tool call
