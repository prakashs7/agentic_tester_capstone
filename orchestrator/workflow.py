"""
LangGraph workflow — wires Agent A, Agent B, and Agent C into a
state-machine with a conditional feedback loop.

Graph topology:

    ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
    │  Agent A     │────▶│  Agent B     │────▶│  Agent C     │
    │  (Parser)    │     │  (Synth.)    │     │  (Auditor)   │
    └─────────────┘     └──────▲──────┘     └──────┬──────┘
                               │    selective       │
                               │    re-gen          │ feedback
                               └────────────────────┘
                            (max 5 iterations)
"""

import os
from langgraph.graph import StateGraph, END
from langchain_groq import ChatGroq

from config.settings import (
    GROQ_API_KEY,
    LLM_MODEL,
    LLM_TEMPERATURE,
    MAX_ITERATIONS,
    OUTPUT_DIR,
)
from agents.agent_a_parser import SpecParserAgent
from agents.agent_b_synthesizer import TestSynthesizerAgent
from agents.agent_c_auditor import ComplianceAuditorAgent
from orchestrator.state import PipelineState


def build_pipeline():
    """Construct and compile the LangGraph state machine."""

    # ── LLM initialisation ───────────────────────────────────
    llm = ChatGroq(
        temperature=LLM_TEMPERATURE,
        model_name=LLM_MODEL,
        groq_api_key=GROQ_API_KEY,
    )

    # ── Agent instances ──────────────────────────────────────
    parser = SpecParserAgent(llm)
    synthesizer = TestSynthesizerAgent(llm)
    auditor = ComplianceAuditorAgent(llm)

    # ── Node functions ───────────────────────────────────────

    def parse_requirements(state: PipelineState) -> dict:
        """Node 1 — Agent A: extract testable requirements via RAG."""
        print("\n" + "=" * 60)
        print("  PHASE 1 : Agent A  —  Specification Parsing (RAG)")
        print("=" * 60)
        reqs = parser.run(state["pdf_path"], state["target_url"])
        return {"requirements": reqs}

    def generate_tests(state: PipelineState) -> dict:
        """Node 2 — Agent B: produce or patch Playwright tests."""
        iteration = state.get("iteration", 0) + 1
        print("\n" + "=" * 60)
        print(f"  PHASE 2 : Agent B  —  Test Synthesis  (iter {iteration}/{MAX_ITERATIONS})")
        print("=" * 60)

        # On the very first pass there is no existing code to patch
        existing = state.get("generated_code") if iteration > 1 else None
        failing = state.get("failing_req_ids") if iteration > 1 else None

        code = synthesizer.generate(
            requirements=state["requirements"],
            target_url=state["target_url"],
            existing_code=existing,
            failing_ids=failing,
        )
        return {"generated_code": code, "iteration": iteration}

    def audit_tests(state: PipelineState) -> dict:
        """Node 3 — Agent C: validate the generated tests."""
        print("\n" + "=" * 60)
        print(f"  PHASE 3 : Agent C  —  Compliance Audit  (iter {state['iteration']}/{MAX_ITERATIONS})")
        print("=" * 60)

        report = auditor.audit(
            code=state["generated_code"],
            requirements=state["requirements"],
            target_url=state["target_url"],
        )

        verdict = report.get("verdict", "FAIL")
        failing = report.get("failing_req_ids", [])
        done = verdict == "PASS" or state["iteration"] >= MAX_ITERATIONS

        return {
            "audit_report": report,
            "failing_req_ids": failing,
            "is_complete": done,
        }

    # ── Conditional edge ─────────────────────────────────────

    def should_continue(state: PipelineState) -> str:
        if state.get("is_complete", False):
            return "end"
        return "generate_tests"

    # ── Graph assembly ───────────────────────────────────────
    graph = StateGraph(PipelineState)

    graph.add_node("parse_requirements", parse_requirements)
    graph.add_node("generate_tests", generate_tests)
    graph.add_node("audit_tests", audit_tests)

    graph.set_entry_point("parse_requirements")
    graph.add_edge("parse_requirements", "generate_tests")
    graph.add_edge("generate_tests", "audit_tests")
    graph.add_conditional_edges(
        "audit_tests",
        should_continue,
        {"generate_tests": "generate_tests", "end": END},
    )

    return graph.compile()


# ── convenience runner ───────────────────────────────────────

def run_pipeline(pdf_path: str, target_url: str) -> dict:
    """Build the graph, execute it, and persist the final test file."""
    pipeline = build_pipeline()

    initial_state: PipelineState = {
        "pdf_path": pdf_path,
        "target_url": target_url,
        "requirements": [],
        "generated_code": "",
        "audit_report": {},
        "failing_req_ids": [],
        "iteration": 0,
        "is_complete": False,
    }

    result = pipeline.invoke(initial_state)

    # Persist the generated test script
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    output_path = os.path.join(OUTPUT_DIR, "generated_tests.py")
    with open(output_path, "w", encoding="utf-8") as fh:
        fh.write(result["generated_code"])
    print(f"\n  [Pipeline] Saved generated tests -> {output_path}")

    return result
