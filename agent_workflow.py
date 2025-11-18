import os
import json
from typing import Dict, Any, Optional, List

import google.generativeai as genai
from dotenv import load_dotenv
from pydantic import ValidationError

from backend.utils import extract_json
from utils.schemas import ItinerarySchema
from utils.logger import logger

# =========================
# Gemini Setup
# =========================
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

model = genai.GenerativeModel(
    MODEL_NAME,
    safety_settings=safety_settings,
    generation_config={"response_mime_type": "text/plain"}
)

# =========================
# Load Prompts
# =========================
def _load_prompt(filename: str) -> str:
    try:
        with open(f"prompts/{filename}", "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        logger.error(f"[PROMPT ERROR] Cannot load: {filename} → {e}")
        return ""


PROMPTS = {
    "itinerary": _load_prompt("itinerary_prompt.txt"),
    "refine": _load_prompt("refine_prompt.txt"),
    "upgrade": _load_prompt("upgrade_prompt.txt"),
    "question": _load_prompt("question_prompt.txt"),
    "packing": _load_prompt("packing_prompt.txt"),
    "story": _load_prompt("story_prompt.txt"),
}

# =========================
# Safe Fallback
# =========================
def fallback_itinerary() -> Dict[str, Any]:
    return {
        "plan": "No plan could be generated.",
        "activities": [],
        "total_cost": 0,
        "eco_score": 5.0,
        "carbon_saved": "0kg",
        "waste_free_score": 5,
        "plan_health_score": 60,
        "budget_breakdown": {"Note": "Unavailable"},
        "carbon_offset_suggestion": "Plant a tree.",
        "ai_image_prompt": "",
        "ai_time_planner_report": "",
        "cost_leakage_report": "",
        "risk_safety_report": "",
        "weather_contingency": "",
        "duplicate_trip_detector": "",
        "experience_highlights": [],
        "trip_mood_indicator": {}
    }

# =========================
# AGENT WORKFLOW
# =========================
class AgentWorkflow:

    # ---------------------------------
    # Gemini Call
    # ---------------------------------
    def _ask(self, prompt: str) -> Optional[str]:
        try:
            response = model.generate_content(prompt)

            # Extract text safely
            if hasattr(response, "text") and response.text:
                return response.text

            # fallback
            if response.candidates:
                parts = response.candidates[0].content.parts
                if parts and hasattr(parts[0], "text"):
                    return parts[0].text

            return None

        except Exception as e:
            logger.error(f"Gemini API Error → {e}")
            return None

    # ---------------------------------
    # Clean LLM output → JSON only
    # ---------------------------------
    def _clean_json(self, text: str) -> str:
        if not text:
            return ""

        cleaned = (
            text.replace("```json", "")
                .replace("```", "")
                .strip()
        )

        start = cleaned.find("{")
        end = cleaned.rfind("}")

        if start == -1 or end == -1:
            return cleaned.strip()

        return cleaned[start:end + 1]

    # ---------------------------------
    # Validate JSON
    # ---------------------------------
    def _validate(self, raw_text: str) -> Optional[Dict[str, Any]]:
        try:
            cleaned = self._clean_json(raw_text)

            # Try direct JSON
            try:
                data = json.loads(cleaned)
            except:
                data = extract_json(cleaned)

            if not data:
                raise ValueError("No JSON extracted.")

            parsed = ItinerarySchema(**data)
            return parsed.model_dump()

        except Exception as e:
            logger.error(f"[JSON ERROR] → {e}")
            return None

    # =====================================================
    # GENERATE FULL ITINERARY
    # =====================================================
    def run(self, query: str, rag_data: List[Dict], budget: int, interests: List[str],
            days: int, location: str, travelers: int, user_profile: Dict, priorities: Dict):

        try:
            profile_ack = (
                f"User '{user_profile.get('name', 'Traveler')}' likes {user_profile.get('interests', [])}."
                if user_profile.get("interests") else ""
            )

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
                profile_ack=profile_ack,
                rag_data=rag_data,
            )

            raw = self._ask(prompt)
            if not raw:
                return fallback_itinerary()

            parsed = self._validate(raw)
            return parsed if parsed else fallback_itinerary()

        except Exception as e:
            logger.error(f"[RUN ERROR] {e}")
            return fallback_itinerary()

    # =====================================================
    # SIMPLE REFINER (Matches Your UI)
    # =====================================================
    def refine_plan(self, previous_plan_json: Dict[str, Any], feedback_query: str) -> Dict[str, Any]:
        try:
            prompt = f"""
You are a travel plan refiner.

User says: "{feedback_query}"

Here is the previous plan JSON:
{json.dumps(previous_plan_json, ensure_ascii=False)}

Rewrite the entire plan and return STRICT JSON only.
"""

            raw = self._ask(prompt)
            if not raw:
                return previous_plan_json

            parsed = self._validate(raw)
            return parsed if parsed else previous_plan_json

        except Exception as e:
            logger.error(f"[REFINE ERROR] {e}")
            return previous_plan_json

    # =====================================================
    # PACKING LIST
    # =====================================================
    def generate_packing_list(self, plan_context: str, user_profile: Dict, list_type: str) -> str:
        try:
            prompt = PROMPTS["packing"].format(
                plan_context=plan_context,
                user_profile=user_profile,
                list_type=list_type
            )
            return self._ask(prompt) or "Could not generate packing list."
        except Exception as e:
            logger.error(f"[PACKING ERROR] {e}")
            return "Could not generate packing list."

    # =====================================================
    # STORY
    # =====================================================
    def generate_story(self, plan_context: str, user_name: str) -> str:
        try:
            prompt = PROMPTS["story"].format(
                plan_context=plan_context,
                user_name=user_name
            )
            return self._ask(prompt) or "Could not generate story."
        except Exception as e:
            logger.error(f"[STORY ERROR] {e}")
            return "Could not generate story."

    # =====================================================
    # CHAT
    # =====================================================
    def ask_question(self, plan_context: str, question: str) -> str:
        try:
            prompt = PROMPTS["question"].format(
                plan_context=plan_context,
                question=question
            )
            return self._ask(prompt) or "Sorry, I couldn't answer that."
        except Exception as e:
            logger.error(f"[CHAT ERROR] {e}")
            return "Sorry, I couldn't answer that."

    # =====================================================
    # UPGRADE
    # =====================================================
    def get_upgrade_suggestions(self, plan_context: str, user_profile: Dict, rag_data: List[Dict]) -> str:
        try:
            prompt = PROMPTS["upgrade"].format(
                plan_context=plan_context,
                user_profile=user_profile,
                rag_data=rag_data
            )
            return self._ask(prompt) or "No upgrade suggestions available."
        except Exception as e:
            logger.error(f"[UPGRADE ERROR] {e}")
            return "Could not generate upgrade suggestions."
