import google.generativeai as genai
import json
from config import Config
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from google.generativeai.types import Tool # <-- NEW IMPORT

class GeminiService:
    def __init__(self):
        if not Config.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY not found in environment variables.")
        genai.configure(api_key=Config.GEMINI_API_KEY)
        
        # --- THIS BLOCK IS NOW CORRECT ---
        # Create the Tool object for Google Search
        google_search_tool = Tool(
            google_search_retrieval={}
        )

        # Model enabled with the Google Search tool for RAG
        self.research_model = genai.GenerativeModel(
            model_name='gemini-1.5-pro-latest',
            tools=[google_search_tool] # <-- Use the Tool object
        )
        
        # Standard model for regular, non-research tasks
        self.standard_model = genai.GenerativeModel('gemini-1.5-pro-latest')

    def generate_json_response(self, prompt):
        """Generates content and expects a clean JSON string back."""
        try:
            # Use the standard model for structured JSON generation
            response = self.standard_model.generate_content(
                prompt,
                # Stricter safety settings for JSON to avoid unwanted text
                safety_settings={
                    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
                    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_ONLY_HIGH,
                }
            )
            cleaned_text = response.text.strip().replace('```json', '').replace('```', '')
            return json.loads(cleaned_text)
        except (json.JSONDecodeError, Exception) as e:
            print(f"Error decoding Gemini response: {e}")
            # Check if response exists before accessing text attribute
            raw_response_text = ""
            if 'response' in locals() and hasattr(response, 'text'):
                raw_response_text = response.text
            print(f"Raw response was: {raw_response_text}")
            return {"error": "Failed to generate or parse AI plan.", "details": str(e)}

    def generate_text_response(self, prompt, use_research_tool=False):
        """Generates a text response, with an option to use the research tool."""
        try:
            model = self.research_model if use_research_tool else self.standard_model
            response = model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            print(f"Error generating text from Gemini: {e}")
            return {"error": "Failed to generate AI response.", "details": str(e)}

# Singleton instance
gemini_service = GeminiService()