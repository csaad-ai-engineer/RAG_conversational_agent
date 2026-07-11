"""Retrieval-augmented generation chain with simple tool-calling routing.

The agent first lets the LLM decide whether the user's question requires an
operational tool call (e.g. checking a live appointment status) or a grounded
answer from the knowledge base. This keeps the RAG path and the tool-calling
path clearly separated and easy to demo.
"""
import json
import re

from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate

from backend import config
from backend.ingestion import get_vectorstore
from backend.tools import TOOL_REGISTRY

ROUTER_PROMPT = ChatPromptTemplate.from_template(
    """You are a routing assistant for a DoctoBook support agent tool.
Decide whether the user's question requires calling one of the available tools,
or whether it can be answered from the knowledge base (general policy/FAQ questions).

Available tools:
{tools_description}

If a tool is needed, respond ONLY with JSON: {{"tool": "<tool_name>", "arguments": {{...}}}}
If no tool is needed, respond ONLY with: {{"tool": null}}

User question: {question}
"""
)

ANSWER_PROMPT = ChatPromptTemplate.from_template(
    """You are a helpful DoctoBook internal support assistant, used only by internal
personnel. All data you have access to (documents, appointments, practitioners) is
fictional. Answer the question using ONLY the context below. If the context does not
contain the answer, say you don't know rather than guessing. Cite which source file
each fact comes from.

Context:
{context}

Question: {question}

Answer:"""
)


def _tools_description() -> str:
    lines = []
    for name, spec in TOOL_REGISTRY.items():
        lines.append(f"- {name}({spec['parameters']}): {spec['description']}")
    return "\n".join(lines)


def _extract_json(text: str) -> dict:
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        return {"tool": None}
    try:
        return json.loads(match.group(0))
    except json.JSONDecodeError:
        return {"tool": None}


class RagAgent:
    def __init__(self):
        self.llm = ChatOllama(model=config.OLLAMA_MODEL, temperature=0, base_url=config.OLLAMA_BASE_URL)
        self.vectorstore = get_vectorstore()

    def _route(self, question: str) -> dict:
        prompt = ROUTER_PROMPT.format(
            tools_description=_tools_description(), question=question
        )
        response = self.llm.invoke(prompt)
        return _extract_json(response.content)

    def _call_tool(self, tool_name: str, arguments: dict) -> dict:
        spec = TOOL_REGISTRY.get(tool_name)
        if not spec:
            return {"error": f"Unknown tool {tool_name}"}
        try:
            return spec["function"](**arguments)
        except TypeError as exc:
            return {"error": f"Invalid arguments for {tool_name}: {exc}"}

    def _answer_from_docs(self, question: str) -> dict:
        retriever = self.vectorstore.as_retriever(search_kwargs={"k": config.RETRIEVAL_K})
        docs = retriever.invoke(question)
        context = "\n\n".join(
            f"[{doc.metadata.get('source', 'unknown')}]\n{doc.page_content}" for doc in docs
        )
        prompt = ANSWER_PROMPT.format(context=context, question=question)
        response = self.llm.invoke(prompt)
        sources = sorted({doc.metadata.get("source", "unknown") for doc in docs})
        return {"answer": response.content, "sources": sources, "mode": "rag"}

    def ask(self, question: str) -> dict:
        routing = self._route(question)
        tool_name = routing.get("tool")

        if tool_name:
            arguments = routing.get("arguments", {}) or {}
            result = self._call_tool(tool_name, arguments)
            return {
                "answer": json.dumps(result, indent=2),
                "sources": [],
                "mode": "tool_call",
                "tool_used": tool_name,
                "tool_arguments": arguments,
            }

        return self._answer_from_docs(question)
