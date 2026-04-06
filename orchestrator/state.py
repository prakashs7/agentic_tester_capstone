"""
Pipeline state definition.
This TypedDict is the single shared data structure that flows between
every node in the LangGraph state machine.
"""

from typing import TypedDict


class PipelineState(TypedDict):
    pdf_path: str              # filesystem path to the SRS PDF
    target_url: str            # base URL of the site under test
    requirements: list         # structured requirements from Agent A
    generated_code: str        # current Playwright test script
    audit_report: dict         # most recent Agent C report
    failing_req_ids: list      # requirement IDs that need fixing
    iteration: int             # current feedback-loop counter
    is_complete: bool          # True when audit passes or max iters hit
