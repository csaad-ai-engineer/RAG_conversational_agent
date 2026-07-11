from contextlib import asynccontextmanager

from fastapi import FastAPI
from pydantic import BaseModel

from backend.rag import RagAgent

agent: RagAgent | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global agent
    agent = RagAgent()
    yield


app = FastAPI(title="DoctoBook Support RAG Agent", lifespan=lifespan)


class ChatRequest(BaseModel):
    question: str


class ChatResponse(BaseModel):
    answer: str
    sources: list[str]
    mode: str
    tool_used: str | None = None
    tool_arguments: dict | None = None


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    result = agent.ask(request.question)
    return ChatResponse(**result)


@app.get("/health")
def health():
    return {"status": "ok"}
