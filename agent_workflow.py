import os
import json
from typing import Dict, Any, Optional, List

import google.generativeai as genai
from dotenv import load_dotenv
from pydantic import ValidationError

from utils import extract_json
from schemas import ItinerarySchema

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
MODEL_NAME = os.getenv("MODEL", "gemini-1.5-flash")

model = genai.GenerativeModel(
    MODEL_NAME,
    generation_config={"response_mime_type": "application/json"}
)

def _load_prompt(file):
    try:
        return open(f"prompts/{file}", "r", encoding="utf-8").read()
    except:
        return ""

PROMPTS = {
    "itinerary": _load_prompt("itinerary_prompt.txt"),
    "refine": _load_prompt("refine_prompt.txt"),
}

def fallback():
    return {
        "plan": "No plan generated.",
        "activities": [],
        "total_cost": 0
    }

class AgentWorkflow:

    def _ask(self, prompt):
        try:
            res = model.generate_content(prompt)
            return res.text
        except:
            return None

    def _clean(self, text):
        if not text: return ""
        c = text.replace("```json", "").replace("```", "")
        start, end = c.find("{"), c.rfind("}")
        return c[start:end+1] if start != -1 else c

    def _parse(self, text):
        try:
            cleaned = self._clean(text)
            try:
                data = json.loads(cleaned)
            except:
                data = extract_json(cleaned)

            if not data:
                return None

            obj = ItinerarySchema(**data)
            return obj.model_dump()

        except:
            return None

    def run(self, query, rag_data, budget, interests, days, location, travelers, user_profile, priorities):

        prompt = PROMPTS["itinerary"].format(
            query=query,
            days=days,
            travelers=travelers,
            budget=budget,
            eco_priority=priorities["eco"],
            budget_priority=priorities["budget"],
            comfort_priority=priorities["comfort"],
            user_name=user_profile["name"],
            user_interests=user_profile["interests"],
            profile_ack="",
            rag_data=rag_data
        )

        raw = self._ask(prompt)
        if not raw:
            return fallback()

        parsed = self._parse(raw)
        return parsed or fallback()

    def refine_plan(self, prev_json, feedback):
        prompt = PROMPTS["refine"].format(
            feedback_query=feedback,
            previous_plan_json=json.dumps(prev_json)
        )
        raw = self._ask(prompt)
        parsed = self._parse(raw)
        return parsed or prev_json
