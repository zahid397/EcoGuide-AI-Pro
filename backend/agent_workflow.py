import os
import google.generativeai as genai
from backend.utils_json import extract_json
from utils.logger import logger

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))


def fallback_itinerary():
    return {
        "summary": "Fallback itinerary",
        "activities": [],
        "daily_plan": []
    }


class AgentWorkflow:
    def __init__(self):
        self.model = genai.GenerativeModel(
            "gemini-1.5-flash",
            generation_config={"response_mime_type": "application/json"}
        )

    # =====================================================
    # MAIN TRIP GENERATION
    # =====================================================
    def run(self, query, rag_data, budget, interests, days,
            location, travelers, user_profile, priorities):

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
                "location": location,
                "priorities": priorities,
                "user_profile": user_profile,
                "context_items": context_items
            }

            response = self.model.generate_content(prompt)

            try:
                raw = response.text
                parsed = extract_json(raw)
                if parsed:
                    return parsed
            except:
                pass

            return fallback_itinerary()

        except Exception as e:
            logger.exception(e)
            return fallback_itinerary()

    # =====================================================
    # PACKING LIST
    # =====================================================
    def generate_packing_list(self, itinerary, user_profile=None):

        prompt = {
            "task": "packing_list",
            "itinerary": itinerary,
            "user_profile": user_profile
        }

        try:
            response = self.model.generate_content(prompt)
            data = extract_json(response.text)
            return data or {"items": ["Passport", "Wallet", "Water Bottle"]}
        except:
            return {"items": ["Passport", "Wallet", "Water Bottle"]}

    # =====================================================
    # STORY
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
            return data or {"story": f"{user_name} had a peaceful eco-friendly adventure."}
        except:
            return {"story": f"{user_name} had a peaceful eco-friendly adventure."}

    # =====================================================
    # CHATBOT
    # =====================================================
    def ask_question(self, question, plan_context=None):

        prompt = {
            "task": "qa",
            "question": question,
            "context": plan_context
        }

        try:
            response = self.model.generate_content(prompt)
            data = extract_json(response.text)
            return data or {"answer": "Sorry, I could not answer that."}
        except:
            return {"answer": "Sorry, I could not answer that."}

    # =====================================================
    # UPGRADE SUGGESTIONS
    # =====================================================
    def get_upgrade_suggestions(self, itinerary):

        prompt = {
            "task": "upgrade_suggestions",
            "itinerary": itinerary
        }

        try:
            response = self.model.generate_content(prompt)
            data = extract_json(response.text)
            return data or {"suggestions": ["Try adding more eco-friendly activities."]}
        except:
            return {"suggestions": ["Try adding more eco-friendly activities."]}
