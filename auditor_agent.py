class QualityAuditor:
    def __init__(self, model):
        self.model = model

    def verify(self, code, requirements):
        """
        Agent C: Audits the code for syntax, hallucinations, and logic errors.
        Ensures the code is strictly Playwright and matches the URL.
        """
        
      
        audit_prompt = (
            f"Act as a Senior QA Auditor. Examine this code based on these requirements: {requirements}.\n\n"
            f"CODE TO AUDIT:\n{code}\n\n"
            "CRITICAL CHECKLIST:\n"
            "1. Is it using ONLY Playwright (sync_api)? (If it uses Flask, it's a FAIL)\n"
            "2. Does it target https://the-internet.herokuapp.com/?\n"
            "3. Are there English explanations or bullet points inside the code?\n"
            "4. Does it include assertions to verify the requirements?\n\n"
            "If the code is perfect, start your response with 'CONFIRMED'.\n"
            "If there are errors, start with 'FAIL' and list the specific issues for the Generator to fix."
        )

      
        response = self.model.invoke(audit_prompt)
        
      
        return response.content if hasattr(response, 'content') else response
