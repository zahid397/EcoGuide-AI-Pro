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
    generation_config={"response_mime_type": "application/json"}
)

# =========================
# Load Prompt Files
# =========================
def _load_prompt(filename: str) -> str:
    try:
        with open(f"prompts/{filename}", "r", encoding="utf-8") as f:
            return f.read()
    except:
        return ""

PROMPTS = {
    "itinerary": _load_prompt("itinerary_prompt.txt"),
    "refine": _load_prompt("refine_prompt.txt"),
    "question": _load_prompt("question_prompt.txt"),
    "packing": _load_prompt("packing_prompt.txt"),
    "story": _load_prompt("story_prompt.txt"),
    "upgrade": "",
}

# =========================
# Fallback Safe Output
# =========================
def fallback_itinerary():
    return {
        "plan": "## No plan generated.\nTry again.",
        "activities": [],
        "total_cost": 0,
        "eco_score": 6,
        "carbon_saved": "0kg",
        "waste_free_score": 5,
        "plan_health_score": 50,
        "budget_breakdown": {},
        "experience_highlights": [],
        "trip_mood_indicator": {},
    }

# =========================
# Clean JSON Response
# =========================
def clean_json(text: str):
    if not text:
        return None
    text = text.replace("```json", "").replace("```", "")
    s, e = text.find("{"), text.rfind("}")
    if s == -1 or e == -1:
        return None
    return text[s:e + 1]


# =========================
# MAIN WORKFLOW CLASS
# =========================
class AgentWorkflow:

    def ask(self, prompt: str) -> Optional[str]:
        try:
            r = model.generate_content(prompt)
            return getattr(r, "text", None)
        except Exception as e:
            logger.error(f"LLM failed: {e}")
            return None

    def parse(self, txt: str):
        try:
            cleaned = clean_json(txt)
            if not cleaned:
                return None

            data = extract_json(cleaned)
            if not data:
                data = json.loads(cleaned)

            parsed = ItinerarySchema(**data)
            return parsed.model_dump()

        except Exception as e:
            logger.error(f"JSON parse error: {e}")
            return None

    # =======================
    # PLAN GENERATOR
    # =======================
    def run(self, query, rag_data, budget, interests, days, location, travelers, user_profile, priorities):
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

        raw = self.ask(prompt)
        parsed = self.parse(raw)

        return parsed if parsed else fallback_itinerary()

    # =======================
    # SAFE REFINER
    # =======================
    def refine_plan(self, previous_plan_json: Dict[str, Any], feedback_query: str):
        prompt = f"""
You are a travel plan refiner.
User feedback: "{feedback_query}"

Here is the previous JSON plan:
{json.dumps(previous_plan_json, ensure_ascii=False)}

Return a NEW improved JSON itinerary.
ALWAYS output valid JSON ONLY.
"""

        raw = self.ask(prompt)
        parsed = self.parse(raw)

        return parsed if parsed else previous_plan_json

    # =======================
    # PACKING LIST
    # =======================
    def generate_packing_list(self, plan_context, user_profile, list_type):
        prompt = PROMPTS["packing"].format(
            plan_context=plan_context,
            user_profile=user_profile,
            list_type=list_type
        )
        return self.ask(prompt) or "Could not generate packing list."

    # =======================
    # STORY
    # =======================
    def generate_story(self, plan_context, user_name):
        prompt = PROMPTS["story"].format(
            plan_context=plan_context,
            user_name=user_name
        )
        return self.ask(prompt) or "Could not generate story."

    # =======================
    # Q&A
    # =======================
    def ask_question(self, plan_context, question):
        prompt = PROMPTS["question"].format(
            plan_context=plan_context,
            question=question
        )
        return self.ask(prompt) or "Sorry, I couldn't answer."

    # =======================
    # UPGRADE (OPTIONAL)
    # =======================
    def get_upgrade_suggestions(self, plan_context, user_profile, rag_data):
        return "- Upgrade suggestions disabled for demo -"
