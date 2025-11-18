import os
import google.generativeai as genai
from dotenv import load_dotenv
from backend.utils import extract_json
from utils.schemas import ItinerarySchema
from utils.logger import logger
from pydantic import ValidationError
from typing import Dict, Any, Optional, List

# Load env
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
MODEL_NAME = os.getenv("MODEL", "gemini-1.5-flash")

# Safe responses
safety_settings = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
]

model = genai.GenerativeModel(MODEL_NAME, safety_settings=safety_settings)


def _load_prompt(filename: str) -> str:
    try:
        with open(f"prompts/{filename}", "r", encoding="utf-8") as f:
            return f.read()
    except:
        logger.error(f"Prompt missing: {filename}")
        return ""


# Load all prompts
PROMPTS = {
    "itinerary": _load_prompt("itinerary_prompt.txt"),
    "refine": _load_prompt("refine_prompt.txt"),
    "upgrade": _load_prompt("upgrade_prompt.txt"),
    "question": _load_prompt("question_prompt.txt"),
    "packing": _load_prompt("packing_prompt.txt"),
    "story": _load_prompt("story_prompt.txt"),
}


# Fallback itinerary
def fallback_plan():
    return {
        "summary": "AI failed, showing fallback plan.",
        "hotel": {"name": "Fallback Hotel", "location": "Dubai", "eco_score": 8.0},
        "activities": [],
        "daily_plan": [],
        "budget_breakdown": {},
    }


# ============================
# AGENT WORKFLOW SAFE VERSION
# ============================
class AgentWorkflow:

    # ------------------------
    # Basic Gemini ask wrapper
    # ------------------------
    def _ask(self, prompt: str) -> Optional[str]:
        try:
            res = model.generate_content(prompt)
            return res.text
        except Exception as e:
            logger.exception(f"Gemini failed: {e}")
            return None

    # ------------------------
    # Validate JSON output
    # ------------------------
    def _validate_json_output(self, llm_output: str) -> Optional[Dict[str, Any]]:
        try:
            json_data = extract_json(llm_output)
            if not json_data:
                return None

            parsed = ItinerarySchema(**json_data)
            return parsed.model_dump()

        except Exception as e:
            logger.exception(f"JSON Parse Error: {e}")
            return None

    # ------------------------
    # MAIN: CREATE ITINERARY
    # ------------------------
    def run(
        self, query: str, rag_data: List[Dict], budget: int, interests: List[str],
        days: int, location: str, travelers: int, user_profile: Dict, priorities: Dict
    ):
        prompt = PROMPTS["itinerary"].format(
            query=query,
            days=days,
            travelers=travelers,
            budget=budget,
            eco_priority=priorities.get("eco", 5),
            budget_priority=priorities.get("budget", 5),
            comfort_priority=priorities.get("comfort", 5),
            user_name=user_profile.get("name", "User"),
            user_interests=user_profile.get("interests", "N/A"),
            rag_data=rag_data,
        )

        raw = self._ask(prompt)
        if not raw:
            return fallback_plan()

        validated = self._validate_json_output(raw)
        return validated or fallback_plan()

    # ------------------------
    # REFINE PLAN
    # ------------------------
    def refine_plan(
        self, previous_plan_json: str, feedback_query: str,
        rag_data: List[Dict], user_profile: Dict, priorities: Dict,
        travelers: int, days: int, budget: int
    ):

        prompt = PROMPTS["refine"].format(
            previous_plan_json=previous_plan_json,
            feedback_query=feedback_query,
            rag_data=rag_data,
            priorities=priorities,
            user_profile=user_profile,
            travelers=travelers,
            days=days,
            budget=budget,
        )

        raw = self._ask(prompt)
        if not raw:
            return fallback_plan()

        validated = self._validate_json_output(raw)
        return validated or fallback_plan()

    # ------------------------
    # UPGRADE SUGGESTIONS
    # ------------------------
    def get_upgrade_suggestions(self, plan_context: str, user_profile: Dict, rag_data: List[Dict]):
        prompt = PROMPTS["upgrade"].format(
            plan_context=plan_context, user_profile=user_profile, rag_data=rag_data
        )
        return self._ask(prompt) or "Upgrade suggestions unavailable right now."

    # ------------------------
    # ASK QUESTION (Chatbot)
    # ------------------------
    def ask_question(self, plan_context: str, question: str):
        prompt = PROMPTS["question"].format(
            plan_context=plan_context, question=question
        )
        return self._ask(prompt) or "Sorry, I couldn't answer that."

    # ------------------------
    # PACKING LIST
    # ------------------------
    def generate_packing_list(self, plan_context: str, user_profile: Dict):
        prompt = PROMPTS["packing"].format(
            plan_context=plan_context, user_profile=user_profile
        )
        return self._ask(prompt) or "Packing list unavailable."

    # ------------------------
    # STORY GENERATION
    # ------------------------
    def generate_story(self, plan_context: str, user_name: str):
        prompt = PROMPTS["story"].format(
            plan_context=plan_context, user_name=user_name
        )
        return self._ask(prompt) or "Could not create story."
