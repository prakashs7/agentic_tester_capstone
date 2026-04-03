import os
from dotenv import load_dotenv
from langgraph.graph import StateGraph, END
from typing import TypedDict, List

# Import your independent agents
from extractor_agent import RequirementExtractor
from generator_agent import CodeGenerator
from auditor_agent import QualityAuditor

# Load API Key from .env
load_dotenv()

# 1. Initialize Google Gemini Model
from langchain_groq import ChatGroq

# Initialize an open-source model (Llama 3 is highly recommended for coding)
llm = ChatGroq(
    temperature=0, 
    model_name="openai/gpt-oss-120b",
    groq_api_key=os.getenv("GROQ_API_KEY")
)
# 2. Setup Independent Agents
extractor = RequirementExtractor(llm) # Agent A
generator = CodeGenerator(llm)       # Agent B
auditor = QualityAuditor(llm)         # Agent C

# 3. Define State and Workflow
class AgentState(TypedDict):
    requirements: List[str]
    code: str
    report: str
    iterations: int

workflow = StateGraph(AgentState)

# Agent B Logic (Generator)
workflow.add_node("Generator", lambda state: {
    "code": generator.generate(state['requirements'], state.get('report')),
    "iterations": state.get('iterations', 0) + 1
})

# Agent C Logic (Auditor)
workflow.add_node("Auditor", lambda state: {
    "report": auditor.verify(state['code'], state['requirements'])
})

# Loop Logic: Max 5 attempts 
def check_completion(state):
    if "CONFIRMED" in state['report'] or state['iterations'] >= 5:
        return END
    return "Generator"

workflow.set_entry_point("Generator")
workflow.add_edge("Generator", "Auditor")
workflow.add_conditional_edges("Auditor", check_completion)

app = workflow.compile()

# 4. Run Execution
if __name__ == "__main__":
    pdf_path = "SpecificationDoc.pdf"
    
    print("--- Phase 1: Agent A Extracting from PDF ---")
    extracted_data = extractor.run(pdf_path) 
    
    initial_input = {
        "requirements": extracted_data,
        "iterations": 0
    }
    
    print("--- Phase 2: Agent B & C Feedback Loop ---")
    result = app.invoke(initial_input)
    
    print(f"\nCompleted in {result['iterations']} iterations.")
    print("Final Code Generated in: playwright_test.py")
    
    with open("playwright_test.py", "w", encoding="utf-8") as f:
        code_content = result['code'].content if hasattr(result['code'], 'content') else result['code']
        clean_code = code_content.replace('“', '"').replace('”', '"').replace('‘', "'").replace('’', "'")
        f.write(clean_code)