# backend/agent_workflow.py

import json
from typing import Dict, Any, List
from backend.gemini_client import ask_gemini
from backend.utils_json import extract_json


class AgentWorkflow:
    """
    Main travel-planning AI workflow.
    Takes: user query + RAG search results
    Sends to: Gemini
    Gets: Structured JSON itinerary
    """

    def __init__(self):
        pass

    # ---------------------------------------
    # Build context from RAG results
    # ---------------------------------------
    def _build_context(self, rag_data: List[Dict[str, Any]]) -> str:
        if not rag_data:
            return "No RAG data available."

        lines = []
        for item in rag_data:
            name = item.get("name", "Unknown")
            loc = item.get("location", "")
            eco = item.get("eco_score", "")
            desc = item.get("description", "")

            lines.append(f"{name} ({loc}) — Eco Score {eco}/10\n{desc}")

        return "\n\n".join(lines)

    # ---------------------------------------
    # Build full Gemini prompt
    # ---------------------------------------
    def _build_prompt(self, query: str, context: str) -> str:
        return f"""
You are EcoGuide AI — an expert eco-friendly travel planner.
You ALWAYS output pure JSON. No extra text.

Use ONLY the following eco-locations:

{context}

User requested:
{query}

Now generate a JSON itinerary with EXACT structure:

{{
  "trip_overview": "Short overview",
  "daily_plan": [
      {{
        "day": 1,
        "title": "Day title",
        "activities": ["..."],
        "hotel": "..."
      }}
  ],
  "packing_list": ["item1", "item2"],
  "travel_story": "A short story",
  "upgrade_suggestions": "..."
}}

⚠️ IMPORTANT:
- DO NOT add text outside JSON.
- DO NOT apologize.
- If info missing, guess intelligently.
"""
    # ---------------------------------------
    # MAIN RUN METHOD
    # ---------------------------------------
    def run(self, query: str, rag_data=None, **kwargs) -> Dict[str, Any]:

        # 1. build context
        context = self._build_context(rag_data)

        # 2. build prompt
        prompt = self._build_prompt(query, context)

        # 3. ask Gemini
        raw_output = ask_gemini(prompt)

        # 4. try extract JSON
        parsed = extract_json(raw_output)

        if parsed:
            return parsed

        # 5. fallback
        return {
            "error": "Gemini returned invalid JSON.",
            "raw_output": raw_output
        }
