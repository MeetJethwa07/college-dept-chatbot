"""
ingest.py — Scrapes KJSIT website and loads into ChromaDB
"""

from scraper.scraper import crawl
from rag.vector_store import add_document, collection_size
import hashlib

BASE_URL   = "https://kjsit.somaiya.edu.in/en"
CHUNK_SIZE = 200
OVERLAP    = 40


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = OVERLAP) -> list[str]:
    """Word-level sliding window chunking with overlap."""
    words = text.split()
    chunks = []
    i = 0
    while i < len(words):
        chunks.append(" ".join(words[i : i + chunk_size]))
        i += chunk_size - overlap
    return chunks


def generate_id(text: str) -> str:
    return hashlib.md5(text.encode()).hexdigest()


def ingest_website():
    print("🚀 Starting KJSIT website ingestion...\n")
    pages = crawl(BASE_URL, max_depth=2, max_pages=80)

    added   = 0
    skipped = 0

    for url, page_text in pages:
        chunks = chunk_text(page_text)

        for chunk in chunks:
            stripped = chunk.strip()
            if len(stripped) < 60:
                skipped += 1
                continue

            doc_id = generate_id(stripped)
            add_document(doc_id, stripped, source_url=url)
            added += 1

    print(f"\n✅ Ingestion complete!")
    print(f"   Pages scraped : {len(pages)}")
    print(f"   Chunks added  : {added}")
    print(f"   Chunks skipped: {skipped}")
    print(f"   Total in DB   : {collection_size()}")


if __name__ == "__main__":
    ingest_website()