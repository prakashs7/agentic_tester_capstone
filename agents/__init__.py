"""
Agents package — houses the three core agents of the pipeline.

* Agent A  →  SpecParserAgent        (specification parsing via RAG)
* Agent B  →  TestSynthesizerAgent   (Playwright code generation)
* Agent C  →  ComplianceAuditorAgent (quality & coverage auditing)
"""

from agents.agent_a_parser import SpecParserAgent
from agents.agent_b_synthesizer import TestSynthesizerAgent
from agents.agent_c_auditor import ComplianceAuditorAgent
