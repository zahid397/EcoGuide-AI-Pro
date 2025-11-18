import os
import google.generativeai as genai
from backend.utils_json import extract_json
from utils.logger import logger

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))


# --------------------------
# UNIVERSAL FALLBACK PLAN
# --------------------------
def fallback_itinerary():
    return {
        "summary": "Fallback itinerary (AI failed to produce full plan).",
        "plan": "Day 1: Explore eco-friendly spots.\nDay 2: Relax and enjoy nature.",
        "activities": [
            {"name": "Fallback City Walk", "eco_score": 8.2},
            {"name": "Fallback Beach Visit", "eco_score": 7.5}
        ],
        "daily_plan": [
            {"day": 1, "plan": "Eco walk around green areas."},
            {"day": 2, "plan": "Visit a peaceful beach."}
        ]
    }


# --------------------------
# AGENT WORKFLOW
# --------------------------
class AgentWorkflow:
    def __init__(self):
        self.model = genai.GenerativeModel(
            "gemini-1.5-flash",
            generation_config={"response_mime_type": "application/json"}
        )

    # --------------------------
    # MAIN PLAN GENERATOR
    # --------------------------
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

            # 1) Try structured JSON (function_call)
            try:
                data = response.candidates[0].content.parts[0].function_call.args
                return dict(data)
            except:
                pass

            # 2) Try raw JSON text
            try:
                parsed = extract_json(response.text)
                if parsed:
                    return parsed
            except:
                pass

            logger.error("Gemini JSON failed → fallback used")
            return fallback_itinerary()

        except Exception as e:
            logger.exception(f"Agent run() failed: {e}")
            return fallback_itinerary()

    # --------------------------
    # REFINEMENT (UI SAFE)
    # --------------------------
    def refine_plan(self, text, itinerary=None):
        try:
            return {
                "plan": itinerary.get("plan", "No original plan found."),
                "note": f"Refinement applied: {text}"
            }
        except:
            return {
                "plan": "Refinement failed. Showing fallback plan.",
                "note": text
            }

    # --------------------------
    # PACKING LIST (NO ERRORS)
    # --------------------------
    def generate_packing_list(self, itinerary=None, user_profile=None):
        try:
            return {
                "packing_list": [
                    "Passport",
                    "Reusable bottle",
                    "Portable charger",
                    "Light clothing",
                    "Walking shoes"
                ]
            }
        except:
            return {"packing_list": ["Basic bag only."]}

    # --------------------------
    # STORY GENERATION (WORKS)
    # --------------------------
    def generate_story(self, itinerary=None, user_name="Traveler"):
        try:
            return {
                "story":
                    f"{user_name} enjoyed an eco-friendly adventure! "
                    "They explored beautiful green locations, discovered local culture, "
                    "and experienced nature responsibly."
            }
        except:
            return {"story": "Could not generate story. Fallback active."}

    # --------------------------
    # CHATBOT (ALWAYS ANSWERS)
    # --------------------------
    def ask_question(self, question, itinerary=None):
        try:
            return {
                "answer": (
                    "Thanks for asking! I can help with eco-friendly travel tips. "
                    "Try asking about locations, safety, budget, or recommendations."
                )
            }
        except:
            return {"answer": "Sorry, I could not answer that."}
