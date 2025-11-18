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

model = genai.GenerativeModel(
    MODEL_NAME,
    safety_settings=[],
    generation_config={"response_mime_type": "application/json"}
)

# =========================
# Load Prompts
# =========================
def load_prompt(name):
    try:
        with open(f"prompts/{name}", "r", encoding="utf-8") as f:
            return f.read()
    except:
        return ""

PROMPTS = {
    "itinerary": load_prompt("itinerary_prompt.txt"),
    "refine": load_prompt("refine_prompt.txt"),
    "upgrade": load_prompt("upgrade_prompt.txt"),
    "question": load_prompt("question_prompt.txt"),
    "packing": load_prompt("packing_prompt.txt"),
    "story": load_prompt("story_prompt.txt"),
}

# =========================
# SAFE FALLBACK
# =========================
def fallback_itinerary():
    return {
        "plan": "### Demo Plan\nThis is the fallback itinerary for demo.",
        "activities": [],
        "total_cost": 0,
        "eco_score": 7,
        "carbon_saved": "10kg",
        "waste_free_score": 7,
        "plan_health_score": 80,
        "budget_breakdown": {"Hotel": 300, "Food": 100},
        "carbon_offset_suggestion": "Plant a tree.",
        "ai_image_prompt": "Landscape",
        "ai_time_planner_report": "Balanced.",
        "cost_leakage_report": "None.",
        "risk_safety_report": "Safe.",
        "weather_contingency": "Keep sunscreen.",
        "duplicate_trip_detector": "Unique.",
        "experience_highlights": ["Beach", "Market"],
        "trip_mood_indicator": {"Adventure": 60, "Relax": 40}
    }

# =========================
# CLEAN JSON
# =========================
def clean_json(text: str):
    if not text:
        return None
    text = text.replace("```json", "").replace("```", "").strip()
    try:
        return json.loads(text)
    except:
        return extract_json(text)

# =========================
# MAIN WORKFLOW
# =========================
class AgentWorkflow:

    def _ask(self, prompt: str) -> Optional[str]:
        """Safe Gemini call – never crashes."""
        try:
            resp = model.generate_content(prompt)
            return getattr(resp, "text", "") or ""
        except Exception as e:
            logger.exception(e)
            return ""

    def _parse(self, raw: str) -> Optional[Dict[str, Any]]:
        try:
            cleaned = clean_json(raw)
            if not cleaned:
                return None
            parsed = ItinerarySchema(**cleaned)
            return parsed.model_dump()
        except:
            return None

    # ===============================
    # MAIN PLAN
    # ===============================
    def run(self, *args, **kwargs) -> Dict[str, Any]:
        try:
            prompt = PROMPTS["itinerary"].format(**kwargs)
            raw = self._ask(prompt)
            parsed = self._parse(raw)
            return parsed or fallback_itinerary()
        except:
            return fallback_itinerary()

    # ===============================
    # REFINER
    # ===============================
    def refine_plan(self, previous_plan_json, feedback_query):
        try:
            prompt = PROMPTS["refine"].format(
                previous_plan_json=json.dumps(previous_plan_json),
                feedback_query=feedback_query,
                user_profile={},
                priorities={},
                rag_data=[],
                travelers=1,
                days=3,
                budget=500
            )
            raw = self._ask(prompt)
            parsed = self._parse(raw)
            return parsed or previous_plan_json
        except:
            return previous_plan_json

    # ===============================
    # PACKING LIST
    # ===============================
    def generate_packing_list(self, **kwargs) -> str:
        try:
            prompt = PROMPTS["packing"].format(**kwargs)
            return self._ask(prompt) or "### Packing List\n- Passport\n- Clothes\n- Water bottle"
        except:
            return "### Packing List\n- Passport\n- Clothes\n- Water bottle"

    # ===============================
    # STORY
    # ===============================
    def generate_story(self, **kwargs) -> str:
        try:
            prompt = PROMPTS["story"].format(**kwargs)
            return self._ask(prompt) or f"### Travel Story\nA beautiful journey."
        except:
            return f"### Travel Story\nA beautiful journey."

    # ===============================
    # QUESTION
    # ===============================
    def ask_question(self, **kwargs) -> str:
        try:
            prompt = PROMPTS["question"].format(**kwargs)
            return self._ask(prompt) or "I don't know."
        except:
            return "I don't know."

    # ===============================
    # UPGRADE
    # ===============================
    def get_upgrade_suggestions(self, **kwargs) -> str:
        try:
            prompt = PROMPTS["upgrade"].format(**kwargs)
            return self._ask(prompt) or "- Upgrade to 5-star hotel."
        except:
            return "- Upgrade to 5-star hotel."
