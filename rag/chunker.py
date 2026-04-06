"""
Text chunking for the RAG pipeline.
Splits large document text into smaller overlapping segments
that fit within embedding model context windows.
"""

from langchain.text_splitter import RecursiveCharacterTextSplitter
from config.settings import CHUNK_SIZE, CHUNK_OVERLAP


def split_into_chunks(text: str) -> list[str]:
    """
    Break the raw document text into overlapping chunks.
    Uses requirement-aware separators so that individual
    FR-* blocks stay together whenever possible.
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", "FR-", ". ", " "],
    )
    return splitter.split_text(text)
