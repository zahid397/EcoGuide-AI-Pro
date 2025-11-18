import os
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
# FALLBACK PLAN
# =========================
def fallback_itinerary():
    return {
        "plan": "Your eco-friendly trip plan is ready!",
        "activities": [],
        "eco_score": 7
    }

# =========================
# AGENT WORKFLOW (NO PROMPTS)
# =========================
class AgentWorkflow:

    def _ask(self, prompt: str) -> str:
        try:
            r = model.generate_content(prompt)
            return getattr(r, "text", "") or "Your trip is ready!"
        except:
            return "Your trip is ready!"

    # MAIN PLAN (MARKDOWN ONLY)
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
        priorities: Dict,
    ) -> Dict[str, Any]:

        try:
            prompt = f"""
You are an eco-friendly travel planner.

Generate a short travel plan in MARKDOWN.
NO JSON. NO codeblock. No special format.

User Query: {query}
Days: {days}
Travelers: {travelers}
Location: {location}
Budget: {budget}
Interests: {interests}
Priorities: {priorities}

Write a clear, friendly trip plan.
"""

            text = self._ask(prompt)

            return {
                "plan": text,
                "activities": [],
                "eco_score": 7
            }

        except:
            return fallback_itinerary()

    # SIMPLE REFINER
    def refine_plan(self, previous_plan_json, feedback_query):
        try:
            prompt = f"""
Refine the following trip plan based on feedback.
Write plain text only.

Feedback: {feedback_query}

Old plan:
{previous_plan_json}
"""
            refined = self._ask(prompt)
            return {"plan": refined}
        except:
            return previous_plan_json

    # PACKING LIST
    def generate_packing_list(self, plan_context, user_profile, list_type):
        return f"### {list_type} Packing List\n- Clothes\n- Water bottle\n- Eco-friendly items"

    # STORY
    def generate_story(self, plan_context, user_name):
        return f"{user_name} enjoyed an amazing, sustainable journey."

    # QUESTIONS
    def ask_question(self, plan_context, question):
        return f"Based on your plan → {question}"

    # UPGRADES
    def get_upgrade_suggestions(self, plan_context, user_profile, rag_data):
        return "- Upgrade hotel\n- Add premium eco activity\n- Explore hidden gems"
