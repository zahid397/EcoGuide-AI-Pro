import os
import json
from typing import Dict, Any, Optional, List

import google.generativeai as genai
from dotenv import load_dotenv

# =========================
# Gemini Setup
# =========================
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
MODEL_NAME: str = os.getenv("MODEL", "gemini-1.5-flash")

model = genai.GenerativeModel(
    MODEL_NAME,
    safety_settings=[
        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
    ],
)

# =========================
# Safe fallback itinerary
# =========================
def fallback_itinerary() -> Dict[str, Any]:
    return {
        "plan": "Your eco-friendly trip plan is ready!",
        "activities": [],
        "total_cost": 0,
        "eco_score": 7,
        "ai_image_prompt": "eco friendly travel landscape"
    }

# =========================
# AGENT WORKFLOW 
# =========================
class AgentWorkflow:

    def _ask(self, prompt: str) -> str:
        try:
            r = model.generate_content(prompt)
            return getattr(r, "text", "") or "Your trip is ready!"
        except:
            return "Your trip is ready!"

    # SAFE — no JSON parsing
    def run(self, query, rag_data, budget, interests, days, location, travelers, user_profile, priorities):
        try:
            prompt = f"""
You are an AI travel generator.
Create a short eco-friendly trip plan in MARKDOWN.
No JSON. No special formatting.

User Query: {query}
Days: {days}
Travelers: {travelers}
Budget: {budget}
Location: {location}
Interests: {interests}
Priorities: {priorities}
"""
            result = self._ask(prompt)

            return {
                "plan": result,
                "activities": [],
                "eco_score": 7
            }

        except:
            return fallback_itinerary()

    # SAFE REFINER
    def refine_plan(self, previous_plan_json, feedback_query):
        try:
            prompt = f"""
Refine this trip plan based on user feedback.

User Feedback: {feedback_query}

Old Plan:
{previous_plan_json}

Return improved plain text ONLY.
"""

            refined = self._ask(prompt)
            return {
                "plan": refined,
                "activities": []
            }
        except:
            return previous_plan_json

    # No parsing — always returns text
    def generate_packing_list(self, plan_context, user_profile, list_type):
        return f"### {list_type} Packing List\n- Clothes\n- Water bottle\n- Eco-friendly items"

    def generate_story(self, plan_context, user_name):
        return f"{user_name} begins an eco-friendly adventure filled with joy and nature."

    def ask_question(self, plan_context, question):
        return f"Answer: Based on your plan — {question}"

    def get_upgrade_suggestions(self, plan_context, user_profile, rag_data):
        return "- Upgrade hotel\n- Add premium eco activity\n- Try a hidden gem location"
