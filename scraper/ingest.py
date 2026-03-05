from scraper.scraper import crawl
from rag.vector_store import add_document
import hashlib
import re

BASE_URL = "https://kjsit.somaiya.edu.in/en"


def chunk_text(text, chunk_size=80):
    sentences = re.split(r'(?<=[.!?]) +', text)
    chunks = []
    current_chunk = []

    word_count = 0

    for sentence in sentences:
        words = sentence.split()
        word_count += len(words)
        current_chunk.append(sentence)

        if word_count >= chunk_size:
            chunks.append(" ".join(current_chunk))
            current_chunk = []
            word_count = 0

    if current_chunk:
        chunks.append(" ".join(current_chunk))

    return chunks


def generate_id(text):
    return hashlib.md5(text.encode()).hexdigest()


def ingest_website():
    pages = crawl(BASE_URL, max_depth=2)

    for url, page_text in pages:
        chunks = chunk_text(page_text)

        for chunk in chunks:
            doc_id = generate_id(chunk)
            add_document(doc_id, chunk, url)

    print("Website content ingested into vector DB!")


if __name__ == "__main__":
    ingest_website()