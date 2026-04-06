"""
Agent A — Specification Parser
================================
Reads an SRS PDF, embeds its content into a vector store via the RAG
pipeline, then uses targeted semantic queries to extract structured,
testable requirements that downstream agents can act on.
"""

import json
from rag.pdf_loader import load_pdf_as_string
from rag.chunker import split_into_chunks
from rag.vector_store import VectorStore


class SpecParserAgent:
    """Extracts structured requirements from an SRS PDF using RAG."""

    def __init__(self, llm):
        self.llm = llm
        self.vector_store = VectorStore()

    # ── public entry point ───────────────────────────────────

    def run(self, pdf_path: str, target_url: str) -> list[dict]:
        """
        Full pipeline:
        1. Load PDF text
        2. Chunk and embed into ChromaDB
        3. Retrieve relevant chunks per query
        4. Ask the LLM to structure them as testable requirements
        """
        print("\n  [Agent A] Reading PDF and building vector index ...")
        raw_text = load_pdf_as_string(pdf_path)
        chunks = split_into_chunks(raw_text)
        self.vector_store.add_chunks(chunks)
        print(f"  [Agent A] Indexed {len(chunks)} chunks into ChromaDB")

        print("  [Agent A] Querying vector store for functional requirements ...")
        requirements = self._extract_requirements(target_url)
        print(f"  [Agent A] Extracted {len(requirements)} testable requirements\n")
        return requirements

    # ── internal helpers ─────────────────────────────────────

    def _extract_requirements(self, target_url: str) -> list[dict]:
        """Retrieve relevant SRS chunks and ask the LLM to structure them."""

        # Pull the most relevant chunks about functional requirements
        search_queries = [
            "functional requirements checkboxes login form authentication",
            "file upload drag and drop dropdown list javascript alerts",
            "expected behavior user actions validation error handling",
            "add remove elements hovers dynamic controls test cases",
        ]
        all_chunks: list[str] = []
        for q in search_queries:
            hits = self.vector_store.query(q, top_k=4)
            all_chunks.extend(hits)

        # Deduplicate while preserving order
        seen = set()
        unique_chunks = []
        for c in all_chunks:
            if c not in seen:
                seen.add(c)
                unique_chunks.append(c)

        context = "\n---\n".join(unique_chunks)

        prompt = (
            "You are a Requirements Engineer. Analyze the following SRS excerpts "
            "and extract ALL testable functional requirements.\n\n"
            f"SRS CONTEXT:\n{context}\n\n"
            f"TARGET URL: {target_url}\n\n"
            "Return a JSON array. Each element must have:\n"
            '  - "req_id"   : the requirement ID (e.g. "FR-CB-01")\n'
            '  - "feature"  : the feature name (e.g. "Checkboxes")\n'
            '  - "url_path" : the page path (e.g. "/checkboxes")\n'
            '  - "description" : what to test\n'
            '  - "expected_behavior" : what the test should assert\n\n'
            "RULES:\n"
            "- Include requirements for: Checkboxes, Login, Dropdown, "
            "File Upload, JavaScript Alerts, Add/Remove Elements, Hovers, Drag and Drop.\n"
            "- Each requirement must be independently testable with Playwright.\n"
            "- Return ONLY valid JSON. No markdown fences, no explanations.\n"
        )

        response = self.llm.invoke(prompt)
        content = response.content if hasattr(response, "content") else str(response)
        return self._parse_json_response(content)

    @staticmethod
    def _parse_json_response(text: str) -> list[dict]:
        """Best-effort JSON extraction from LLM output."""
        text = text.strip()

        # Strip markdown code fences if the model wrapped its response
        if text.startswith("```"):
            text = text.split("\n", 1)[1]
        if text.endswith("```"):
            text = text.rsplit("```", 1)[0]
        text = text.strip()

        try:
            data = json.loads(text)
            return data if isinstance(data, list) else []
        except json.JSONDecodeError:
            # Fallback: locate the outermost JSON array
            start = text.find("[")
            end = text.rfind("]") + 1
            if start != -1 and end > start:
                try:
                    return json.loads(text[start:end])
                except json.JSONDecodeError:
                    pass
            print("  [Agent A] ⚠ Could not parse LLM response as JSON")
            return []
