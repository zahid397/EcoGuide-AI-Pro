import os
import google.generativeai as genai
from backend.utils_json import extract_json
from utils.logger import logger

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))


class AgentWorkflow:
    def __init__(self):
        self.model = genai.GenerativeModel("gemini-1.5-flash")

    def run(
        self,
        query,
        rag_data,
        budget,
        interests,
        days,
        location,
        travelers,
        user_profile,
        priorities
    ):
        try:
            context = ""
            for item in rag_data:
                context += (
                    f"- {item.get('name')} ({item.get('data_type')}) | "
                    f"{item.get('location')} | eco={item.get('eco_score')}\n"
                )

            prompt = f"""
You are an AI Eco Travel Planner.
Your job is to create an itinerary using ONLY these items:

{context}

Trip: {query}
Budget: {budget}
Days: {days}
Travelers: {travelers}
User Interests: {interests}

Return ONLY JSON in this structure:

{{
  "summary": "...",
  "hotel": {{ "name": "", "location": "", "eco_score": 0, "reason": "" }},
  "daily_plan": [
      {{ "day": 1, "activity": "", "location": "", "eco_score": 0, "reason": "" }}
  ],
  "total_estimated_cost": 0
}}
"""

            response = self.model.generate_content(prompt)
            raw = response.text
            data = extract_json(raw)

            if not data:
                logger.error("MODEL JSON FAILED: " + raw)
                return None

            return data

        except Exception as e:
            logger.exception(f"Agent failed: {e}")
            return None
