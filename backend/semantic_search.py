from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

# Load model once
model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
def create_embeddings(notes):
    """
    Creates embeddings for every note.
    """

    texts = [
        note["title"] + ". " + note["content"]
        for note in notes
    ]

    embeddings = model.encode(texts)

    return embeddings


def semantic_search(query, notes, embeddings, top_k=3):
    """
    Returns the top_k most similar notes.
    """

    query_embedding = model.encode([query])

    similarities = cosine_similarity(
        query_embedding,
        embeddings
    )[0]

    ranked = []
    for note, score in zip(notes, similarities):
        ranked.append({
            "title": note["title"],
            "content": note["content"],
            "score": round(float(score), 4)
        })

    ranked.sort(
        key=lambda x: x["score"],
        reverse=True
    )

    return ranked[:top_k]