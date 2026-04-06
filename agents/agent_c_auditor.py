"""
Agent C — Compliance Auditor
===============================
Receives the generated Playwright test code together with the original
requirements and performs a multi-point quality audit:

* Hallucination detection  — tests targeting non-existent pages/elements
* Missing coverage          — requirements with no corresponding test
* Edge-case verification    — negative scenarios handled?
* Syntax & import checks    — valid Python, correct Playwright imports
* Locator accuracy          — selectors matching the real site DOM

Returns a structured JSON report consumed by the orchestrator to decide
whether to loop back to Agent B or terminate the pipeline.
"""

import json


class ComplianceAuditorAgent:
    """Audits generated test code for correctness, coverage, and quality."""

    def __init__(self, llm):
        self.llm = llm

    # ── public entry point ───────────────────────────────────

    def audit(self, code: str, requirements: list[dict], target_url: str) -> dict:
        """Run the full audit and return a structured report dict."""
        print(f"  [Agent C] Auditing code against {len(requirements)} requirements ...")

        req_block = self._format_requirements(requirements)

        prompt = f"""You are a Senior QA Auditor. Examine the Playwright test code and compare it against the requirements below.

REQUIREMENTS:
{req_block}

TARGET URL: {target_url}

CODE TO AUDIT:
{code}

AUDIT CHECKLIST (check every point):
1. HALLUCINATION — Does the code reference pages or elements that do NOT exist on the target site?
2. MISSING TESTS — Are there requirements with no corresponding test function?
3. EDGE CASES   — Are negative scenarios handled (wrong creds, empty forms, etc.)?
4. COVERAGE     — What fraction of requirements has a matching test?
5. SYNTAX       — Is the code valid Python?  Proper indentation?
6. LOCATORS     — Do CSS / XPath selectors match the real site DOM?
7. IMPORTS      — Must use 'from playwright.sync_api import sync_playwright, expect'.
8. NO FLASK     — Code must NOT import Flask or build a web server.
9. ASSERTIONS   — Every test function must contain at least one expect() call.

RESPOND WITH A SINGLE JSON OBJECT (no markdown, no extra text):
{{
    "verdict": "PASS" or "FAIL",
    "coverage_pct": <integer 0-100>,
    "total_requirements": <int>,
    "covered_requirements": <int>,
    "issues": [
        {{
            "req_id": "<requirement ID or GENERAL>",
            "issue_type": "<hallucination|missing|edge_case|syntax|locator|import>",
            "description": "<specific problem>",
            "severity": "HIGH" or "MEDIUM" or "LOW"
        }}
    ],
    "failing_req_ids": ["<IDs that need re-generation>"],
    "summary": "<one-line summary>"
}}

Return ONLY the JSON object."""

        response = self.llm.invoke(prompt)
        content = response.content if hasattr(response, "content") else str(response)

        report = self._parse_audit_response(content)
        self._print_report(report)
        return report

    # ── JSON parsing ─────────────────────────────────────────

    @staticmethod
    def _parse_audit_response(text: str) -> dict:
        text = text.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1]
        if text.endswith("```"):
            text = text.rsplit("```", 1)[0]
        text = text.strip()

        try:
            return json.loads(text)
        except json.JSONDecodeError:
            start = text.find("{")
            end = text.rfind("}") + 1
            if start != -1 and end > start:
                try:
                    return json.loads(text[start:end])
                except json.JSONDecodeError:
                    pass
            return {
                "verdict": "FAIL",
                "coverage_pct": 0,
                "issues": [
                    {
                        "req_id": "PARSE_ERROR",
                        "issue_type": "syntax",
                        "description": "Could not parse audit response from LLM",
                        "severity": "HIGH",
                    }
                ],
                "failing_req_ids": [],
                "summary": "Audit response was unparseable — will retry",
            }

    # ── pretty-print ─────────────────────────────────────────

    @staticmethod
    def _print_report(report: dict) -> None:
        verdict = report.get("verdict", "UNKNOWN")
        icon = "PASS" if verdict == "PASS" else "FAIL"

        print(f"\n  {'='*56}")
        print(f"   [{icon}]  AUDIT VERDICT: {verdict}")
        print(f"  {'='*56}")
        print(f"   Coverage : {report.get('coverage_pct', '?')}%")
        print(f"   Summary  : {report.get('summary', 'N/A')}")

        issues = report.get("issues", [])
        if issues:
            print(f"\n   Issues ({len(issues)}):")
            for issue in issues:
                sev = issue.get("severity", "?")
                tag = "[HIGH]" if sev == "HIGH" else "[MED] " if sev == "MEDIUM" else "[LOW] "
                print(f"     {tag} [{issue.get('req_id')}] {issue.get('description')}")

        failing = report.get("failing_req_ids", [])
        if failing:
            print(f"\n   Queued for re-generation: {', '.join(failing)}")

        print(f"  {'='*56}\n")

    # ── helpers ──────────────────────────────────────────────

    @staticmethod
    def _format_requirements(requirements: list[dict]) -> str:
        lines = []
        for r in requirements:
            lines.append(
                f"- {r.get('req_id')}: {r.get('description', '')} "
                f"(Path: {r.get('url_path', '/')})"
            )
        return "\n".join(lines)
