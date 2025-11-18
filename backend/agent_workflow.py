import os
import google.generativeai as genai
from backend.utils_json import extract_json
from utils.logger import logger

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))


def fallback_itinerary():
    return {
        "summary": "Fallback itinerary (AI failed).",
        "hotel": {"name": "Fallback Hotel", "location": "Dubai"},
        "activities": [
            {"title": "Fallback City Walk"},
            {"title": "Fallback Beach Visit"}
        ],
        "daily_plan": [
            {"day": 1, "plan": "Fallback sightseeing"},
            {"day": 2, "plan": "Fallback activity"}
        ]
    }


class AgentWorkflow:
    def __init__(self):
        self.model = genai.GenerativeModel(
            "gemini-1.5-flash",
            generation_config={"response_mime_type": "application/json"}
        )

    # ==================================================
    # MAIN GENERATOR
    # ==================================================
    def run(self, **kwargs):
        try:
            response = self.model.generate_content(kwargs)
            data = None

            # Try function_call output
            try:
                data = response.candidates[0].content.parts[0].function_call.args
                return dict(data)
            except:
                pass

            # Try normal JSON text
            try:
                data = extract_json(response.text)
                if data:
                    return data
            except:
                pass

            logger.error("Gemini returned invalid JSON. Using fallback.")
            return fallback_itinerary()

        except Exception as e:
            logger.exception(e)
            return fallback_itinerary()

    # ==================================================
    # REFINE PLAN — (THIS FIXES YOUR ERROR)
    # ==================================================
    def refine_plan(self, itinerary, refinement_query):
        try:
            prompt = {
                "task": "refine_existing_plan",
                "refinement_query": refinement_query,
                "current_plan": itinerary
            }

            response = self.model.generate_content(prompt)

            # Try function_call
            try:
                data = response.candidates[0].content.parts[0].function_call.args
                return dict(data)
            except:
                pass

            # Try JSON
            parsed = extract_json(response.text)
            if parsed:
                return parsed

            logger.error("Refine failed, using fallback.")
            return itinerary  # Keep old plan

        except Exception as e:
            logger.exception(e)
            return itinerary
