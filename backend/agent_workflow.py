import os
import google.generativeai as genai
from dotenv import load_dotenv
from backend.utils import extract_json
from utils.schemas import ItinerarySchema
from utils.logger import logger
from pydantic import ValidationError
from typing import Dict, Any, Optional, List

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
MODEL_NAME: str = os.getenv("MODEL", "gemini-1.5-flash")

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
        return ""

PROMPTS = {
    "itinerary": _load_prompt("itinerary_prompt.txt"),
    "refine": _load_prompt("refine_prompt.txt"),
    "upgrade": _load_prompt("upgrade_prompt.txt"),
    "question": _load_prompt("question_prompt.txt"),
    "packing": _load_prompt("packing_prompt.txt"),
    "story": _load_prompt("story_prompt.txt"),
}

class AgentWorkflow:

    # -------------------------------
    # Generic LLM Caller
    # -------------------------------
    def _ask(self, prompt: str) -> Optional[str]:
        try:
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            logger.exception(f"Gemini API call failed: {e}")
            return None

    # -------------------------------
    # Validate Schema (JSON)
    # -------------------------------
    def _validate_json_output(self, llm_output: str) -> Optional[Dict[str, Any]]:
        try:
            json_data = extract_json(llm_output)
            if not json_data:
                raise ValueError("No JSON found")
            parsed = ItinerarySchema(**json_data)
            return parsed.model_dump()
        except Exception as e:
            logger.error(f"JSON Validation Failed: {e}")
            return None

    # -------------------------------
    # MAIN PLAN GENERATOR
    # -------------------------------
    def run(self, query: str, rag_data: List[Dict], budget: int, interests: List[str],
            days: int, location: str, travelers: int, user_profile: Dict,
            priorities: Dict) -> Optional[Dict[str, Any]]:

        prompt = PROMPTS["itinerary"].format(
            query=query, days=days, travelers=travelers, budget=budget,
            eco_priority=priorities.get("eco"), budget_priority=priorities.get("budget"),
            comfort_priority=priorities.get("comfort"), user_profile=user_profile,
            rag_data=rag_data
        )

        result = self._ask(prompt)
        return self._validate_json_output(result) if result else None

    # -------------------------------
    # REFINER — UI Compatible
    # -------------------------------
    def refine_plan(self, previous_plan_json: str, feedback_query: str, 
                    rag_data: List[Dict], user_profile: Dict, priorities: Dict, 
                    travelers: int, days: int, budget: int) -> Optional[Dict]:

        prompt = PROMPTS["refine"].format(
            feedback_query=feedback_query,
            previous_plan_json=previous_plan_json,
            travelers=travelers,
            days=days,
            budget=budget,
            user_profile=user_profile,
            rag_data=rag_data,
            priorities=priorities,
        )

        result = self._ask(prompt)
        return self._validate_json_output(result) if result else None

    # -------------------------------
    # UPGRADE SUGGESTIONS (No plan_context errors)
    # -------------------------------
    def get_upgrade_suggestions(self, plan_context: str, user_profile: Dict, rag_data: List[Dict]) -> str:
        prompt = PROMPTS["upgrade"].format(
            plan_context=plan_context,
            user_profile=user_profile,
            rag_data=rag_data,
        )
        result = self._ask(prompt)
        return result or "No upgrade suggestions were generated."

    # -------------------------------
    # CHATBOT
    # -------------------------------
    def ask_question(self, plan_context: str, question: str) -> str:
        prompt = PROMPTS["question"].format(
            plan_context=plan_context, question=question
        )
        result = self._ask(prompt)
        return result or "Sorry, I could not answer that question."

    # -------------------------------
    # PACKING LIST (UI Compatible)
    # -------------------------------
    def generate_packing_list(self, plan_context: str, user_profile: Dict, list_type: str) -> str:
        prompt = PROMPTS["packing"].format(
            plan_context=plan_context,
            user_profile=user_profile,
            list_type=list_type
        )
        result = self._ask(prompt)
        return result or "Packing list unavailable."

    # -------------------------------
    # STORY GENERATOR
    # -------------------------------
    def generate_story(self, plan_context: str, user_name: str) -> str:
        prompt = PROMPTS["story"].format(
            plan_context=plan_context,
            user_name=user_name
        )
        result = self._ask(prompt)
        return result or "Could not generate story."
