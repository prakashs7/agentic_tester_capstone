class CodeGenerator:
    def __init__(self, model):
        self.model = model

    def generate(self, requirements, feedback=None):
        """
        Agent B: Generates clean, executable Playwright code.
        Ensures NO conversational text or markdown is included.
        """
        
     
        system_instruction = (
            "You are a Playwright Automation Expert. "
            "CRITICAL: Always start your code with 'from playwright.sync_api import sync_playwright'. "
            "NEVER use 'import sync_playwright' alone. "
            "Your ONLY job is to write Python Playwright tests. "
            "DO NOT use Flask. DO NOT build a website. "
            "Do NOT fail the test if there are 'net::ERR_NAME_NOT_RESOLVED' console errors. "
            "ONLY write code that opens a browser and tests 'https://the-internet.herokuapp.com/'. "
            "Output ONLY the raw Python code without markdown blocks or explanations."
            "CRITICAL: For checkbox assertions, use 'expect(locator).to_be_checked()' "
            "or 'expect(locator).not_to_be_checked()'. "
            "NEVER use '.to_have_property(\"checked\")' as it causes an AttributeError."
        )

        if feedback:
          
            user_prompt = (
                f"UPDATE the existing code based on this feedback: {feedback}. "
                f"Requirements: {requirements}"
            )
        else:
          
            user_prompt = (
                f"Generate a standalone Playwright Python script for: {requirements}. "
                f"Target URL: https://the-internet.herokuapp.com/."
            )

      
        full_prompt = f"{system_instruction}\n\n{user_prompt}"
        
      
        response = self.model.invoke(full_prompt)
        return response.content if hasattr(response, 'content') else response
