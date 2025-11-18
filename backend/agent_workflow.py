import os
import google.generativeai as genai
from dotenv import load_dotenv
from backend.utils import extract_json
from utils.schemas import ItinerarySchema
from utils.logger import logger
import json

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-1.5-flash")

# ডিফল্ট প্রম্পট (যদি ফাইল না থাকে)
DEFAULT_PROMPT = """
You are an expert travel planner. Create a valid JSON itinerary based on the user request.
Output ONLY JSON matching this schema:
{
    "plan": "Markdown plan...",
    "activities": [],
    "total_cost": 0,
    "eco_score": 0,
    "carbon_saved": "0kg",
    "budget_breakdown": {},
    "ai_time_planner_report": "Looks good",
    "risk_safety_report": "Safe",
    "cost_leakage_report": "None"
}
"""

def _load_prompt(filename):
    """Loads prompt from file or returns default."""
    try:
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        path = os.path.join(base_path, "prompts", filename)
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except:
        return DEFAULT_PROMPT

class AgentWorkflow:
    def _ask(self, prompt):
        try:
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            logger.exception(f"Gemini Error: {e}")
            return None

    def _validate(self, text):
        try:
            data = extract_json(text)
            if not data: return ItinerarySchema().model_dump()
            return ItinerarySchema(**data).model_dump()
        except:
            return ItinerarySchema().model_dump()

    # ---------------------------------------------------------
    # 1. MAIN RUN FUNCTION
    # ---------------------------------------------------------
    def run(self, query, rag_data, **kwargs):
        try:
            prompt_template = _load_prompt("itinerary_prompt.txt")
            rag_str = json.dumps(rag_data, default=str)
            
            prompt = prompt_template.replace("{query}", str(query))
            prompt = prompt.replace("{rag_data}", rag_str)
            
            for key, value in kwargs.items():
                placeholder = "{" + key + "}"
                if placeholder in prompt:
                    prompt = prompt.replace(placeholder, str(value))

            return self._validate(self._ask(prompt))
            
        except Exception as e:
            logger.exception(f"Run Workflow Failed: {e}")
            fallback = f"{DEFAULT_PROMPT}\nUser Query: {query}\nData: {str(rag_data)[:1000]}"
            return self._validate(self._ask(fallback))

    # ---------------------------------------------------------
    # 2. REFINE PLAN
    # ---------------------------------------------------------
    def refine_plan(self, previous_plan_json=None, feedback_query="", rag_data=[], **kwargs):
        try:
            rag_str = json.dumps(rag_data, default=str)
            plan_str = str(previous_plan_json)

            prompt = f"""
            You are a travel assistant. Refine the following JSON plan based on user feedback.
            
            **Current Plan JSON:**
            {plan_str[:10000]} 
            
            **User Feedback:**
            "{feedback_query}"
            
            **New Options (RAG):**
            {rag_str[:5000]}
            
            **Instructions:**
            1. Modify the plan according to the feedback (e.g. make it cheaper, change location).
            2. Keep the exact same JSON structure.
            3. Output ONLY valid JSON.
            """
            
            response = self._ask(prompt)
            return self._validate(response)

        except Exception as e:
            logger.exception(f"Refine Failed: {e}")
            return None

    # ---------------------------------------------------------
    # 3. OTHER HELPERS (Fixed Story & Packing List)
    # ---------------------------------------------------------
    def ask_question(self, plan_context, question):
        # Fix: Ensure inputs are strings
        prompt = f"Context: {str(plan_context)[:5000]}\n\nUser Question: {str(question)}\n\nAnswer briefly."
        return self._ask(prompt) or "I couldn't answer that."

    def generate_packing_list(self, plan_context, user_profile, list_type):
        # Fix: Ensure inputs are strings to prevent crash
        prompt = f"Create a {str(list_type)} packing list for this trip based on profile {str(user_profile)}:\n{str(plan_context)[:3000]}"
        return self._ask(prompt) or "Packing list unavailable."

    def generate_story(self, plan_context, user_name):
        # Fix: Ensure inputs are strings
        prompt = f"Write a short travel story for {str(user_name)} based on this plan:\n{str(plan_context)[:3000]}"
        return self._ask(prompt) or "Story generation failed."

    def get_upgrade_suggestions(self, plan_context, user_profile, rag_data):
        # Fix: Ensure inputs are strings
        prompt = f"Suggest 3 premium upgrades for this plan:\n{str(plan_context)[:3000]}"
        return self._ask(prompt) or "No upgrades found."
        
