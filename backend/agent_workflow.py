import json
from typing import Dict, Any, List
from utils.logger import logger
from backend.utils_json import extract_json


class AgentWorkflow:
    """
    AI Agent: Takes RAG results + user info → builds final itinerary.
    Works even if LLM returns half-json, broken text, or missing fields.
    """

    def __init__(self):
        pass

    # ----------------------------------------------------------------------
    def run(
        self,
        query: str,
        rag_data: List[Dict[str, Any]],
        budget: float,
        interests: List[str],
        days: int,
        location: str,
        travelers: int,
        user_profile: Dict[str, Any],
        priorities: Dict[str, Any]
    ) -> Dict[str, Any]:

        try:
            # 💡 Build prompt for LLM
            prompt = self._build_prompt(
                query=query,
                rag_data=rag_data,
                budget=budget,
                interests=interests,
                days=days,
                location=location,
                travelers=travelers,
                user_profile=user_profile,
                priorities=priorities
            )

            # --------------------------------
            # 💬 CALL LLM (Gemini or GPT)
            # --------------------------------
            # তুমি এখানে নিজের LLM function call করবে
            # For example:
            # llm_response = call_llm(prompt)

            llm_response = self._mock_llm_response(rag_data, days)  # 🔥 DEMO STABLE

            # --------------------------------
            # 🧠 Extract JSON from response
            # --------------------------------
            itinerary = extract_json(llm_response)

            if not itinerary:
                logger.warning("⚠️ LLM JSON extraction failed. Using fallback plan")
                itinerary = self._fallback_itinerary(rag_data, days)

            return itinerary

        except Exception as e:
            logger.exception(f"Agent failed: {e}")
            return self._fallback_itinerary(rag_data, days)

    # ----------------------------------------------------------------------
    def _build_prompt(
        self, query, rag_data, budget, interests, days, location, travelers, user_profile, priorities
    ) -> str:

        return f"""
You are EcoGuide AI — an expert sustainability travel planner.

USER PROFILE:
Name: {user_profile.get("name","Unknown")}
Budget: {budget}
Interests: {interests}
Priorities: {priorities}

TRIP INFO:
Days: {days}
Travelers: {travelers}
Location: {location}

RAG MATCHES (Highly relevant eco-friendly hotels/activities):
{json.dumps(rag_data, indent=2)}

TASK:
Create an eco-friendly trip plan in **VALID JSON ONLY**:

Format:
{{
  "trip_overview": "...",
  "daily_plan": [
      {{"day": 1, "morning": "", "afternoon": "", "evening": ""}},
      ...
  ],
  "recommended_hotels": [],
  "top_activities": []
}}
"""

    # ----------------------------------------------------------------------
    def _mock_llm_response(self, rag_data, days):
        """
        🔥 Reliable fallback for demos (LLM not required).
        Always returns clean JSON based on RAG results.
        """

        hotels = [x for x in rag_data if x.get("data_type") == "Hotel"]
        activities = [x for x in rag_data if x.get("data_type") == "Activity"]

        plan = {
            "trip_overview": f"Eco-friendly {days}-day trip based on top sustainable options.",
            "daily_plan": [],
            "recommended_hotels": hotels[:3],
            "top_activities": activities[:5]
        }

        for d in range(1, days + 1):
            plan["daily_plan"].append({
                "day": d,
                "morning": activities[d % len(activities)].get("name", "Nature Walk") if activities else "Local eco-walk",
                "afternoon": activities[(d+1) % len(activities)].get("name", "Cultural Tour") if activities else "Cultural eco spot",
                "evening": hotels[d % len(hotels)].get("name", "Eco Stay") if hotels else "Relax at eco hotel"
            })

        return json.dumps(plan)

    # ----------------------------------------------------------------------
    def _fallback_itinerary(self, rag_data, days):
        """🔥 If LLM or JSON fails → use guaranteed fallback."""
        hotels = [x for x in rag_data if x.get("data_type") == "Hotel"]
        activities = [x for x in rag_data if x.get("data_type") == "Activity"]

        plan = {
            "trip_overview": "Backup eco-friendly plan (LLM failed).",
            "daily_plan": [],
            "recommended_hotels": hotels[:3] if hotels else [],
            "top_activities": activities[:5] if activities else []
        }

        # Generate simple plan
        for d in range(1, days + 1):
            plan["daily_plan"].append({
                "day": d,
                "morning": "Visit nearby eco spot",
                "afternoon": "Low-impact cultural walk",
                "evening": "Relax at eco hotel"
            })

        return plan
