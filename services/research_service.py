from .gemini_service import gemini_service
from prompts import PromptLibrary

class ResearchService:
    def perform_research(self, query: str):
        prompt = PromptLibrary.ai_researcher(query)
        # Call the gemini_service with the flag to enable the search tool
        return gemini_service.generate_text_response(prompt, use_research_tool=True)

# Singleton instance
research_service = ResearchService()