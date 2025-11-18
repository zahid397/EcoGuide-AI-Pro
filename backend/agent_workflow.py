import os
import google.generativeai as genai
from backend.utils_json import extract_json
from utils.logger import logger

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))


def fallback_itinerary():
    return {
        "summary": "Fallback itinerary because main AI failed.",
        "hotel": {"name": "Fallback Hotel", "location": "Dubai", "eco_score": 8.2},
        "activities": [
            {"title": "Fallback Walk", "eco_score": 8.0},
            {"title": "Fallback Beach", "eco_score": 7.5},
        ],
        "daily_plan": [
            {"day": 1, "plan": "Relax and fallback sightseeing"},
            {"day": 2, "plan": "Eco-friendly fallback activity"},
        ],
    }


class AgentWorkflow:

    def __init__(self):
        self.model = genai.GenerativeModel(
            "gemini-1.5-flash",
            generation_config={"response_mime_type": "application/json"},
        )

    # ===================================================
    # MAIN RESPONSE (ITINERARY)
    # ===================================================
    def run(self, query, rag_data, budget, interests, days, location, travelers, user_profile, priorities):
        try:
            context_items = [
                {
                    "name": item.get("name", ""),
                    "type": item.get("data_type", ""),
                    "location": item.get("location", ""),
                    "eco_score": item.get("eco_score", 0),
                    "description": item.get("description", ""),
                }
                for item in rag_data
            ]

            prompt = {
                "query": query,
                "budget": budget,
                "days": days,
                "travelers": travelers,
                "interests": interests,
                "priorities": priorities,
                "user_profile": user_profile,
                "context_items": context_items,
            }

            response = self.model.generate_content(prompt)

            # Try function-call JSON
            try:
                args = response.candidates[0].content.parts[0].function_call.args
                return dict(args)
            except:
                pass

            # Try parse JSON
            try:
                parsed = extract_json(response.text)
                if parsed:
                    return parsed
            except:
                pass

            logger.error("Gemini failed — fallback used.")
            return fallback_itinerary()

        except Exception as e:
            logger.exception(f"Agent failed: {e}")
            return fallback_itinerary()

    # ===================================================
    # UPGRADE SUGGESTIONS (EXACT SIGNATURE FIX)
    # ===================================================
    def get_upgrade_suggestions(self, plan_context=None):
        """
        FIX: Streamlit calls this function with plan_context=...
        So we must accept that keyword.
        """
        try:
            prompt = {
                "task": "Suggest optional premium upgrades based on the user's plan.",
                "plan_context": plan_context or "No plan data provided."
            }

            response = self.model.generate_content(prompt)

            parsed = extract_json(response.text)
            if parsed:
                return parsed

            # fallback simple list
            return {
                "upgrades": [
                    "Premium eco-hotel upgrade",
                    "Organic dining add-on",
                    "Private EV sightseeing tour"
                ]
            }

        except Exception as e:
            logger.exception(f"Upgrade suggestion failed: {e}")
            return {
                "upgrades": [
                    "Upgrade suggestion unavailable — fallback mode"
                ]
            }
