"""
Agent B — Test Synthesizer
============================
Generates executable Playwright Python test scripts from structured
requirements.  Supports two modes:

1. **Full generation**  — first iteration; builds the complete script.
2. **Selective re-generation** — subsequent iterations; rewrites only
   the test methods that Agent C flagged as failing or missing, then
   merges them back into the existing script.
"""

import re


class TestSynthesizerAgent:
    """Generates (or patches) Playwright test code from requirements."""

    def __init__(self, llm):
        self.llm = llm

    # ── public entry point ───────────────────────────────────

    def generate(
        self,
        requirements: list[dict],
        target_url: str,
        existing_code: str = None,
        failing_ids: list[str] = None,
    ) -> str:
        """
        If *existing_code* and *failing_ids* are provided, re-generate
        only the failing test methods and merge them into the existing
        code. Otherwise, produce a brand-new script from scratch.
        """
        if existing_code and failing_ids:
            print(f"  [Agent B] Selective re-gen for {len(failing_ids)} failing tests ...")
            return self._selective_regen(
                requirements, target_url, existing_code, failing_ids
            )

        print(f"  [Agent B] Generating full test suite ({len(requirements)} requirements) ...")
        return self._full_generation(requirements, target_url)

    # ── full generation (first pass) ─────────────────────────

    def _full_generation(self, requirements: list[dict], target_url: str) -> str:
        req_block = self._format_requirements(requirements)

        prompt = f"""You are a Playwright Automation Expert writing Python test scripts.

REQUIREMENTS TO TEST:
{req_block}

TARGET URL: {target_url}

STRICT RULES — follow every single one:
1. First line of code MUST be: from playwright.sync_api import sync_playwright, expect
2. Also import: from pathlib import Path  (for the file-upload test)
3. Write ONE function per requirement, named  test_<req_id>
   where req_id is lowercased and hyphens become underscores.
   Example: def test_fr_cb_01(page):
4. Put a comment  # TEST: <REQ_ID>  as the first line inside each function.
5. Use correct CSS selectors / locators that match the real site.
6. Include at least one expect() assertion per function.
7. For JS alerts use  page.on("dialog", lambda d: d.accept())  BEFORE the click.
8. For file upload create a temp file with Path, upload it, then delete it.
9. For checkbox assertions use expect(cb).to_be_checked() or .not_to_be_checked().
10. Write a  run_all()  function that launches the browser, creates a page,
    calls every test_* function in sequence, and closes the browser in a
    finally block.
11. End with:  if __name__ == "__main__": run_all()
12. Output ONLY raw Python code.  NO markdown fences, NO explanations.
13. NEVER use Flask.  NEVER build a web server.

Write the complete, executable test script now:"""

        response = self.llm.invoke(prompt)
        code = response.content if hasattr(response, "content") else str(response)
        return self._clean_code(code)

    # ── selective re-generation (subsequent passes) ──────────

    def _selective_regen(
        self,
        requirements: list[dict],
        target_url: str,
        existing_code: str,
        failing_ids: list[str],
    ) -> str:
        failing_reqs = [r for r in requirements if r.get("req_id") in failing_ids]
        if not failing_reqs:
            return existing_code

        req_block = self._format_requirements(failing_reqs)

        prompt = f"""You are a Playwright Automation Expert. Fix ONLY the following failing test functions.

FAILING REQUIREMENTS:
{req_block}

TARGET URL: {target_url}

EXISTING CODE (for context — do NOT rewrite everything):
{existing_code[:2000]}

RULES:
1. Write ONLY the replacement test functions — nothing else.
2. Keep the naming convention:  def test_<req_id>(page):
3. Keep the comment  # TEST: <REQ_ID>  as the first line.
4. Use correct locators that match the real site elements.
5. Include expect() assertions.
6. Output ONLY raw Python code — NO markdown fences.

Write the fixed test functions now:"""

        response = self.llm.invoke(prompt)
        new_methods = response.content if hasattr(response, "content") else str(response)
        new_methods = self._clean_code(new_methods)
        return self._merge_methods(existing_code, new_methods, failing_ids)

    # ── merge logic ──────────────────────────────────────────

    @staticmethod
    def _merge_methods(
        existing_code: str, new_methods: str, failing_ids: list[str]
    ) -> str:
        """
        For each failing requirement ID, find the corresponding function
        in *existing_code* and replace it with the version from *new_methods*.
        """
        updated = existing_code

        for req_id in failing_ids:
            fn_name = "test_" + req_id.lower().replace("-", "_")

            # Regex capturing a full function body (up to the next def / end)
            old_pat = re.compile(
                rf"(def {fn_name}\(.*?\):.*?)(?=\ndef |\Z)", re.DOTALL
            )
            new_pat = re.compile(
                rf"(def {fn_name}\(.*?\):.*?)(?=\ndef |\Z)", re.DOTALL
            )

            new_match = new_pat.search(new_methods)
            if new_match:
                old_match = old_pat.search(updated)
                if old_match:
                    updated = (
                        updated[: old_match.start()]
                        + new_match.group(0)
                        + updated[old_match.end() :]
                    )

        return updated

    # ── formatting helpers ───────────────────────────────────

    @staticmethod
    def _format_requirements(requirements: list[dict]) -> str:
        lines = []
        for r in requirements:
            lines.append(
                f"- {r.get('req_id', 'N/A')}: [{r.get('feature', '')}] "
                f"Path: {r.get('url_path', '/')} | "
                f"{r.get('description', '')} -> "
                f"Expected: {r.get('expected_behavior', '')}"
            )
        return "\n".join(lines)

    @staticmethod
    def _clean_code(code: str) -> str:
        """Strip markdown fences and fix curly/smart quotes."""
        code = code.strip()
        if code.startswith("```python"):
            code = code[len("```python") :]
        elif code.startswith("```"):
            code = code[3:]
        if code.endswith("```"):
            code = code[:-3]

        replacements = {
            "\u201c": '"', "\u201d": '"',   # smart double quotes
            "\u2018": "'", "\u2019": "'",   # smart single quotes
        }
        for old, new in replacements.items():
            code = code.replace(old, new)

        return code.strip()
