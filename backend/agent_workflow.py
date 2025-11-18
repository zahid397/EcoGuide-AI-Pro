import os
import google.generativeai as genai
from backend.utils_json import extract_json
from utils.logger import logger

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))


def fallback_itinerary():
    return {
        "summary": "Fallback itinerary.",
        "hotel": {"name": "Fallback Hotel"},
        "activities": [{"title": "Fallback Activity"}],
        "daily_plan": [{"day": 1, "plan": "Relax"}],
        "eco_score": 8.0,
        "carbon_saved": "5kg"
    }


class AgentWorkflow:
    def __init__(self):
        self.model = genai.GenerativeModel(
            "gemini-1.5-flash",
            generation_config={"response_mime_type": "application/json"}
        )

    # =========================================================
    # MAIN TRIP GENERATOR
    # =========================================================
    def run(
        self, query, rag_data, budget, interests, days, location,
        travelers, user_profile, priorities
    ):
        try:
            prompt = {
                "query": query,
                "budget": budget,
                "days": days,
                "location": location,
                "travelers": travelers,
                "interests": interests,
                "priorities": priorities,
                "user_profile": user_profile,
                "context_items": rag_data
            }

            response = self.model.generate_content(prompt)

            try:
                data = response.candidates[0].content.parts[0].function_call.args
                return dict(data)
            except:
                pass

            parsed = extract_json(response.text)
            if parsed:
                return parsed

        except Exception as e:
            logger.exception(e)

        return fallback_itinerary()

    # =========================================================
    # FIXED: REFINER (UI calls this correctly)
    # =========================================================
    def refine_plan(self, plan_context, refinement_query):
        """UI passes: plan_context + user text"""
        try:
            prompt = f"""
            Improve this itinerary based on user request.
            ITINERARY: {plan_context}
            REQUEST: {refinement_query}
            Return JSON only.
            """

            resp = self.model.generate_content(prompt)
            data = extract_json(resp.text)
            if data:
                return data

        except:
            pass

        return plan_context

    # =========================================================
    # FIXED: STORY GENERATOR (UI passes plan_context)
    # =========================================================
    def generate_story(self, plan_context):
        prompt = f"""
        Write a fun travel story based on this itinerary.
        Return JSON: {{"story": "..."}}
        ITINERARY: {plan_context}
        """
        try:
            resp = self.model.generate_content(prompt)
            data = extract_json(resp.text)
            return data.get("story", "")
        except:
            return "Could not generate story."

    # =========================================================
    # FIXED: PACKING LIST GENERATOR (UI passes plan_context)
    # =========================================================
    def generate_packing_list(self, plan_context):
        prompt = f"""
        Create a packing list for this trip.
        Return JSON: {{"items": ["..."]}}
        ITINERARY: {plan_context}
        """
        try:
            resp = self.model.generate_content(prompt)
            data = extract_json(resp.text)
            return data.get("items", [])
        except:
            return ["Passport", "Eco bag", "Water bottle"]

    # =========================================================
    # FIXED: CHATBOT (UI passes plan_context + question)
    # =========================================================
    def ask_question(self, question, plan_context):
        prompt = f"""
        User asked: {question}
        Use this itinerary as context: {plan_context}
        Answer in JSON: {{"answer": "..."}}
        """
        try:
            resp = self.model.generate_content(prompt)
            data = extract_json(resp.text)
            return data.get("answer", "")
        except:
            return "Sorry, I couldn't answer that."

    # =========================================================
    # FIXED: UPGRADE SUGGESTIONS
    # =========================================================
    def get_upgrade_suggestions(self, plan_context):
        prompt = f"""
        Suggest 3 improvements.
        Return JSON: {{"upgrades": ["..."]}}
        PLAN: {plan_context}
        """
        try:
            resp = self.model.generate_content(prompt)
            data = extract_json(resp.text)
            return data.get("upgrades", [])
        except:
            return ["Add more eco spots", "Improve food choices", "Extend beach time"]
