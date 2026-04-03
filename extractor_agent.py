from pypdf import PdfReader

class RequirementExtractor:
    """Agent A: Responsible for parsing the PDF and structuring requirements."""
    
    def __init__(self, model):
        
        self.model = model

    def run(self, pdf_path: str):
        """Main entry point for Agent A."""
        # 1. Read the physical PDF file from the project folder
        raw_text = self._read_pdf(pdf_path)
        
        # 2. Use the LLM to extract and structure the data
        return self._extract_requirements(raw_text)

    def _read_pdf(self, path: str) -> str:
        """Internal method to convert PDF pages to a single string."""
        text = ""
        try:
            reader = PdfReader(path)
            for page in reader.pages:
                content = page.extract_text()
                if content:
                    text += content
            return text
        except Exception as e:
            return f"Error reading PDF: {str(e)}"

    def _extract_requirements(self, text: str):
        """Internal method to trigger the AI extraction logic."""
        # This prompt ensures we get the FR-IDs and behaviors mentioned in the SRS
        prompt = (
            f"Act as a Requirements Engineer. From the following text, extract a "
            f"structured list of every 'Requirement ID' (e.g., FR-CB-01) and its "
            f"corresponding 'Expected Behavior'. \n\nTEXT: {text}"
        )
        
        # Agent A 'invokes' the model to get the structured list
        response = self.model.invoke(prompt)
        
        # Return the extracted content to the main workflow
        return response