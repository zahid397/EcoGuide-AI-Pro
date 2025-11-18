import os
import json
import google.generativeai as genai
from dotenv import load_dotenv
from backend.utils import extract_json
from utils.schemas import ItinerarySchema
from utils.logger import logger

# 1. Load Environment Variables
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if api_key:
    genai.configure(api_key=api_key)
else:
    logger.error("❌ GEMINI_API_KEY Missing! Check your .env file.")

# --- ✳️ FORCE MODEL: GEMINI 1.5 FLASH (Fastest & Cheapest) ---
MODEL_NAME = "gemini-1.5-flash"

# 2. Disable Safety Filters (To prevent blocking travel plans)
safety_settings = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
]

model = genai.GenerativeModel(MODEL_NAME, safety_settings=safety_settings)

# --- ✳️ HARDCODED PROMPTS (Fallback if files missing) ---
ITINERARY_PROMPT_TEMPLATE = """
You are an expert AI travel planner using Gemini 1.5 Flash. Create a valid JSON itinerary.

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
2. Output ONLY valid JSON matching this structure:
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
Refine this JSON plan based on feedback using Gemini 1.5 Flash.
Current Plan: {previous_plan_json}
Feedback: {feedback_query}
New RAG Data: {rag_data}
Output ONLY JSON with the same structure.
"""

def _load_prompt(filename):
    """Loads prompt from file or returns None."""
    try:
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        path = os.path.join(base_path, "prompts", filename)
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except:
        return None

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
            # Try loading from file, else use Hardcoded Template
            file_prompt = _load_prompt("itinerary_prompt.txt")
            prompt_template = file_prompt if file_prompt else ITINERARY_PROMPT_TEMPLATE

            rag_str = json.dumps(rag_data, default=str)
            user_profile = kwargs.get('user_profile', {})
            priorities = kwargs.get('priorities', {})
            
            profile_ack = ""
            if user_profile.get('interests'):
                profile_ack = f"User likes {user_profile.get('interests')}"

            # Safe Formatting (Handles both file and hardcoded templates)
            # We replace placeholders manually to avoid KeyError if the file has different keys
            prompt = prompt_template.replace("{query}", str(query))
            prompt = prompt.replace("{rag_data}", rag_str)
            
            # Replace common keys safely
            replacements = {
                "{budget}": str(kwargs.get('budget', 1000)),
                "{days}": str(kwargs.get('days', 3)),
                "{travelers}": str(kwargs.get('travelers', 1)),
                "{eco_priority}": str(priorities.get('eco', 5)),
                "{budget_priority}": str(priorities.get('budget', 5)),
                "{comfort_priority}": str(priorities.get('comfort', 5)),
                "{user_name}": str(user_profile.get('name', 'User')),
                "{user_interests}": str(user_profile.get('interests', [])),
                "{profile_ack}": profile_ack
            }
            
            for key, val in replacements.items():
                prompt = prompt.replace(key, val)

            return self._validate(self._ask(prompt))

        except Exception as e:
            logger.exception(f"Run Workflow Failed: {e}")
            return self._validate(None)

    def refine_plan(self, previous_plan_json=None, feedback_query="", rag_data=[], **kwargs):
        try:
            prompt = REFINE_PROMPT_TEMPLATE.format(
                previous_plan_json=str(previous_plan_json)[:8000], 
                feedback_query=feedback_query,
                rag_data=json.dumps(rag_data, default=str)[:3000]
            )
            return self._validate(self._ask(prompt))
        except Exception as e:
            logger.exception(f"Refine Failed: {e}")
            return None

    # --- HELPERS ---
    def ask_question(self, plan_context, question):
        return self._ask(f"Context: {str(plan_context)[:5000]}\nQuestion: {question}\nAnswer briefly.") or "I couldn't answer that."

    def generate_packing_list(self, plan_context, user_profile, list_type):
        return self._ask(f"Create a {list_type} packing list for: {str(plan_context)[:3000]}") or "List unavailable."

    def generate_story(self, plan_context, user_name):
        return self._ask(f"Write a story for {user_name} based on: {str(plan_context)[:3000]}") or "Story unavailable."

    def get_upgrade_suggestions(self, plan_context, user_profile, rag_data):
        return self._ask(f"Suggest 3 upgrades for: {str(plan_context)[:3000]}") or "No upgrades."
        
