"""Loads support docs, splits them into chunks, and persists embeddings to ChromaDB."""
import chromadb
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings

from backend import config


def load_documents():
    loader = DirectoryLoader(config.DOCS_DIR, glob="**/*.md", loader_cls=TextLoader)
    return loader.load()


def split_documents(documents):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=config.CHUNK_SIZE,
        chunk_overlap=config.CHUNK_OVERLAP,
    )
    return splitter.split_documents(documents)


def build_vectorstore():
    documents = load_documents()
    chunks = split_documents(documents)

    # Drop any existing collection first so re-running ingestion (e.g. on every
    # container start) is idempotent instead of appending duplicate chunks.
    client = chromadb.PersistentClient(path=config.CHROMA_DIR)
    if config.COLLECTION_NAME in {c.name for c in client.list_collections()}:
        client.delete_collection(config.COLLECTION_NAME)

    embeddings = OllamaEmbeddings(model=config.OLLAMA_EMBED_MODEL, base_url=config.OLLAMA_BASE_URL)
    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        collection_name=config.COLLECTION_NAME,
        persist_directory=config.CHROMA_DIR,
    )
    return vectorstore


def get_vectorstore():
    embeddings = OllamaEmbeddings(model=config.OLLAMA_EMBED_MODEL, base_url=config.OLLAMA_BASE_URL)
    return Chroma(
        collection_name=config.COLLECTION_NAME,
        embedding_function=embeddings,
        persist_directory=config.CHROMA_DIR,
    )


if __name__ == "__main__":
    vs = build_vectorstore()
    print(f"Ingested and persisted vectorstore at {config.CHROMA_DIR}")
