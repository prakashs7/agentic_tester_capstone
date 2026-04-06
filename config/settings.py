"""
Centralized configuration for the Agentic AI Tester pipeline.
All tunable parameters live here so they are easy to find and modify.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ── LLM Settings ─────────────────────────────────────────────
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
LLM_MODEL = "llama-3.3-70b-versatile"
LLM_TEMPERATURE = 0        # deterministic output for reproducibility

# ── RAG / Embedding Settings ─────────────────────────────────
EMBEDDING_MODEL = "all-MiniLM-L6-v2"   # runs locally, ~80 MB on first download
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50
CHROMA_COLLECTION = "srs_requirements"

# ── Pipeline Settings ────────────────────────────────────────
MAX_ITERATIONS = 5          # upper bound on Agent B ↔ C feedback loops
DEFAULT_TARGET_URL = "https://the-internet.herokuapp.com/"
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "output")
SPECS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "specs")
