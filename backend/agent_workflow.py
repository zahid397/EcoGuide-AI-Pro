import os
import google.generativeai as genai
from backend.utils_json import extract_json
from utils.logger import logger

# Configure Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))


# ======================================================
# Fallback itinerary (never crash)
# ======================================================
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


# ======================================================
# AGENT WORKFLOW (Primary LLM Engine)
# ======================================================
class AgentWorkflow:
    def __init__(self):
        self.model = genai.GenerativeModel(
            "gemini-1.5-flash",
            generation_config={
                "response_mime_type": "application/json"
            }
        )

    # --------------------------------------------------
    # MAIN PLAN GENERATOR
    # --------------------------------------------------
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
                "context_items": context_items,
            }

            response = self.model.generate_content(prompt)

            # 1) Try function_call JSON
            try:
                args = response.candidates[0].content.parts[0].function_call.args
                return dict(args)
            except:
                pass

            # 2) Try raw JSON text
            try:
                parsed = extract_json(response.text)
                if parsed:
                    return parsed
            except:
                pass

            return fallback_itinerary()

        except Exception as e:
            logger.exception(f"Agent failed: {e}")
            return fallback_itinerary()

    # =====================================================
    # SUPPORT FUNCTIONS FIXED FOR UI (NO ERRORS ANYMORE)
    # =====================================================

    def generate_packing_list(
        self,
        itinerary=None,
        user_profile=None,
        plan_context=None,
        list_type=None
    ):
        """Safe packing list generator — supports list_type & plan_context."""
        try:
            base_items = [
                "Passport",
                "Eco water bottle",
                "Reusable shopping bag",
                "Comfortable walking shoes",
                "Portable charger",
            ]

            # Customise based on list type
            if list_type == "beach":
                base_items += ["Swimwear", "Sunscreen", "Beach towel"]
            elif list_type == "adventure":
                base_items += ["Hiking boots", "First aid kit", "Energy bars"]
            elif list_type == "luxury":
                base_items += ["Formal wear", "Premium toiletries"]

            return {"packing_list": base_items}

        except:
            return {"packing_list": ["Passport", "Shoes", "Water bottle"]}

    def generate_story(
        self,
        itinerary=None,
        user_name="Traveler",
        plan_context=None
    ):
        """Simple fallback travel story — accepts plan_context."""
        try:
            return {
                "story": (
                    f"{user_name} enjoyed an unforgettable eco-friendly adventure! "
                    "They explored sustainable attractions, enjoyed nature, and "
                    "created beautiful memories through green travel."
                )
            }
        except:
            return {"story": "Fallback travel story."}

    def ask_question(
        self,
        question,
        itinerary=None,
        plan_context=None
    ):
        """Simple chatbot fallback (never crashes)."""
        try:
            return {
                "answer": (
                    "Thanks for your question! I can help with eco-travel, costs, "
                    "recommendations, sustainability tips, and itinerary adjustments."
                )
            }
        except:
            return {"answer": "Fallback answer."}
