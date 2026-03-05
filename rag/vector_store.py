import chromadb
from chromadb.config import Settings
from rag.embedder import get_embedding

# Proper persistent client
client = chromadb.Client(
    Settings(
        persist_directory="./chroma_db",
        is_persistent=True
    )
)

collection = client.get_or_create_collection(
    name="college_knowledge"
)

def add_document(doc_id, text, source_url):
    embedding = get_embedding(text)
    collection.add(
        ids=[doc_id],
        documents=[text],
        embeddings=[embedding],
        metadatas=[{"source": source_url}]
    )

def query_documents(query, top_k=3):
    embedding = get_embedding(query)
    results = collection.query(
        query_embeddings=[embedding],
        n_results=top_k
    )

    if results and results["documents"]:
        documents = results["documents"][0]
        metadatas = results["metadatas"][0]
        return list(zip(documents, metadatas))

    return []