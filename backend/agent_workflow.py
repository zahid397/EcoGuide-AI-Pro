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
        "summary": "This is an auto-generated fallback itinerary because the AI could not produce a valid response.",
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
            {"day": 1, "plan": "Relax, fallback sightseeing."},
            {"day": 2, "plan": "Eco-friendly fallback activity."}
        ]
    }


# ============================================
#  AGENT WORKFLOW (WITH FORCED JSON + FALLBACK)
# ============================================
class AgentWorkflow:
    def __init__(self):
        # Force Gemini to return PURE JSON ONLY
        self.model = genai.GenerativeModel(
            "gemini-1.5-flash",
            generation_config={
                "response_mime_type": "application/json"  # 🔥 Forces JSON output
            }
        )

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
            # Prepare RAG context for the LLM
            context_items = []
            for item in rag_data:
                context_items.append({
                    "name": item.get("name", ""),
                    "type": item.get("data_type", ""),
                    "location": item.get("location", ""),
                    "eco_score": item.get("eco_score", 0),
                    "description": item.get("description", "")
                })

            # Build full prompt
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

            # Request JSON-only answer
            response = self.model.generate_content(prompt)

            # -----------------------
            # 1st Attempt: Function Call
            # -----------------------
            try:
                data = response.candidates[0].content.parts[0].function_call.args
                return dict(data)
            except:
                pass

            # -----------------------
            # 2nd Attempt: Raw JSON Extraction
            # -----------------------
            try:
                raw_text = response.text
                parsed = extract_json(raw_text)
                if parsed:
                    return parsed
            except:
                pass

            # -----------------------
            # 3rd Attempt: FALLBACK
            # -----------------------
            logger.error("Gemini failed to produce usable JSON. Using fallback.")
            return fallback_itinerary()

        except Exception as e:
            logger.exception(f"Agent failed: {e}")
            return fallback_itinerary()
