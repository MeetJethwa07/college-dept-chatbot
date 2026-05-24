"""
retriever.py — Production-grade RAG retrieval layer for KJSIT Chatbot
"""
 
from rag.vector_store import query_documents_with_scores
 
# ── Tuning knobs ──────────────────────────────────────────────────────────────
MAX_DISTANCE      = 0.80   # Cosine distance threshold
TOP_K_RETURN      = 3      # Final number of chunks to return to LLM
MIN_CHUNK_CHARS   = 60     # Skip chunks that are too short to be meaningful
DEDUP_SIMILARITY  = 0.92   # If two chunks share >92% of words, drop the lower-scored one
DEPT_KNOWLEDGE_BOOST = 0.35  # Subtract from distance for dept_knowledge chunks
# ─────────────────────────────────────────────────────────────────────────────
 
 
def _is_dept_knowledge(meta: dict) -> bool:
    source = meta.get("source", "")
    return "dept_knowledge" in source.lower()
 
 
def _jaccard_similarity(text_a: str, text_b: str) -> float:
    set_a = set(text_a.lower().split())
    set_b = set(text_b.lower().split())
    if not set_a or not set_b:
        return 0.0
    return len(set_a & set_b) / len(set_a | set_b)
 
 
def _deduplicate(chunks):
    kept = []
    for doc, meta, score in chunks:
        is_dup = any(
            _jaccard_similarity(doc, existing_doc) >= DEDUP_SIMILARITY
            for existing_doc, _, _ in kept
        )
        if not is_dup:
            kept.append((doc, meta, score))
    return kept
 
 
def retrieve(query: str):
    if not query or not query.strip():
        return []
 
    # Step 1: Fetch a large pool — enough to always include dept_knowledge chunks
    all_results = query_documents_with_scores(query, top_k=50)
    if not all_results:
        return []
 
    # Step 2: Separate dept_knowledge vs website chunks
    dept_chunks    = [(doc, meta, dist) for doc, meta, dist in all_results if _is_dept_knowledge(meta)]
    website_chunks = [(doc, meta, dist) for doc, meta, dist in all_results if not _is_dept_knowledge(meta)]
 
    # Step 3: Always take top 2 dept_knowledge chunks if they exist
    top_dept = dept_chunks[:2]
 
    # Step 4: Fill remaining slots with website chunks
    combined = top_dept + website_chunks
 
    # Step 5: Filter by distance and min length
    filtered = [
        (doc, meta, dist)
        for doc, meta, dist in combined
        if dist <= MAX_DISTANCE and len(doc.strip()) >= MIN_CHUNK_CHARS
    ]
 
    if not filtered:
        return []
 
    # Step 6: Apply boost to dept_knowledge chunks so they rank first
    boosted = []
    for doc, meta, dist in filtered:
        if _is_dept_knowledge(meta):
            dist = max(0.0, dist - DEPT_KNOWLEDGE_BOOST)
        boosted.append((doc, meta, dist))
 
    # Step 7: Sort best-first
    boosted.sort(key=lambda x: x[2])
 
    # Step 8: Deduplicate
    deduped = _deduplicate(boosted)
 
    # Step 9: Convert distance to relevance score
    final = []
    for doc, meta, dist in deduped[:TOP_K_RETURN]:
        relevance = round(1.0 - (dist / 2.0), 4)
        final.append((doc, meta, relevance))
 
    return final
 
 
def retrieve_as_context(query: str, max_chars_per_chunk: int = 1800) -> str:
    results = retrieve(query)
    if not results:
        return ""
 
    chunks = []
    seen_sources = set()
 
    for doc, meta, score in results:
        source = meta.get("source", "unknown")
        trimmed = doc[:max_chars_per_chunk].strip()
        label = f"[Source: {source} | Relevance: {score:.2f}]"
 
        if source not in seen_sources:
            chunks.append(f"{label}\n{trimmed}")
            seen_sources.add(source)
 
    return "\n\n---\n\n".join(chunks)
 
 
def retrieve_source_urls(query: str) -> list[str]:
    results = retrieve(query)
    seen = []
    for _, meta, _ in results:
        url = meta.get("source", "")
        if url and url not in seen:
            seen.append(url)
    return seen
 