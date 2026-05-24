"""
load_data.py — Loads dept_knowledge.txt into ChromaDB
"""

import sys
from rag.vector_store import add_document, collection_size, delete_documents_by_prefix

SOURCE_LABEL = "dept_knowledge.txt"
CHUNK_SIZE   = 60
OVERLAP      = 10


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = OVERLAP) -> list[str]:
    words = text.split()
    chunks = []
    i = 0
    while i < len(words):
        chunk = " ".join(words[i : i + chunk_size])
        chunks.append(chunk)
        i += chunk_size - overlap
    return chunks


def load_knowledge_file(filepath: str = "dept_knowledge.txt", force: bool = False) -> None:

    if force:
        print("🗑️  Force mode: deleting old dept_knowledge chunks...")
        deleted = delete_documents_by_prefix("dept_chunk_")
        print(f"   Deleted {deleted} old chunks.")

    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    chunks = chunk_text(content)
    added   = 0
    skipped = 0

    for i, chunk in enumerate(chunks):
        if len(chunk.strip()) < 40:
            skipped += 1
            continue
        add_document(
            doc_id=f"dept_chunk_{i}",
            text=chunk,
            source_url=SOURCE_LABEL,
        )
        added += 1

    print(f"✅ Knowledge loaded: {added} chunks added, {skipped} skipped.")
    print(f"   Total docs in vector DB: {collection_size()}")


if __name__ == "__main__":
    # Run with: python -m rag.load_data --force
    force = "--force" in sys.argv
    load_knowledge_file(force=force)