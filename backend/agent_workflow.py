import os
import google.generativeai as genai
from dotenv import load_dotenv
from backend.utils import extract_json
from utils.schemas import ItinerarySchema
from utils.logger import logger
from typing import Dict, Any, Optional, List
from pydantic import ValidationError
import json

# Load environment
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
MODEL_NAME = os.getenv("MODEL", "gemini-1.5-flash")

# Safety
safety_settings = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
]

# Model
model = genai.GenerativeModel(
    MODEL_NAME,
    safety_settings=safety_settings,
    generation_config={"response_mime_type": "application/json"}
)


# Load prompt files
def _load_prompt(filename: str) -> str:
    try:
        with open(f"prompts/{filename}", "r", encoding="utf-8") as f:
            return f.read()
    except:
        logger.error(f"Missing prompt file: {filename}")
        return ""


PROMPTS = {
    "itinerary": _load_prompt("itinerary_prompt.txt"),
    "refine": _load_prompt("refine_prompt.txt"),
    "upgrade": _load_prompt("upgrade_prompt.txt"),
    "question": _load_prompt("question_prompt.txt"),
    "packing": _load_prompt("packing_prompt.txt"),
    "story": _load_prompt("story_prompt.txt"),
}


# -------- FALLBACK SAFE ITINERARY --------
def fallback_itinerary() -> Dict[str, Any]:
    return {
        "plan": "### Day 1\nFallback itinerary because AI failed.",
        "activities": [],
        "total_cost": 0,
        "eco_score": 7.0,
        "carbon_saved": "0kg",
        "waste_free_score": 5,
        "plan_health_score": 50,
        "budget_breakdown": {},
        "carbon_offset_suggestion": "Plant a tree.",
        "ai_image_prompt": "Eco travel scene.",
        "ai_time_planner_report": "Fallback schedule.",
        "cost_leakage_report": "None.",
        "risk_safety_report": "Standard travel safety.",
        "weather_contingency": "Check local weather.",
        "duplicate_trip_detector": "Unique trip.",
        "experience_highlights": [],
        "trip_mood_indicator": {}
    }


# -------- AGENT WORKFLOW CLASS --------
class AgentWorkflow:

    # Gemini Call
    def _ask(self, prompt: str) -> Optional[str]:
        try:
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            logger.error(f"Gemini Failed → {e}")
            return None

    # CLEAN + PARSE JSON
    def _validate_json_output(self, llm_output: str) -> Optional[Dict[str, Any]]:
        try:
            # Hard clean to remove garbage
            cleaned = llm_output.strip()
            cleaned = cleaned.replace("```json", "").replace("```", "")
            cleaned = cleaned.replace("\n'", "").replace("'\n", "")
            cleaned = cleaned.replace("'\n", "")
            cleaned = cleaned.replace("`", "")
            cleaned = cleaned.lstrip("'").lstrip('"')

            data = extract_json(cleaned)
            if not data:
                raise ValueError("JSON not found in LLM output")

            parsed = ItinerarySchema(**data)
            return parsed.model_dump()

        except Exception as e:
            logger.error(f"JSON validation failed → {e}")
            return None

    # MAIN PLAN GENERATION
    def run(
        self,
        query: str,
        rag_data: List[Dict],
        budget: int,
        interests: List[str],
        days: int,
        location: str,
        travelers: int,
        user_profile: Dict,
        priorities: Dict
    ) -> Dict[str, Any]:

        prompt = PROMPTS["itinerary"].format(
            query=query,
            days=days,
            travelers=travelers,
            budget=budget,
            eco_priority=priorities.get("eco", 5),
            budget_priority=priorities.get("budget", 5),
            comfort_priority=priorities.get("comfort", 5),
            user_name=user_profile.get("name", "Traveler"),
            user_interests=user_profile.get("interests", []),
            profile_ack="",
            rag_data=rag_data
        )

        raw = self._ask(prompt)
        if not raw:
            return fallback_itinerary()

        parsed = self._validate_json_output(raw)
        return parsed if parsed else fallback_itinerary()

    # REFINER
    def refine_plan(
        self,
        previous_plan_json: Dict[str, Any],
        feedback_query: str,
        rag_data: List[Dict],
        user_profile: Dict,
        priorities: Dict,
        travelers: int,
        days: int,
        budget: int
    ) -> Dict[str, Any]:

        prompt = PROMPTS["refine"].format(
            user_profile=user_profile,
            priorities=priorities,
            feedback_query=feedback_query,
            previous_plan_json=json.dumps(previous_plan_json),
            rag_data=rag_data,
            travelers=travelers,
            days=days,
            budget=budget
        )

        raw = self._ask(prompt)
        if not raw:
            return fallback_itinerary()

        parsed = self._validate_json_output(raw)
        return parsed if parsed else fallback_itinerary()

    # UPGRADE
    def get_upgrade_suggestions(self, plan_context: str, user_profile: Dict, rag_data: List[Dict]) -> str:
        prompt = PROMPTS["upgrade"].format(
            plan_context=plan_context,
            user_profile=user_profile,
            rag_data=rag_data
        )
        return self._ask(prompt) or "No upgrade suggestions available."

    # CHATBOT
    def ask_question(self, plan_context: str, question: str) -> str:
        prompt = PROMPTS["question"].format(
            plan_context=plan_context,
            question=question
        )
        return self._ask(prompt) or "Sorry, I couldn't answer your question."

    # PACKING LIST
    def generate_packing_list(self, plan_context: str, user_profile: Dict, list_type: str) -> str:
        prompt = PROMPTS["packing"].format(
            user_profile=user_profile,
            plan_context=plan_context,
            list_type=list_type
        )
        return self._ask(prompt) or "Could not generate packing list."

    # STORY
    def generate_story(self, plan_context: str, user_name: str) -> str:
        prompt = PROMPTS["story"].format(
            user_name=user_name,
            plan_context=plan_context
        )
        return self._ask(prompt) or "Could not generate story."
