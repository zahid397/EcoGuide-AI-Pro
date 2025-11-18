import json
import traceback
from typing import Any, Dict, List

from backend.utils import extract_json


class AgentWorkflow:
    """
    AI workflow engine for generating trip itinerary.
    Works with any RAG results and produces structured JSON.
    """

    def __init__(self):
        # If you use Gemini:
        from openai import OpenAI
        self.client = OpenAI()  # Uses OPENAI_API_KEY or GOOGLE_API_KEY through env

    # ------------------------------------------------------------------
    def run(
        self,
        query: str,
        rag_data: List[Dict[str, Any]],
        budget: int,
        interests: List[str],
        days: int,
        location: str,
        travelers: int,
        user_profile: Dict[str, Any],
        priorities: Dict[str, int],
    ) -> Dict[str, Any]:
        """
        Main function to generate itinerary with AI help.
        Returns structured dict (JSON).
        """

        try:
            prompt = self._build_prompt(
                query=query,
                rag_data=rag_data,
                budget=budget,
                interests=interests,
                days=days,
                location=location,
                travelers=travelers,
                user_profile=user_profile,
                priorities=priorities,
            )

            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.4,
            )

            raw_output = response.choices[0].message["content"]

            parsed = extract_json(raw_output)
            if not parsed:
                return {
                    "error": "AI returned invalid JSON.",
                    "raw_response": raw_output,
                }

            return parsed

        except Exception as e:
            return {
                "error": str(e),
                "trace": traceback.format_exc(),
            }

    # ------------------------------------------------------------------
    def _build_prompt(
        self,
        query: str,
        rag_data: List[Dict[str, Any]],
        budget: int,
        interests: List[str],
        days: int,
        location: str,
        travelers: int,
        user_profile: Dict[str, Any],
        priorities: Dict[str, int],
    ) -> str:
        """
        Create structured AI prompt with instructions + JSON format.
        """

        rag_text = json.dumps(rag_data, indent=2)

        return f"""
You are EcoGuide AI — an expert eco-friendly travel planner.

User Query:
{query}

User Profile:
{json.dumps(user_profile, indent=2)}

Trip Preferences:
- Location: {location}
- Travelers: {travelers}
- Days: {days}
- Interests: {', '.join(interests)}
- Budget: {budget}
- Priorities: {priorities}

Eco-Friendly Options from Database (RAG results):
{rag_text}

=========================
IMPORTANT RESPONSE RULES
=========================
1. Always respond ONLY with **valid JSON**.
2. Do NOT include explanations outside the JSON.
3. The JSON MUST contain:

{
  "summary": "short overview of the trip",
  "daily_plan": [
     {
       "day": 1,
       "activities": [
          {
            "name": "",
            "eco_score": 0,
            "cost": 0,
            "location": "",
            "description": ""
          }
       ]
     }
  ],
  "estimated_total_cost": 0,
  "packing_list": [],
  "tips": []
}

4. Ensure activities come **only from RAG data**.
5. Ensure total cost does not exceed budget.
6. Make the trip realistic, eco-friendly and safe.
"""
