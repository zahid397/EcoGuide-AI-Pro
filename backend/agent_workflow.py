import os
import google.generativeai as genai
from dotenv import load_dotenv
from backend.utils import extract_json
from utils.schemas import ItinerarySchema
from utils.logger import logger
from pydantic import ValidationError
import json

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-1.5-flash")

def _load_prompt(filename):
    try:
        path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "prompts", filename)
        with open(path, "r", encoding="utf-8") as f: return f.read()
    except: return ""

PROMPTS = {
    "itinerary": _load_prompt("itinerary_prompt.txt"),
    "refine": _load_prompt("refine_prompt.txt"),
    "upgrade": _load_prompt("upgrade_prompt.txt"),
    "question": _load_prompt("question_prompt.txt"),
    "packing": _load_prompt("packing_prompt.txt"),
    "story": _load_prompt("story_prompt.txt"),
}

class AgentWorkflow:
    def _ask(self, prompt):
        try:
            return model.generate_content(prompt).text
        except Exception as e:
            logger.exception(e)
            return None

    def _validate(self, output):
        try:
            data = extract_json(output)
            if not data: return ItinerarySchema().model_dump() # Fallback
            return ItinerarySchema(**data).model_dump()
        except:
            return ItinerarySchema().model_dump() # Fallback on error

    def run(self, query, rag_data, budget, interests, days, location, travelers, user_profile, priorities):
        # 100% Safe Format Call
        try:
            p_ack = f"User likes {user_profile.get('interests')}" if user_profile.get('interests') else ""
            prompt = PROMPTS["itinerary"].format(
                query=query, days=days, travelers=travelers, budget=budget,
                eco_priority=priorities.get('eco', 5), budget_priority=priorities.get('budget', 5),
                comfort_priority=priorities.get('comfort', 5),
                user_name=user_profile.get('name', 'User'), user_interests=str(interests),
                profile_ack=p_ack, rag_data=json.dumps(rag_data, default=str)
            )
            return self._validate(self._ask(prompt))
        except Exception as e:
            logger.exception(f"Run failed: {e}")
            return None

    # (Refine, Upgrade, etc. function-গুলোও সেইম pattern ফলো করবে)
    # ... (Code length কমানোর জন্য বাকি ফাংশন আগের মতোই রাখলাম, লজিক same)
    # শুধু মনে রাখবি: সব _ask() এর পর _validate() কল করবি।
    
    def refine_plan(self, previous_plan_json, feedback_query, rag_data, user_profile, priorities, travelers, days, budget):
        try:
            prompt = PROMPTS["refine"].format(
                user_profile=user_profile, priorities=priorities, feedback_query=feedback_query,
                previous_plan_json=previous_plan_json, rag_data=json.dumps(rag_data, default=str),
                travelers=travelers, days=days, budget=budget
            )
            return self._validate(self._ask(prompt))
        except: return None

    def get_upgrade_suggestions(self, plan_context, user_profile, rag_data):
        prompt = PROMPTS["upgrade"].format(user_profile=user_profile, plan_context=plan_context, rag_data=json.dumps(rag_data, default=str))
        return self._ask(prompt) or "No suggestions."

    def ask_question(self, plan_context, question):
        prompt = PROMPTS["question"].format(plan_context=plan_context, question=question)
        return self._ask(prompt) or "I couldn't answer that."

    def generate_packing_list(self, plan_context, user_profile, list_type):
        prompt = PROMPTS["packing"].format(user_profile=user_profile, plan_context=plan_context, list_type=list_type)
        return self._ask(prompt) or "No packing list."

    def generate_story(self, plan_context, user_name):
        prompt = PROMPTS["story"].format(user_name=user_name, plan_context=plan_context)
        return self._ask(prompt) or "No story generated."
      
