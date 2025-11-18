import os
import json
import google.generativeai as genai
from dotenv import load_dotenv
from backend.utils import extract_json
from utils.schemas import ItinerarySchema
from utils.logger import logger
from pydantic import ValidationError
from typing import Dict, Any, Optional, List

# ================================
# Gemini Setup (USE 2.5-FLASH)
# ================================
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

MODEL_NAME = "gemini-2.5-flash"   # ❤️ BEST MODEL

model = genai.GenerativeModel(
    MODEL_NAME,
    safety_settings=[
        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
    ],
    generation_config={
        "temperature": 0.6,
        "max_output_tokens": 8192,
        "top_p": 0.95
    }
)

# ================================
# SAFE FALLBACK (NEVER FAILS)
# ================================
def fallback_itinerary():
    return {
        "plan": "## No plan generated.",
        "activities": [],
        "total_cost": 0,
        "eco_score": 7,
        "carbon_saved": "0kg",
        "waste_free_score": 5,
        "plan_health_score": 60,
        "budget_breakdown": {},
        "carbon_offset_suggestion": "",
        "ai_image_prompt": "",
        "ai_time_planner_report": "",
        "cost_leakage_report": "",
        "risk_safety_report": "",
        "weather_contingency": "",
        "duplicate_trip_detector": "",
        "experience_highlights": [],
        "trip_mood_indicator": {}
    }

# ================================
# Agent Workflow
# ================================
class AgentWorkflow:

    # ---------------------------------------
    # Safe Gemini Caller (NEVER RETURNS NONE)
    # ---------------------------------------
    def _ask(self, prompt: str) -> str:
        try:
            response = model.generate_content(prompt)

            # Primary
            if hasattr(response, "text") and response.text:
                return response.text

            # Candidate fallback
            if response.candidates:
                parts = response.candidates[0].content.parts
                if parts and hasattr(parts[0], "text"):
                    return parts[0].text

            logger.error("⚠ Gemini returned empty text.")
            return "{}"

        except Exception as e:
            logger.error(f"⚠ Gemini API Error → {e}")
            return "{}"

    # ---------------------------------------
    # Clean Output → Extract Only JSON
    # ---------------------------------------
    def _clean_output(self, text: str) -> str:
        if not text:
            return "{}"

        text = text.replace("```json", "").replace("```", "").strip()
        start = text.find("{")
        end = text.rfind("}")

        if start == -1 or end == -1:
            return "{}"

        return text[start: end+1]

    # ---------------------------------------
    # Validate JSON Using Schema
    # ---------------------------------------
    def _validate(self, raw: str):
        try:
            cleaned = self._clean_output(raw)

            try:
                data = json.loads(cleaned)
            except:
                data = extract_json(cleaned)

            if not data:
                raise ValueError("LLM returned empty JSON")

            schema = ItinerarySchema(**data)
            return schema.model_dump()

        except Exception as e:
            logger.error(f"⚠ JSON Validation Failed → {e}")
            return None

    # ---------------------------------------
    # RUN → Generate the Plan
    # ---------------------------------------
    def run(self, query, rag_data, budget, interests, days, location, travelers, user_profile, priorities):

        prompt = f"""
You are an expert sustainable travel planner.
Generate a full eco-friendly itinerary.

User Query: {query}
Days: {days}, Travelers: {travelers}, Budget: {budget}
User Profile: {user_profile}
Priorities: {priorities}
RAG Data: {rag_data}

Return **VALID JSON ONLY** following EXACTLY this schema:
{{
  "plan": "Markdown plan...",
  "activities": [],
  "total_cost": 0,
  "eco_score": 8,
  "carbon_saved": "20kg",
  "waste_free_score": 8,
  "plan_health_score": 85,
  "budget_breakdown": {{"Hotel": 500}},
  "carbon_offset_suggestion": "",
  "ai_image_prompt": "",
  "ai_time_planner_report": "",
  "cost_leakage_report": "",
  "risk_safety_report": "",
  "weather_contingency": "",
  "duplicate_trip_detector": "",
  "experience_highlights": [],
  "trip_mood_indicator": {{"Adventure": 60}}
}}
"""

        raw = self._ask(prompt)
        parsed = self._validate(raw)

        return parsed if parsed else fallback_itinerary()

    # ---------------------------------------
    # REFINE PLAN
    # ---------------------------------------
    def refine_plan(self, prev_plan, feedback):
        prompt = f"""
You refine travel itineraries.

User Feedback: "{feedback}"
Previous Plan:
{json.dumps(prev_plan, indent=2)}

Return NEW **VALID JSON ONLY**.
"""

        raw = self._ask(prompt)
        parsed = self._validate(raw)

        return parsed if parsed else prev_plan

    # ---------------------------------------
    # PACKING LIST
    # ---------------------------------------
    def generate_packing_list(self, plan_context, user_profile, list_type):
        prompt = f"""
Generate a travel packing list.

Plan: {plan_context}
User Profile: {user_profile}
List Type: {list_type}

Return Markdown ONLY.
"""
        return self._ask(prompt)

    # ---------------------------------------
    # STORY
    # ---------------------------------------
    def generate_story(self, plan_context, user_name):
        prompt = f"""
Write a short travel story for {user_name}.

Plan: {plan_context}
Return Markdown only.
"""
        return self._ask(prompt)

    # ---------------------------------------
    # CHATBOT Q/A
    # ---------------------------------------
    def ask_question(self, plan_context, question):
        prompt = f"""
Answer the user's question based on this plan.

Plan: {plan_context}
Question: {question}

Keep the answer short.
"""
        return self._ask(prompt)

    # ---------------------------------------
    # UPGRADE SUGGESTIONS
    # ---------------------------------------
    def get_upgrade_suggestions(self, plan_context, user_profile, rag_data):
        prompt = f"""
Suggest 4 premium upgrades.

Plan: {plan_context}
User Profile: {user_profile}
RAG Data: {rag_data}

Return Markdown list only.
"""
        return self._ask(prompt)
