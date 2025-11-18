import os
import json
from typing import Dict, Any, Optional, List

import google.generativeai as genai
from dotenv import load_dotenv
from pydantic import ValidationError

from backend.utils import extract_json
from utils.schemas import ItinerarySchema
from utils.logger import logger

# ==========================================
# Gemini Setup
# ==========================================
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
MODEL_NAME = os.getenv("MODEL", "gemini-1.5-flash")

model = genai.GenerativeModel(
    MODEL_NAME,
    generation_config={"response_mime_type": "application/json"}
)

# ==========================================
# Load prompts
# ==========================================
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
}

# ==========================================
# Safe Fallback
# ==========================================
def fallback_itinerary():
    return {
        "plan": "## Fallback Plan\nAI failed, generating a simple backup plan.",
        "activities": [],
        "total_cost": 0,
        "eco_score": 5,
        "carbon_saved": "0kg",
        "budget_breakdown": {},
        "waste_free_score": 5,
        "plan_health_score": 50,
        "experience_highlights": [],
        "trip_mood_indicator": {},
    }

# ==========================================
# Helper: Clean JSON TXT
# ==========================================
def clean_json(txt: str):
    if not txt:
        return None
    txt = txt.replace("```json", "").replace("```", "")
    start = txt.find("{")
    end = txt.rfind("}")
    if start == -1 or end == -1:
        return None
    return txt[start:end+1]


# ==========================================
# AGENT WORKFLOW (FINAL SOLID VERSION)
# ==========================================
class AgentWorkflow:

    # ---------------- Ask Gemini ----------------
    def ask(self, prompt: str) -> Optional[str]:
        try:
            response = model.generate_content(prompt)
            return response.text
        except:
            return None

    # ---------------- Validate JSON ----------------
    def parse_json(self, txt: str) -> Optional[Dict[str, Any]]:
        try:
            cleaned = clean_json(txt)
            if not cleaned:
                return None

            raw = extract_json(cleaned)
            if not raw:
                raw = json.loads(cleaned)

            parsed = ItinerarySchema(**raw)
            return parsed.model_dump()

        except:
            return None

    # ---------------- Generate Plan ----------------
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
        parsed = self.parse_json(raw)
        return parsed if parsed else fallback_itinerary()

    # ---------------- Refine Plan ----------------
    def refine_plan(self, old_json, feedback):
        prompt = PROMPTS["refine"].format(
            previous_plan_json=json.dumps(old_json),
            feedback_query=feedback,
            user_profile={},
            priorities={},
            rag_data=[],
            travelers=1,
            days=3,
            budget=1000
        )
        raw = self.ask(prompt)
        parsed = self.parse_json(raw)
        return parsed if parsed else old_json

    # ---------------- Packing ----------------
    def generate_packing_list(self, plan_context, user_profile, list_type):
        prompt = PROMPTS["packing"].format(
            plan_context=plan_context,
            user_profile=user_profile,
            list_type=list_type
        )
        return self.ask(prompt) or "Could not generate packing list."

    # ---------------- Story ----------------
    def generate_story(self, plan_context, user_name):
        prompt = PROMPTS["story"].format(
            plan_context=plan_context,
            user_name=user_name
        )
        return self.ask(prompt) or "Could not generate story."

    # ---------------- Chat ----------------
    def ask_question(self, plan_context, question):
        prompt = PROMPTS["question"].format(
            plan_context=plan_context,
            question=question
        )
        return self.ask(prompt) or "Sorry, I don't know."
