# Agentic AI Tester

> Multi-agent system that reads an SRS document, extracts testable requirements,
> generates executable Playwright test scripts, and iteratively refines them
> through an AI-powered quality audit loop.

---

## Architecture

```
                    ┌────────────────────────────────┐
                    │         main.py (CLI)           │
                    │   --pdf  specs/SRS.pdf          │
                    │   --url  https://site.com/      │
                    └───────────────┬────────────────┘
                                    │
                    ┌───────────────▼────────────────┐
                    │     LangGraph State Machine     │
                    │                                 │
                    │  ┌─────────┐    ┌──────────┐   │
                    │  │ Agent A │───►│ Agent B  │   │
                    │  │ Parser  │    │ Synth.   │   │
                    │  └─────────┘    └────┬─────┘   │
                    │                      │         │
                    │                      ▼         │
                    │                 ┌──────────┐   │
                    │                 │ Agent C  │   │
                    │                 │ Auditor  │   │
                    │                 └────┬─────┘   │
                    │                      │         │
                    │          ┌───────────┴───┐     │
                    │          │  PASS?        │     │
                    │          │  or iter ≥ 5? │     │
                    │          └───┬───────┬───┘     │
                    │           No │       │ Yes     │
                    │              ▼       ▼         │
                    │         Agent B     END        │
                    │        (selective              │
                    │         re-gen)                │
                    └────────────────────────────────┘
                                    │
                    ┌───────────────▼────────────────┐
                    │   output/generated_tests.py     │
                    └────────────────────────────────┘
```

---

## Agents

### Agent A — Specification Parser

| Property       | Details                                        |
|----------------|------------------------------------------------|
| **Input**      | SRS PDF document                               |
| **Technique**  | RAG (Retrieval-Augmented Generation)           |
| **Embedding**  | `all-MiniLM-L6-v2` via sentence-transformers   |
| **Vector DB**  | ChromaDB (in-memory, cosine similarity)        |
| **Output**     | Structured JSON list of testable requirements  |

Agent A reads the PDF, splits it into overlapping text chunks, embeds them
into ChromaDB, then retrieves the most relevant fragments to feed to the LLM.
The LLM structures these into a list of requirements, each with:

- `req_id` — e.g. `FR-CB-01`
- `feature` — e.g. Checkboxes
- `url_path` — e.g. `/checkboxes`
- `description` — what to test
- `expected_behavior` — what to assert

### Agent B — Test Synthesizer

| Property       | Details                                         |
|----------------|-------------------------------------------------|
| **Input**      | Requirements list + optional audit feedback     |
| **LLM**        | Groq — Llama 3.3 70B                           |
| **Output**     | Executable Playwright Python test script        |
| **Key feature**| **Selective re-generation** — only patches tests|
|                | that Agent C flagged as failing                 |

On the first pass Agent B generates the complete test script. On subsequent
passes it receives the list of `failing_req_ids` from Agent C and regenerates
**only** those specific test functions, merging them back into the existing
code via regex-based function replacement.

### Agent C — Compliance Auditor

| Property       | Details                                      |
|----------------|----------------------------------------------|
| **Input**      | Generated code + original requirements       |
| **Checks**     | Hallucination, missing coverage, edge cases, |
|                | syntax, locator accuracy, imports            |
| **Output**     | Structured JSON audit report                 |
| **Verdict**    | `PASS` → pipeline ends, `FAIL` → loop back  |

---

## RAG Pipeline

```
┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
│  PDF     │────►│ Chunker  │────►│ Embedder │────►│ ChromaDB │
│  Loader  │     │ (500char │     │ MiniLM   │     │ (cosine) │
│          │     │  overlap │     │ L6-v2    │     │          │
└──────────┘     │  50char) │     └──────────┘     └────┬─────┘
                 └──────────┘                           │
                                                        │ query
                                                        ▼
                                                  ┌──────────┐
                                                  │ Relevant │
                                                  │ Chunks   │
                                                  └──────────┘
```

---

## Project Structure

```
capstone/
├── agents/
│   ├── __init__.py
│   ├── agent_a_parser.py         # Specification Parser (RAG)
│   ├── agent_b_synthesizer.py    # Playwright Code Generator
│   └── agent_c_auditor.py        # Quality Auditor
├── rag/
│   ├── __init__.py
│   ├── pdf_loader.py             # PDF text extraction
│   ├── chunker.py                # Text chunking
│   └── vector_store.py           # ChromaDB + embeddings
├── orchestrator/
│   ├── __init__.py
│   ├── state.py                  # PipelineState TypedDict
│   └── workflow.py               # LangGraph wiring
├── config/
│   └── settings.py               # All tunable parameters
├── specs/
│   └── SpecificationDoc.pdf      # Input SRS document
├── output/
│   └── generated_tests.py        # Generated Playwright tests
├── main.py                       # CLI entry point
├── requirements.txt
├── .env                          # GROQ_API_KEY (not committed)
├── .env.example
├── .gitignore
└── README.md                     # This file
```

---

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/prakashs7/agentic_tester_capstone.git
cd agentic_tester_capstone
```

### 2. Create virtual environment

```bash
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS / Linux
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
playwright install chromium
```

### 4. Set your API key

```bash
copy .env.example .env
# Edit .env and paste your Groq API key
```

Get a free API key at [console.groq.com/keys](https://console.groq.com/keys).

---

## Usage

### Run with default SRS and target URL

```bash
python main.py
```

### Run with a different SRS document

```bash
python main.py --pdf specs/AnotherSRS.pdf --url https://example.com/
```

### Run the generated tests

```bash
python output/generated_tests.py
```

---

## How It Works

1. **Agent A** reads the SRS PDF → chunks → embeds into ChromaDB →
   retrieves relevant sections → LLM structures them into testable requirements.

2. **Agent B** receives the requirements → generates a complete Playwright
   Python test script with one function per requirement.

3. **Agent C** audits the code for hallucination, missing tests, edge cases,
   syntax errors, and locator accuracy → produces a structured audit report.

4. If the audit **fails**, Agent C sends the list of failing requirement IDs
   back to Agent B, which **selectively re-generates** only those test
   functions (not the entire script).

5. Steps 2–4 repeat up to **5 times** or until the audit passes.

6. The final test script is saved to `output/generated_tests.py`.

---

## Tech Stack

| Component            | Technology                          |
|----------------------|-------------------------------------|
| Framework            | LangGraph (state machine)           |
| LLM                  | Groq — Llama 3.3 70B Versatile     |
| Embeddings           | sentence-transformers (MiniLM-L6)   |
| Vector Store         | ChromaDB (in-memory)                |
| PDF Parsing          | pypdf                               |
| Test Framework       | Playwright (sync API)               |
| Language             | Python 3.10+                        |

---

## Configuration

All settings are in `config/settings.py`:

| Setting              | Default                                  | Description                       |
|----------------------|------------------------------------------|-----------------------------------|
| `LLM_MODEL`          | `llama-3.3-70b-versatile`               | Groq model name                   |
| `LLM_TEMPERATURE`    | `0`                                      | Deterministic output              |
| `EMBEDDING_MODEL`    | `all-MiniLM-L6-v2`                      | Local embedding model             |
| `MAX_ITERATIONS`     | `5`                                      | Max feedback loop iterations      |
| `CHUNK_SIZE`         | `500`                                    | RAG text chunk size               |
| `CHUNK_OVERLAP`      | `50`                                     | Overlap between chunks            |
| `DEFAULT_TARGET_URL` | `https://the-internet.herokuapp.com/`    | Default site to test              |

---

## License

This project is part of a capstone submission and is not licensed for
commercial redistribution.
