import os
import google.generativeai as genai
from dotenv import load_dotenv
from utils_json import extract_json
from schemas import ItinerarySchema
import json
from pydantic import ValidationError

# LOAD ENV
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

MODEL_NAME = "gemini-1.5-flash"

model = genai.GenerativeModel(
    model_name=MODEL_NAME,
    generation_config={"response_mime_type": "application/json"}
)

def fallback_itinerary():
    return {
        "plan": "No itinerary generated.",
        "activities": [],
        "total_cost": 0,
        "eco_score": 7.0,
        "carbon_saved": "0kg",
        "waste_free_score": 5,
        "plan_health_score": 50,
        "budget_breakdown": {},
        "carbon_offset_suggestion": "Plant a tree.",
        "ai_image_prompt": "Eco travel.",
        "ai_time_planner_report": "Basic schedule.",
        "cost_leakage_report": "None.",
        "risk_safety_report": "Standard safety.",
        "weather_contingency": "Check forecast.",
        "duplicate_trip_detector": "Unique trip.",
        "experience_highlights": [],
        "trip_mood_indicator": {}
    }

class AgentWorkflow:

    def _ask(self, prompt: str):
        try:
            res = model.generate_content(prompt)
            return res.text
        except:
            return None

    def _validate(self, llm_output: str):
        try:
            data = extract_json(llm_output)
            parsed = ItinerarySchema(**data)
            return parsed.model_dump()
        except:
            return None

    def run(self, query, rag_data, budget, interests, days, location, travelers, user_profile, priorities):
        prompt = open("prompts/itinerary_prompt.txt").read().format(
            query=query,
            days=days,
            travelers=travelers,
            budget=budget,
            eco_priority=priorities["eco"],
            budget_priority=priorities["budget"],
            comfort_priority=priorities["comfort"],
            user_name=user_profile["name"],
            user_interests=user_profile.get("interests", []),
            profile_ack="",
            rag_data=rag_data
        )
        raw = self._ask(prompt)
        parsed = self._validate(raw)
        return parsed or fallback_itinerary()

    def refine_plan(self, previous_plan_json, feedback_query, rag_data, user_profile, priorities, travelers, days, budget):
        prompt = open("prompts/refine_prompt.txt").read().format(
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
        parsed = self._validate(raw)
        return parsed or fallback_itinerary()

    def ask_question(self, plan_context, question):
        prompt = open("prompts/question_prompt.txt").read().format(
            plan_context=plan_context,
            question=question
        )
        return self._ask(prompt) or "Could not answer."

    def generate_packing_list(self, plan_context, user_profile, list_type):
        prompt = open("prompts/packing_prompt.txt").read().format(
            plan_context=plan_context,
            user_profile=user_profile,
            list_type=list_type
        )
        return self._ask(prompt) or "Could not generate packing list."

    def generate_story(self, plan_context, user_name):
        prompt = open("prompts/story_prompt.txt").read().format(
            plan_context=plan_context,
            user_name=user_name
        )
        return self._ask(prompt) or "Could not generate story."
