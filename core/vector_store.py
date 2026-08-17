import os
from pathlib import Path
import chromadb
from chromadb import Collection
from sentence_transformers import SentenceTransformer

_CHROMA_PATH = os.getenv("CHROMA_DB_PATH", "./db/chroma")
_EMBED_MODEL = "all-MiniLM-L6-v2"

_client: chromadb.PersistentClient = None
_embedder: SentenceTransformer = None


def _get_client() -> chromadb.PersistentClient:
    global _client
    if _client is None:
        Path(_CHROMA_PATH).mkdir(parents=True, exist_ok=True)
        _client = chromadb.PersistentClient(path=_CHROMA_PATH)
    return _client


def _get_embedder() -> SentenceTransformer:
    global _embedder
    if _embedder is None:
        _embedder = SentenceTransformer(_EMBED_MODEL)
    return _embedder


def init_collection(name: str) -> Collection:
    return _get_client().get_or_create_collection(
        name=name,
        metadata={"hnsw:space": "cosine"},
    )


def upsert_chunks(collection_name: str, chunks: list[dict]) -> None:
    """
    Each chunk: {text, source, page, chunk_id, version}
    """
    if not chunks:
        return
    collection = init_collection(collection_name)
    embedder = _get_embedder()
    texts = [c["text"] for c in chunks]
    embeddings = embedder.encode(texts, show_progress_bar=False).tolist()
    collection.upsert(
        ids=[c["chunk_id"] for c in chunks],
        embeddings=embeddings,
        documents=texts,
        metadatas=[
            {
                "source": c["source"],
                "page": c.get("page", 0),
                "version": c.get("version", 1),
            }
            for c in chunks
        ],
    )


def get_all(collection_name: str) -> list[dict]:
    """Return every chunk in the collection (used by BM25 indexer)."""
    collection = init_collection(collection_name)
    total = collection.count()
    if total == 0:
        return []
    results = collection.get(
        limit=total,
        include=["documents", "metadatas"],
    )
    return [
        {
            "text": doc,
            "source": meta["source"],
            "page": meta["page"],
            "version": meta["version"],
        }
        for doc, meta in zip(results["documents"], results["metadatas"])
    ]


def delete_by_source(collection_name: str, source: str) -> None:
    """Remove all chunks belonging to a specific source document."""
    collection = init_collection(collection_name)
    results = collection.get(where={"source": source})
    if results["ids"]:
        collection.delete(ids=results["ids"])


def query(collection_name: str, query_text: str, n_results: int = 5) -> list[dict]:
    collection = init_collection(collection_name)
    embedder = _get_embedder()
    embedding = embedder.encode([query_text], show_progress_bar=False).tolist()
    results = collection.query(
        query_embeddings=embedding,
        n_results=n_results,
        include=["documents", "metadatas", "distances"],
    )
    chunks = []
    for doc, meta, dist in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
    ):
        chunks.append(
            {
                "text": doc,
                "source": meta["source"],
                "page": meta["page"],
                "version": meta["version"],
                "score": round(1 - dist, 4),
            }
        )
    return chunks
