import os
import google.generativeai as genai
from dotenv import load_dotenv
from backend.utils import extract_json
from utils.schemas import ItinerarySchema
from utils.logger import logger
import json

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
MODEL_NAME = os.getenv("MODEL", "gemini-1.5-flash")

model = genai.GenerativeModel(MODEL_NAME)

# --- ✳️ HARDCODED PROMPTS (No file dependency) ---

ITINERARY_PROMPT_TEMPLATE = """
You are an elite AI travel planner. Create a valid JSON itinerary.

**Request:**
Query: {query}
Budget: ${budget}
Duration: {days} days
Travelers: {travelers}
Priorities: Eco={eco_priority}/10, Budget={budget_priority}/10, Comfort={comfort_priority}/10
Profile: {user_name} likes {user_interests}. {profile_ack}
RAG Data: {rag_data}

**INSTRUCTIONS:**
1. Create a detailed day-by-day plan in Markdown.
2. Select matching activities from RAG Data.
3. Output ONLY valid JSON matching this structure:
{{
  "plan": "### Day 1: ... (Markdown)",
  "activities": [
    {{ "name": "Example Hotel", "cost": 100, "eco_score": 9.0, "data_type": "Hotel", "image_url": "..." }}
  ],
  "total_cost": 0,
  "eco_score": 8.5,
  "carbon_saved": "20kg",
  "waste_free_score": 8,
  "plan_health_score": 90,
  "budget_breakdown": {{ "Hotel": 500, "Food": 200 }},
  "carbon_offset_suggestion": "Plant a tree.",
  "ai_image_prompt": "A photo of...",
  "ai_time_planner_report": "Schedule looks good.",
  "cost_leakage_report": "No leaks.",
  "risk_safety_report": "Stay hydrated.",
  "weather_contingency": "Check forecast.",
  "duplicate_trip_detector": "Unique trip.",
  "experience_highlights": ["Highlight 1", "Highlight 2"],
  "trip_mood_indicator": {{ "Adventure": 80, "Relax": 20 }}
}}
"""

REFINE_PROMPT_TEMPLATE = """
Refine this JSON plan based on feedback.
Current Plan: {previous_plan_json}
Feedback: {feedback_query}
New RAG Data: {rag_data}
Constraints: {days} days, ${budget}, {travelers} travelers.
Output ONLY JSON with the same structure as the original plan.
"""

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
            # If validation fails, return a default schema to prevent crashes
            if not data: return ItinerarySchema().model_dump()
            return ItinerarySchema(**data).model_dump()
        except:
            return ItinerarySchema().model_dump()

    def run(self, query, rag_data, **kwargs):
        """Generates a new plan using hardcoded prompt."""
        try:
            rag_str = json.dumps(rag_data, default=str)
            user_profile = kwargs.get('user_profile', {})
            priorities = kwargs.get('priorities', {})
            
            profile_ack = ""
            if user_profile.get('interests'):
                profile_ack = f"User likes {user_profile.get('interests')}"

            prompt = ITINERARY_PROMPT_TEMPLATE.format(
                query=query,
                budget=kwargs.get('budget', 1000),
                days=kwargs.get('days', 3),
                travelers=kwargs.get('travelers', 1),
                eco_priority=priorities.get('eco', 5),
                budget_priority=priorities.get('budget', 5),
                comfort_priority=priorities.get('comfort', 5),
                user_name=user_profile.get('name', 'User'),
                user_interests=str(user_profile.get('interests', [])),
                profile_ack=profile_ack,
                rag_data=rag_str
            )

            return self._validate(self._ask(prompt))

        except Exception as e:
            logger.exception(f"Run Workflow Failed: {e}")
            return self._validate(None)

    def refine_plan(self, previous_plan_json=None, feedback_query="", rag_data=[], **kwargs):
        """Refines plan using hardcoded prompt."""
        try:
            prompt = REFINE_PROMPT_TEMPLATE.format(
                previous_plan_json=str(previous_plan_json)[:8000], # Limit length
                feedback_query=feedback_query,
                rag_data=json.dumps(rag_data, default=str)[:3000],
                days=kwargs.get('days', 3),
                budget=kwargs.get('budget', 1000),
                travelers=kwargs.get('travelers', 1)
            )
            return self._validate(self._ask(prompt))
        except Exception as e:
            logger.exception(f"Refine Failed: {e}")
            return None

    # --- OTHER HELPERS (Direct Prompts) ---
    def ask_question(self, plan_context, question):
        return self._ask(f"Context: {str(plan_context)[:5000]}\nQuestion: {question}\nAnswer briefly.") or "Error."

    def generate_packing_list(self, plan_context, user_profile, list_type):
        return self._ask(f"Create a {list_type} packing list for: {str(plan_context)[:3000]}") or "List unavailable."

    def generate_story(self, plan_context, user_name):
        return self._ask(f"Write a story for {user_name} based on: {str(plan_context)[:3000]}") or "Story unavailable."

    def get_upgrade_suggestions(self, plan_context, user_profile, rag_data):
        return self._ask(f"Suggest 3 upgrades for: {str(plan_context)[:3000]}") or "No upgrades."
        
