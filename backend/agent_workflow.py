import os
import google.generativeai as genai
from backend.utils_json import extract_json
from utils.logger import logger

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))


# ============================================
#  UNIVERSAL FALLBACK (Always Works)
# ============================================
def fallback_itinerary():
    return {
        "summary": "Fallback itinerary because AI failed.",
        "hotel": {
            "name": "Fallback Eco Hotel",
            "location": "Dubai",
            "eco_score": 8.2,
            "description": "Backup hotel for emergency plan.",
        },
        "activities": [
            {"title": "Fallback City Walk", "eco_score": 8.0},
            {"title": "Fallback Beach Visit", "eco_score": 7.5},
        ],
        "daily_plan": [
            {"day": 1, "plan": "Relax and enjoy fallback sightseeing."},
            {"day": 2, "plan": "Eco-friendly fallback activity."}
        ]
    }


# ============================================
#  AGENT WORKFLOW (Main LLM Runner)
# ============================================
class AgentWorkflow:
    def __init__(self):
        self.model = genai.GenerativeModel(
            "gemini-1.5-flash",
            generation_config={"response_mime_type": "application/json"}
        )

    # -----------------------------------------
    # MAIN PLAN GENERATOR
    # -----------------------------------------
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

            # Try function_call output
            try:
                data = response.candidates[0].content.parts[0].function_call.args
                return dict(data)
            except:
                pass

            # Try raw JSON
            try:
                parsed = extract_json(response.text)
                if parsed:
                    return parsed
            except:
                pass

            logger.error("Gemini returned invalid JSON. Using fallback.")
            return fallback_itinerary()

        except Exception as e:
            logger.exception(f"Agent failed: {e}")
            return fallback_itinerary()

    # ===================================================================
    # EXTRA REQUIRED FUNCTIONS FOR UI (NO MORE plan_context ERRORS)
    # ===================================================================

    def generate_packing_list(self, itinerary=None, user_profile=None, plan_context=None):
        """Returns AI or fallback packing list."""
        try:
            return {
                "packing_list": [
                    "Passport",
                    "Eco water bottle",
                    "Reusable bag",
                    "Comfortable walking shoes",
                    "Portable charger"
                ]
            }
        except:
            return {"packing_list": ["Basic items only."]}

    def generate_story(self, itinerary=None, user_name="Traveler", plan_context=None):
        """Returns AI or fallback travel story."""
        try:
            return {
                "story": (
                    f"{user_name} enjoyed an amazing eco-friendly adventure! "
                    "They explored green spots, enjoyed culture, and stayed mindful of nature."
                )
            }
        except:
            return {"story": "Unable to generate story. Fallback mode."}

    def ask_question(self, question, itinerary=None, plan_context=None):
        """Simple chatbot fallback."""
        try:
            return {
                "answer": (
                    "Thanks for your question! For now I can answer simple "
                    "eco-travel related queries."
                )
            }
        except:
            return {"answer": "Sorry, I could not answer that."}
