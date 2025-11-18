import os
import google.generativeai as genai
from backend.utils_json import extract_json
from utils.logger import logger

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))


# ============================
# UNIVERSAL FALLBACK
# ============================
def fallback_itinerary():
    return {
        "summary": "Fallback itinerary (AI issue).",
        "hotel": {"name": "Fallback Eco Hotel", "location": "Dubai"},
        "activities": [{"title": "Fallback Activity"}],
        "daily_plan": [{"day": 1, "plan": "Relax and fallback"}],
        "eco_score": 8.0,
        "carbon_saved": "5kg"
    }


# ============================
# FULL AGENT WORKFLOW
# ============================
class AgentWorkflow:
    def __init__(self):
        self.model = genai.GenerativeModel(
            "gemini-1.5-flash",
            generation_config={"response_mime_type": "application/json"}
        )

    # =====================================================
    # MAIN TRIP GENERATOR
    # =====================================================
    def run(self, query, rag_data, budget, interests, days, location, travelers, user_profile, priorities):
        try:
            prompt = {
                "query": query,
                "budget": budget,
                "days": days,
                "travelers": travelers,
                "location": location,
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

            try:
                parsed = extract_json(response.text)
                if parsed:
                    return parsed
            except:
                pass

            return fallback_itinerary()

        except Exception as e:
            logger.exception(e)
            return fallback_itinerary()

    # =====================================================
    # PLAN REFINER
    # =====================================================
    def refine_plan(self, itinerary, instruction):
        try:
            prompt = [
                {"role": "system", "content": "Refine this itinerary strictly in JSON."},
                {"role": "user", "content": f"ITINERARY:\n{itinerary}\n\nREFINEMENT:\n{instruction}"}
            ]

            response = self.model.generate_content(prompt)

            parsed = extract_json(response.text)
            if parsed:
                return parsed

            return itinerary
        except:
            return itinerary

    # =====================================================
    # STORY GENERATOR (FIXED)
    # =====================================================
    def generate_story(self, itinerary, user_name):
        prompt = f"""
        Write a fun travel story for {user_name} based on this itinerary.
        Return JSON only: {{"story": "..."}}
        """

        try:
            resp = self.model.generate_content(prompt)
            data = extract_json(resp.text)
            if data:
                return data.get("story", "")
        except:
            pass

        return "Could not generate story."

    # =====================================================
    # PACKING LIST GENERATOR (FIXED)
    # =====================================================
    def generate_packing_list(self, itinerary, user_name):
        prompt = f"""
        Create a packing list for {user_name} based on this itinerary.
        Return JSON: {{"items": ["item1","item2"]}}
        """

        try:
            resp = self.model.generate_content(prompt)
            parsed = extract_json(resp.text)
            if parsed:
                return parsed.get("items", [])
        except:
            pass

        return ["Passport", "Water bottle", "Eco-friendly bag"]

    # =====================================================
    # CHATBOT QUESTION HANDLER (FIXED)
    # =====================================================
    def ask_question(self, question, itinerary):
        prompt = f"""
        User question: {question}
        Context itinerary: {itinerary}
        Answer nicely in JSON:
        {{"answer": "..."}} 
        """

        try:
            resp = self.model.generate_content(prompt)
            parsed = extract_json(resp.text)
            if parsed:
                return parsed.get("answer", "")
        except:
            pass

        return "Sorry, I couldn't answer that."

    # =====================================================
    # UPGRADE SUGGESTIONS (FIXED)
    # =====================================================
    def get_upgrade_suggestions(self, plan_context):
        prompt = f"""
        Suggest 3 improvements for this trip plan.
        Return JSON: {{"upgrades": ["A","B","C"]}}
        PLAN: {plan_context}
        """

        try:
            resp = self.model.generate_content(prompt)
            parsed = extract_json(resp.text)
            if parsed:
                return parsed.get("upgrades", [])
        except:
            pass

        return ["Add more eco attractions", "Improve transport", "Add nightlife options"]
