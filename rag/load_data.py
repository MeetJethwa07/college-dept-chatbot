from rag.vector_store import add_document

def load_knowledge_file():
    with open("dept_knowledge.txt", "r", encoding="utf-8") as f:
        content = f.read()

    # Simple chunking
    chunks = content.split("\n\n")

    for i, chunk in enumerate(chunks):
        if chunk.strip():
            add_document(f"chunk_{i}", chunk)

    print("Knowledge loaded into vector DB!")

if __name__ == "__main__":
    load_knowledge_file()