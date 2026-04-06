"""
ChromaDB-backed vector store for semantic search over SRS chunks.
Embeddings are computed locally with sentence-transformers so
no external API call is needed for this step.
"""

import chromadb
from sentence_transformers import SentenceTransformer
from config.settings import EMBEDDING_MODEL, CHROMA_COLLECTION


class VectorStore:
    """Thin wrapper around ChromaDB that handles embedding + retrieval."""

    def __init__(self):
        self.embedder = SentenceTransformer(EMBEDDING_MODEL)
        # in-memory client — no files written to disk
        self.client = chromadb.Client()
        self.collection = self.client.get_or_create_collection(
            name=CHROMA_COLLECTION,
            metadata={"hnsw:space": "cosine"},
        )

    # ── public API ───────────────────────────────────────────

    def add_chunks(self, chunks: list[str]) -> None:
        """Embed a list of text chunks and store them."""
        embeddings = self.embedder.encode(chunks).tolist()
        ids = [f"chunk_{i}" for i in range(len(chunks))]
        self.collection.add(
            documents=chunks,
            embeddings=embeddings,
            ids=ids,
        )

    def query(self, question: str, top_k: int = 5) -> list[str]:
        """Return the *top_k* most relevant chunks for *question*."""
        query_embedding = self.embedder.encode([question]).tolist()
        results = self.collection.query(
            query_embeddings=query_embedding,
            n_results=top_k,
        )
        if results["documents"]:
            return results["documents"][0]
        return []
