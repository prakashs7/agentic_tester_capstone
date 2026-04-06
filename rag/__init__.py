"""
RAG (Retrieval-Augmented Generation) pipeline package.
Handles PDF ingestion, text chunking, embedding, and semantic retrieval.
"""

from rag.pdf_loader import load_pdf, load_pdf_as_string
from rag.chunker import split_into_chunks
from rag.vector_store import VectorStore
