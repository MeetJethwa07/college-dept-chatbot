from sentence_transformers import SentenceTransformer

# Load lightweight embedding model
model = SentenceTransformer("all-mpnet-base-v2")

def get_embedding(text):
    return model.encode(text).tolist()

# this converts text --> vector(384 dimensions)