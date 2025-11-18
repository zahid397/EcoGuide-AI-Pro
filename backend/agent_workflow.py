import os
import json
from dotenv import load_dotenv
import google.generativeai as genai
from utils.schemas import ItinerarySchema
from utils.logger import logger
from utils.extract import extract_json  # <-- your simple extractor
from typing import Dict, Any, Optional, List

# Load environment variables
load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
MODEL_NAME = os.getenv("MODEL", "gemini-1.5-flash")

# Safety Off
safety_settings = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
]

model = genai.GenerativeModel(MODEL_NAME, safety_settings=safety_settings)


# =========================
# DEFAULT PROMPT (NO FILE NEEDED)
# =========================
DEFAULT_ITINERARY_PROMPT = """
You are an expert eco-travel planner. Create a detailed JSON itinerary.

User Query: {query}
Days: {days}
Travelers: {travelers}
Budget: ${budget}

Priorities:
- Eco: {eco_priority}/10
- Budget: {budget_priority}/10
- Comfort: {comfort_priority}/10

Profile: 
User name: {user_name}
User interests: {user_interests}

RAG Data (Recommended Activities):
{rag_data}

INSTRUCTIONS:
1. Create a day-by-day Markdown plan.
2. Select activities that match eco-score, budget, and interests.
3. Ensure JSON output strictly follows this schema:

{
  "plan": "Markdown itinerary...",
  "activities": [ LIST OF SELECTED ACTIVITIES FROM RAG DATA ],
  "total_cost": 0,
  "eco_score": 8.2,
  "carbon_saved": "14kg",
  "waste_free_score": 7,
  "plan_health_score": 85,
  "budget_breakdown": { "Hotel": 200, "Food": 60 }
}

RETURN **ONLY JSON** WITH NO MARKDOWN OUTSIDE.
"""


class ItineraryAgent:

    def _render_template(self, template: str, **kwargs) -> str:
        """Simple string formatter"""
        try:
            return template.format(**kwargs)
        except Exception as e:
            logger.error(f"Template formatting error: {e}")
            return template

    # =========================
    # Main AI Function
    # =========================
    def run(
        self,
        query: str,
        days: int,
        travelers: int,
        budget: float,
        priorities: Dict[str, int],
        rag_data: List[Dict[str, Any]],
        user_profile: Dict[str, Any]
    ) -> Dict[str, Any]:

        try:
            # Build prompt
            prompt = self._render_template(
                DEFAULT_ITINERARY_PROMPT,
                query=query,
                days=days,
                travelers=travelers,
                budget=budget,
                eco_priority=priorities.get("eco", 5),
                budget_priority=priorities.get("budget", 5),
                comfort_priority=priorities.get("comfort", 5),
                user_name=user_profile.get("name", "Traveler"),
                user_interests=user_profile.get("interests", "travel"),
                rag_data=json.dumps(rag_data, indent=2)
            )

            # Call Gemini
            ai_response = model.generate_content(
                prompt,
                generation_config={"temperature": 0.7, "max_output_tokens": 8192}
            )

            raw_text = ai_response.text

            # Extract JSON (safe)
            data = extract_json(raw_text)

            # Validate JSON with Pydantic
            validated = ItinerarySchema(**data)

            logger.info("Itinerary generated successfully.")
            return validated.dict()

        except Exception as e:
            logger.error(f"AI generation error: {e}")
            return {
                "error": "AI agent failed to generate itinerary.",
                "details": str(e),
                "plan": "Unable to create itinerary. Please try again later.",
                "activities": rag_data[:5],  # fallback activities
                "total_cost": 0,
                "eco_score": 5,
                "carbon_saved": "0kg",
                "waste_free_score": 5,
                "plan_health_score": 50,
                "budget_breakdown": {}
            }
