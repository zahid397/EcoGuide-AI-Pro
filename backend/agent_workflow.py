import os
import google.generativeai as genai
from backend.utils_json import extract_json
from utils.logger import logger

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))


def fallback_itinerary():
    return {
        "summary": "Fallback itinerary because the AI could not produce a valid response.",
        "hotel": {"name": "Fallback Eco Hotel", "location": "Dubai", "eco_score": 8.2},
        "activities": [{"title": "City Walk", "eco_score": 8.0}],
        "daily_plan": [{"day": 1, "plan": "Exploration fallback activity."}],
    }


class AgentWorkflow:
    def __init__(self):
        self.model = genai.GenerativeModel(
            "gemini-1.5-flash",
            generation_config={"response_mime_type": "application/json"}
        )

    # -------------------------------------------------
    # MAIN ITINERARY GENERATION
    # -------------------------------------------------
    def run(self, query, rag_data, budget, interests, days, location, travelers, user_profile, priorities):
        try:
            context_items = []
            for item in rag_data:
                context_items.append({
                    "name": item.get("name", ""),
                    "type": item.get("data_type", ""),
                    "location": item.get("location", ""),
                    "eco_score": item.get("eco_score", 0),
                    "description": item.get("description", "")
                })

            prompt = {
                "query": query,
                "budget": budget,
                "days": days,
                "travelers": travelers,
                "interests": interests,
                "priorities": priorities,
                "user_profile": user_profile,
                "context_items": context_items
            }

            response = self.model.generate_content(prompt)

            # Direct function-call style JSON
            try:
                data = response.candidates[0].content.parts[0].function_call.args
                return dict(data)
            except:
                pass

            # Parse raw JSON
            try:
                parsed = extract_json(response.text)
                if parsed:
                    return parsed
            except:
                pass

            logger.error("Gemini failed to create JSON. Using fallback.")
            return fallback_itinerary()

        except Exception as e:
            logger.exception(f"Agent failed: {e}")
            return fallback_itinerary()

    # -------------------------------------------------
    # UPGRADE SUGGESTIONS (FIXED)
    # Always accepts **plan_context** (no error ever)
    # -------------------------------------------------
    def get_upgrade_suggestions(self, plan_context=None):
        """
        FIXED: plan_context is optional now.
        Your Streamlit UI can call this safely.
        """

        try:
            prompt = {
                "task": "Suggest upgrades based on the plan.",
                "plan_context": plan_context or "No context available."
            }

            response = self.model.generate_content(prompt)

            parsed = extract_json(response.text)
            if parsed:
                return parsed

            return {
                "upgrades": [
                    "Upgrade to eco-hotel premium room.",
                    "Add sustainable city bike tour.",
                    "Include organic dining experience."
                ]
            }

        except Exception as e:
            logger.exception(f"Upgrade suggestion failed: {e}")
            return {
                "upgrades": [
                    "Eco-upgrade suggestion unavailable — fallback mode.",
                ]
            }
