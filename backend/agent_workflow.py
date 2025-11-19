import os
import json
import google.generativeai as genai
from dotenv import load_dotenv
from backend.utils import extract_json
from utils.schemas import ItinerarySchema
from utils.logger import logger

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
MODEL_NAME = os.getenv("MODEL", "gemini-1.5-flash")

# Safety OFF (যাতে উত্তর ব্লক না করে)
safety_settings = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
]

model = genai.GenerativeModel(MODEL_NAME, safety_settings=safety_settings)

# Fallback Prompt (ফাইল না পেলে এটা চলবে)
DEFAULT_PROMPT = """
You are an expert travel planner. Create a JSON itinerary.
Output JSON ONLY matching this schema:
{
  "plan": "Markdown plan...",
  "activities": [],
  "total_cost": 0,
  "eco_score": 0,
  "carbon_saved": "0kg",
  "waste_free_score": 5,
  "plan_health_score": 80,
  "budget_breakdown": {"Hotel": 0, "Food": 0},
  "carbon_offset_suggestion": "Plant a tree",
  "ai_image_prompt": "Nature view",
  "ai_time_planner_report": "Schedule is good",
  "cost_leakage_report": "No leaks",
  "risk_safety_report": "Safe trip",
  "duplicate_trip_detector": "Unique trip",
  "experience_highlights": [],
  "trip_mood_indicator": {}
}
"""

def _load_prompt(filename):
    try:
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        path = os.path.join(base, "prompts", filename)
        with open(path, "r", encoding="utf-8") as f: return f.read()
    except: return DEFAULT_PROMPT

class AgentWorkflow:
    def _ask(self, prompt):
        try:
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            logger.exception(f"Gemini API Error: {e}")
            return None

    def _validate(self, text):
        try:
            data = extract_json(text)
            if not data: return ItinerarySchema().model_dump()
            return ItinerarySchema(**data).model_dump()
        except: return ItinerarySchema().model_dump()

    def run(self, query, rag_data, **kwargs):
        try:
            prompt_template = _load_prompt("itinerary_prompt.txt")
            rag_str = json.dumps(rag_data, default=str)
            
            prompt = prompt_template.replace("{query}", str(query))
            prompt = prompt.replace("{rag_data}", rag_str)
            
            for k, v in kwargs.items():
                prompt = prompt.replace("{" + k + "}", str(v))
                
            return self._validate(self._ask(prompt))
        except Exception as e:
            logger.exception(e)
            return self._validate(self._ask(f"{DEFAULT_PROMPT}\nQuery: {query}"))

    def refine_plan(self, previous_plan_json=None, feedback_query="", rag_data=[], **kwargs):
        try:
            # Limit context size to prevent errors
            prompt = f"""
            Refine this JSON plan.
            Feedback: {feedback_query}
            Current Plan: {str(previous_plan_json)[:5000]}
            Output ONLY JSON.
            """
            return self._validate(self._ask(prompt))
        except: return None

    # --- FIX: Shorten Context for Chat & Story ---
    
    def ask_question(self, plan_context, question):
        # Context ছোট করে পাঠানো হচ্ছে
        prompt = f"""
        Context: {str(plan_context)[:4000]}
        Question: "{question}"
        Answer nicely in 2-3 sentences.
        """
        return self._ask(prompt) or "I'm having trouble connecting. Please ask again."

    def generate_story(self, plan_context, user_name):
        prompt = f"""
        Write a short (100 words) travel story for {user_name}.
        Based on: {str(plan_context)[:3000]}
        """
        return self._ask(prompt) or "Once upon a time... (Story generation failed)."

    def generate_packing_list(self, plan_context, user_profile, list_type):
        prompt = f"Create a {list_type} packing list based on: {str(plan_context)[:3000]}"
        return self._ask(prompt) or "### Essentials\n* Passport\n* Money"

    def get_upgrade_suggestions(self, plan_context, user_profile, rag_data):
        prompt = f"Suggest 3 upgrades for: {str(plan_context)[:3000]}"
        return self._ask(prompt) or "No upgrades available."
        
