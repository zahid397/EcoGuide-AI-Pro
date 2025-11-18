import os
import json
import google.generativeai as genai
from dotenv import load_dotenv
from backend.utils import extract_json
from utils.schemas import ItinerarySchema
from utils.logger import logger
from typing import Dict, Any, Optional, List

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
MODEL_NAME = os.getenv("MODEL", "gemini-1.5-flash")

# Safety settings
safety_settings = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
]

model = genai.GenerativeModel(MODEL_NAME, safety_settings=safety_settings)

# --- ✳️ FIX: DEFAULT PROMPT WITH PLACEHOLDERS ---
# ফাইল না পেলে এটি ব্যবহার হবে, এবং এতে {query} ইত্যাদি থাকতে হবে।
DEFAULT_PROMPT = """
You are an expert travel planner. Create a detailed JSON itinerary based on the request.

**Request:**
Query: {query}
RAG Data: {rag_data}

**Instructions:**
1. Create a day-by-day plan in Markdown.
2. Output ONLY valid JSON matching this schema:
{
  "plan": "Markdown plan...",
  "activities": [],
  "total_cost": 0,
  "eco_score": 0,
  "carbon_saved": "0kg",
  "waste_free_score": 5,
  "plan_health_score": 80,
  "budget_breakdown": {},
  "carbon_offset_suggestion": "None",
  "ai_image_prompt": "None",
  "ai_time_planner_report": "Good",
  "cost_leakage_report": "None",
  "risk_safety_report": "Safe",
  "weather_contingency": "None",
  "duplicate_trip_detector": "None",
  "experience_highlights": [],
  "trip_mood_indicator": {}
}
"""

def _load_prompt(filename):
    try:
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        path = os.path.join(base, "prompts", filename)
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except:
        logger.warning(f"Prompt file {filename} not found. Using fallback.")
        return DEFAULT_PROMPT

class AgentWorkflow:
    def _ask(self, prompt):
        try:
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            logger.exception(f"Gemini Error: {e}")
            return None

    def _validate(self, text):
        try:
            data = extract_json(text)
            if not data: return ItinerarySchema().model_dump()
            return ItinerarySchema(**data).model_dump()
        except:
            return ItinerarySchema().model_dump()

    def run(self, query, rag_data, **kwargs):
        try:
            prompt_template = _load_prompt("itinerary_prompt.txt")
            rag_str = json.dumps(rag_data, default=str)
            
            # --- ✳️ FIX: Safe Replacement ---
            # যদি টেমপ্লেটে {query} না থাকে (ভুল ফাইলে), আমরা ম্যানুয়ালি যোগ করব
            if "{query}" not in prompt_template:
                prompt_template = DEFAULT_PROMPT

            prompt = prompt_template.replace("{query}", str(query))
            prompt = prompt.replace("{rag_data}", rag_str)
            
            # Dynamic replacements
            for k, v in kwargs.items():
                placeholder = "{" + k + "}"
                if placeholder in prompt:
                    prompt = prompt.replace(placeholder, str(value))
                
            return self._validate(self._ask(prompt))
            
        except Exception as e:
            logger.exception(e)
            # Emergency Fallback
            fallback = DEFAULT_PROMPT.replace("{query}", str(query)).replace("{rag_data}", str(rag_data)[:500])
            return self._validate(self._ask(fallback))

    def refine_plan(self, previous_plan_json=None, feedback_query="", rag_data=[], **kwargs):
        try:
            prompt = f"""
            Refine this JSON plan based on feedback.
            Current Plan: {str(previous_plan_json)[:8000]}
            Feedback: {feedback_query}
            New Options: {json.dumps(rag_data, default=str)[:3000]}
            Output ONLY JSON.
            """
            return self._validate(self._ask(prompt))
        except Exception as e:
            logger.exception(e)
            return None

    # --- Helper Functions (Direct Prompts) ---
    
    def ask_question(self, plan_context, question):
        prompt = f"Context: {str(plan_context)[:5000]}\nQuestion: {question}\nAnswer briefly."
        return self._ask(prompt) or "I couldn't answer that."

    def generate_packing_list(self, plan_context, user_profile, list_type):
        prompt = f"Create a {list_type} packing list for: {str(plan_context)[:3000]}"
        return self._ask(prompt) or "Could not generate list."

    def generate_story(self, plan_context, user_name):
        prompt = f"Write a story for {user_name} based on: {str(plan_context)[:3000]}"
        return self._ask(prompt) or "Could not generate story."

    def get_upgrade_suggestions(self, plan_context, user_profile, rag_data):
        prompt = f"Suggest 3 upgrades for: {str(plan_context)[:3000]}"
        return self._ask(prompt) or "No upgrades available."
        
