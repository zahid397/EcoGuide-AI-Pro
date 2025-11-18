import os
import google.generativeai as genai
from dotenv import load_dotenv
from backend.utils import extract_json
from utils.schemas import ItinerarySchema
from utils.logger import logger
from typing import Dict, Any, Optional, List
from pydantic import ValidationError
import json

# Load env
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
MODEL_NAME = os.getenv("MODEL", "gemini-1.5-flash")

# Safer config
model = genai.GenerativeModel(
    MODEL_NAME,
    safety_settings=[
        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
    ]
)

# ------- Load Prompts -------
def _load_prompt(filename: str) -> str:
    try:
        with open(f"prompts/{filename}", "r", encoding="utf-8") as f:
            return f.read()
    except:
        return ""


PROMPTS = {
    "itinerary": _load_prompt("itinerary_prompt.txt"),
    "refine": _load_prompt("refine_prompt.txt"),
    "upgrade": _load_prompt("upgrade_prompt.txt"),
    "question": _load_prompt("question_prompt.txt"),
    "packing": _load_prompt("packing_prompt.txt"),
    "story": _load_prompt("story_prompt.txt"),
}

# ------- Fallback -------
def fallback_itinerary():
    return {
        "plan": "No plan generated.",
        "activities": [],
        "total_cost": 0,
        "eco_score": 0,
        "carbon_saved": "0kg",
        "waste_free_score": 5,
        "plan_health_score": 60,
        "budget_breakdown": {},
        "carbon_offset_suggestion": "Plant a tree.",
        "ai_image_prompt": "",
        "ai_time_planner_report": "",
        "cost_leakage_report": "",
        "risk_safety_report": "",
        "weather_contingency": "",
        "duplicate_trip_detector": "Unique trip",
        "experience_highlights": [],
        "trip_mood_indicator": {}
    }


# ============= AGENT WORKFLOW =============
class AgentWorkflow:

    # SAFE model call — always returns clean text
    def _ask(self, prompt: str) -> Optional[str]:
        try:
            response = model.generate_content(prompt)

            # Gemini often puts JSON in parts -> extract safely
            try:
                parts = response.candidates[0].content.parts
                if parts and parts[0].text:
                    return parts[0].text
            except:
                pass

            # fallback to response.text
            return getattr(response, "text", None)

        except Exception as e:
            logger.error(f"Gemini error → {e}")
            return None

    # Validate final JSON
    def _validate_json_output(self, raw_output: str):
        try:
            data = extract_json(raw_output)
            if not data:
                return None

            parsed = ItinerarySchema(**data)
            return parsed.model_dump()

        except Exception as e:
            logger.error(f"JSON validation error → {e}")
            return None

    # MAIN PLAN
    def run(self, query, rag_data, budget, interests, days, location,
            travelers, user_profile, priorities):

        prompt = PROMPTS["itinerary"].format(
            query=query,
            days=days,
            travelers=travelers,
            budget=budget,
            eco_priority=priorities.get("eco"),
            budget_priority=priorities.get("budget"),
            comfort_priority=priorities.get("comfort"),
            user_name=user_profile.get("name", "Traveler"),
            user_interests=user_profile.get("interests", []),
            profile_ack="",
            rag_data=json.dumps(rag_data)
        )

        raw = self._ask(prompt)
        if not raw:
            return fallback_itinerary()

        parsed = self._validate_json_output(raw)
        return parsed if parsed else fallback_itinerary()

    # REFINER
    def refine_plan(self, previous_plan_json, feedback_query, rag_data,
                    user_profile, priorities, travelers, days, budget):

        prompt = PROMPTS["refine"].format(
            user_profile=user_profile,
            priorities=priorities,
            feedback_query=feedback_query,
            previous_plan_json=json.dumps(previous_plan_json),
            rag_data=json.dumps(rag_data),
            travelers=travelers,
            days=days,
            budget=budget
        )

        raw = self._ask(prompt)
        if not raw:
            return fallback_itinerary()

        parsed = self._validate_json_output(raw)
        return parsed if parsed else fallback_itinerary()

    # CHAT
    def ask_question(self, plan_context, question):
        prompt = PROMPTS["question"].format(
            plan_context=plan_context,
            question=question
        )
        return self._ask(prompt) or "Couldn't answer."

    # PACKING
    def generate_packing_list(self, plan_context, user_profile, list_type):
        prompt = PROMPTS["packing"].format(
            plan_context=plan_context,
            user_profile=user_profile,
            list_type=list_type
        )
        return self._ask(prompt) or "Could not generate."

    # STORY
    def generate_story(self, plan_context, user_name):
        prompt = PROMPTS["story"].format(
            plan_context=plan_context,
            user_name=user_name
        )
        return self._ask(prompt) or "Could not generate story."
