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
MODEL_NAME: str = os.getenv("MODEL", "gemini-1.5-flash")

safety_settings = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
]

# ❌ REMOVE response_mime_type — AI must return MARKDOWN + JSON ✨
model = genai.GenerativeModel(
    MODEL_NAME,
    safety_settings=safety_settings
)

# =========================
# Load Prompt Files
# =========================
def _load_prompt(filename: str) -> str:
    try:
        with open(f"prompts/{filename}", "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        logger.error(f"Prompt load error: {filename} → {e}")
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
# Fallback Safe Itinerary
# =========================
def fallback_itinerary() -> Dict[str, Any]:
    return {
        "plan": "## No detailed plan generated.\nPlease try again.",
        "activities": [],
        "total_cost": 0,
        "eco_score": 7.0,
        "carbon_saved": "0kg",
        "waste_free_score": 5,
        "plan_health_score": 50,
        "budget_breakdown": {"Note": "AI could not generate data."},
        "carbon_offset_suggestion": "Plant a tree.",
        "ai_image_prompt": "Eco-friendly beautiful landscape.",
        "ai_time_planner_report": "Basic schedule only.",
        "cost_leakage_report": "No data.",
        "risk_safety_report": "Standard safety advice.",
        "weather_contingency": "Check weather before travel.",
        "duplicate_trip_detector": "Unique trip.",
        "experience_highlights": [],
        "trip_mood_indicator": {},
    }

# =========================
# Agent Workflow Class
# =========================
class AgentWorkflow:

    # ---- Gemini Call ----
    def _ask(self, prompt: str) -> Optional[str]:
        try:
            response = model.generate_content(prompt)

            text = getattr(response, "text", None)

            if not text and response.candidates:
                try:
                    parts = response.candidates[0].content.parts
                    if parts and hasattr(parts[0], "text"):
                        text = parts[0].text
                except:
                    pass

            return text
        except Exception as e:
            logger.error(f"Gemini call failed → {e}")
            return None

    # ---- Clean raw LLM output to extract only JSON ----
    def _clean_llm_output(self, text: str) -> str:
        if not text:
            return ""

        cleaned = text.strip()

        cleaned = cleaned.replace("```json", "").replace("```", "")

        start = cleaned.find("{")
        end = cleaned.rfind("}")

        if start == -1 or end == -1:
            return cleaned.strip()

        return cleaned[start:end + 1].strip()

    # ---- Validate JSON and apply Pydantic schema ----
    def _validate_json_output(self, llm_output: str) -> Optional[Dict[str, Any]]:
        try:
            cleaned = self._clean_llm_output(llm_output)

            data = None

            try:
                data = json.loads(cleaned)
            except:
                data = extract_json(cleaned)

            if not data:
                raise ValueError(f"No valid JSON: {cleaned[:100]}...")

            parsed = ItinerarySchema(**data)
            return parsed.model_dump()

        except ValidationError as e:
            logger.error(f"Schema validation failed → {e}")
            return None
        except Exception as e:
            logger.error(f"JSON parse failed → {e}")
            return None

    # =================================================
    # MAIN ITINERARY GENERATOR
    # =================================================
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

        try:
            profile_ack = ""
            if user_profile.get("interests"):
                profile_ack = (
                    f"User '{user_profile.get('name', 'Traveler')}' likes "
                    f"{user_profile.get('interests')}."
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

            parsed = self._validate_json_output(raw)
            return parsed if parsed else fallback_itinerary()

        except Exception as e:
            logger.exception(f"Agent.run failed → {e}")
            return fallback_itinerary()

    # =================================================
    # SIMPLE REFINER — matches your UI exactly
    # =================================================
    def refine_plan(self, previous_plan_json: Dict[str, Any], feedback_query: str) -> Dict[str, Any]:
        try:
            prompt = f"""
You are a travel plan refiner.

User feedback: "{feedback_query}"

Here is the previous plan:
{json.dumps(previous_plan_json, ensure_ascii=False)}

Modify the plan and return a NEW JSON itinerary.
Keep same structure.
Always output VALID JSON only.
"""

            raw = self._ask(prompt)
            if not raw:
                return previous_plan_json

            parsed = self._validate_json_output(raw)
            return parsed if parsed else previous_plan_json

        except Exception as e:
            logger.exception(f"Refine failed → {e}")
            return previous_plan_json

    # =================================================
    # PACKING LIST
    # =================================================
    def generate_packing_list(self, plan_context: str, user_profile: Dict, list_type: str) -> str:
        try:
            prompt = PROMPTS["packing"].format(
                plan_context=plan_context,
                user_profile=user_profile,
                list_type=list_type
            )
            resp = self._ask(prompt)
            return resp or "Could not generate packing list."
        except Exception as e:
            logger.exception(f"Packing list failed → {e}")
            return "Could not generate packing list."

    # =================================================
    # STORY
    # =================================================
    def generate_story(self, plan_context: str, user_name: str) -> str:
        try:
            prompt = PROMPTS["story"].format(
                plan_context=plan_context,
                user_name=user_name
            )
            resp = self._ask(prompt)
            return resp or "Could not generate story."
        except Exception as e:
            logger.exception(f"Story failed → {e}")
            return "Could not generate story."

    # =================================================
    # CHATBOT
    # =================================================
    def ask_question(self, plan_context: str, question: str) -> str:
        try:
            prompt = PROMPTS["question"].format(
                plan_context=plan_context,
                question=question
            )
            resp = self._ask(prompt)
            return resp or "Sorry, I couldn't answer that."
        except Exception as e:
            logger.exception(f"Question handler failed → {e}")
            return "Sorry, I couldn't answer that."

    # =================================================
    # UPGRADE SUGGESTIONS
    # =================================================
    def get_upgrade_suggestions(self, plan_context: str, user_profile: Dict, rag_data: List[Dict]) -> str:
        try:
            prompt = PROMPTS["upgrade"].format(
                plan_context=plan_context,
                user_profile=user_profile,
                rag_data=rag_data
            )
            resp = self._ask(prompt)
            return resp or "No upgrade suggestions available."
        except Exception as e:
            logger.exception(f"Upgrade failed → {e}")
            return "Could not generate upgrade suggestions."
