import os
import google.generativeai as genai
from backend.utils_json import extract_json
from utils.logger import logger

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))


# -----------------------------
# SAFE FALLBACK
# -----------------------------
def fallback(text="Not available"):
    return {"result": text}


# -----------------------------
# MAIN WORKFLOW
# -----------------------------
class AgentWorkflow:
    def __init__(self):
        self.model = genai.GenerativeModel(
            "gemini-1.5-flash",
            generation_config={"response_mime_type": "application/json"}
        )

    # =====================================================
    # MAIN TRIP PLAN GENERATOR
    # =====================================================
    def run(self, query, rag_data, budget, interests, days,
            location, travelers, user_profile, priorities):

        prompt = {
            "task": "generate_itinerary",
            "query": query,
            "budget": budget,
            "days": days,
            "travelers": travelers,
            "location": location,
            "interests": interests,
            "user_profile": user_profile,
            "priorities": priorities,
            "context_items": rag_data
        }

        try:
            response = self.model.generate_content(prompt)
            data = extract_json(response.text)
            return data or fallback("Could not make full plan")
        except Exception as e:
            logger.exception(e)
            return fallback()

    # =====================================================
    # PACKING LIST (UI calls with 3 args)
    # =====================================================
    def generate_packing_list(self, list_type, itinerary, user_profile=None):

        prompt = {
            "task": "packing_list",
            "list_type": list_type,
            "itinerary": itinerary,
            "user_profile": user_profile
        }

        try:
            response = self.model.generate_content(prompt)
            data = extract_json(response.text)
            return data or {"items": ["Passport", "Shoes", "Water Bottle"]}
        except:
            return {"items": ["Passport", "Shoes", "Water Bottle"]}

    # =====================================================
    # STORY (UI calls with 2 args)
    # =====================================================
    def generate_story(self, itinerary, user_name="Traveler"):

        prompt = {
            "task": "travel_story",
            "itinerary": itinerary,
            "user_name": user_name
        }

        try:
            response = self.model.generate_content(prompt)
            data = extract_json(response.text)
            return data or {"story": f"{user_name} had a nice eco trip."}
        except:
            return {"story": f"{user_name} had a nice eco trip."}

    # =====================================================
    # CHAT TAB (UI calls 2 args)
    # =====================================================
    def ask_question(self, question, itinerary):

        prompt = {
            "task": "qa",
            "question": question,
            "itinerary": itinerary
        }

        try:
            response = self.model.generate_content(prompt)
            data = extract_json(response.text)
            return data or {"answer": "Sorry, I couldn't answer that."}
        except:
            return {"answer": "Sorry, I couldn't answer that."}

    # =====================================================
    # UPGRADE (UI calls 1 arg)
    # =====================================================
    def get_upgrade_suggestions(self, itinerary):

        prompt = {
            "task": "upgrade_suggestions",
            "itinerary": itinerary
        }

        try:
            response = self.model.generate_content(prompt)
            data = extract_json(response.text)
            return data or {"suggestions": ["Try adding more eco activities."]}
        except:
            return {"suggestions": ["Try adding more eco activities."]}
