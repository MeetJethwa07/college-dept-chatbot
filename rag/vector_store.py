"""
vector_store.py — ChromaDB wrapper for KJSIT Chatbot
"""

import chromadb
from rag.embedder import get_embedding

# ── Client setup ──────────────────────────────────────────────────────────────
client = chromadb.PersistentClient(path="./chroma_db")

collection = client.get_or_create_collection(
    name="college_knowledge",
    metadata={"hnsw:space": "cosine"},   # explicitly use cosine similarity
)
# ─────────────────────────────────────────────────────────────────────────────


def add_document(doc_id: str, text: str, source_url: str = "") -> None:
    """Add a document chunk. Skips silently if doc_id already exists."""
    existing = collection.get(ids=[doc_id])
    if existing and existing["ids"]:
        return

    embedding = get_embedding(text)
    collection.add(
        ids=[doc_id],
        documents=[text],
        embeddings=[embedding],
        metadatas=[{"source": source_url}],
    )


def query_documents_with_scores(query: str, top_k: int = 8) -> list[tuple[str, dict, float]]:
    """
    Returns [(document, metadata, distance), ...] sorted by distance ascending.
    Distance is cosine distance: 0.0 = identical, 2.0 = opposite.
    """
    if collection.count() == 0:
        return []

    safe_k = min(top_k, collection.count())

    embedding = get_embedding(query)
    results = collection.query(
        query_embeddings=[embedding],
        n_results=safe_k,
        include=["documents", "metadatas", "distances"],
    )

    if not results or not results["documents"] or not results["documents"][0]:
        return []

    documents = results["documents"][0]
    metadatas = results["metadatas"][0]
    distances = results["distances"][0]

    return list(zip(documents, metadatas, distances))


def query_documents(query: str, top_k: int = 5) -> list[tuple[str, dict]]:
    """Backward-compatible wrapper. Returns [(document, metadata), ...]."""
    results = query_documents_with_scores(query, top_k=top_k)
    return [(doc, meta) for doc, meta, _ in results]


def collection_size() -> int:
    """How many chunks are stored?"""
    return collection.count()

def delete_documents_by_prefix(prefix: str) -> int:
    """
    Deletes all documents whose ID starts with the given prefix.
    Returns the number of deleted documents.
    """
    try:
        all_ids = collection.get()["ids"]
        to_delete = [id for id in all_ids if id.startswith(prefix)]
        if to_delete:
            collection.delete(ids=to_delete)
        return len(to_delete)
    except Exception as e:
        print(f"  ⚠️ Delete error: {e}")
        return 0