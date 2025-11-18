import os
import google.generativeai as genai
from dotenv import load_dotenv
from backend.utils import extract_json
from utils.schemas import ItinerarySchema
from utils.logger import logger
import json
from pydantic import ValidationError
from typing import Dict, Any, Optional, List

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
MODEL_NAME: str = os.getenv("MODEL", "gemini-1.5-flash")

safety_settings = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
]

model = genai.GenerativeModel(MODEL_NAME, safety_settings=safety_settings)

def _load_prompt(filename: str) -> str:
    """Loads a prompt from the prompts/ directory."""
    try:
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        file_path = os.path.join(base_path, "prompts", filename)
        
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        logger.error(f"Prompt file not found: {filename}")
        return ""
    except Exception as e:
        logger.exception(f"Error loading prompt {filename}: {e}")
        return ""

# Load prompts once
PROMPTS = {
    "itinerary": _load_prompt("itinerary_prompt.txt"),
    "refine": _load_prompt("refine_prompt.txt"),
    "upgrade": _load_prompt("upgrade_prompt.txt"),
    "question": _load_prompt("question_prompt.txt"),
    "packing": _load_prompt("packing_prompt.txt"),
    "story": _load_prompt("story_prompt.txt"),
}

class AgentWorkflow:
    def _ask(self, prompt: str) -> Optional[str]:
        """Internal helper to call the model."""
        if not prompt:
            logger.error("Empty prompt passed to _ask")
            return None
            
        try:
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            logger.exception(f"Gemini API call failed: {e}")
            return None 

    def _validate_json_output(self, llm_output: str) -> Optional[Dict[str, Any]]:
        """Extracts JSON, validates with Pydantic, and returns a dict."""
        try:
            json_data = extract_json(llm_output)
            if not json_data:
                raise ValueError("No JSON found in LLM output")
            
            # Validate with Schema
            parsed_data = ItinerarySchema(**json_data)
            return parsed_data.model_dump()

        except ValidationError as e:
            logger.error(f"AI Response Schema Validation Failed: {e}")
            return None
        except Exception as e:
            logger.exception(f"Failed to parse or validate JSON: {e}")
            return None

    def run(self, query: str, rag_data: List[Dict], budget: int, interests: List[str], 
            days: int, location: str, travelers: int, user_profile: Dict, 
            priorities: Dict) -> Optional[Dict[str, Any]]:
        """Generates a NEW plan from scratch."""
        
        # 1. Prepare Profile Acknowledgement
        profile_ack = ""
        if user_profile.get('interests'):
            profile_ack = f"**Bonus Context:** I see your saved profile ('{user_profile.get('name')}') prefers {user_profile.get('interests')}. I will try to prioritize these!"

        # 2. Prepare Prompt
        # ✳️ FIX: Ensure 'profile_ack' matches the placeholder in your text file
        try:
            prompt = PROMPTS["itinerary"].format(
                query=query,
                days=days,
                travelers=travelers,
                budget=budget,
                eco_priority=priorities.get('eco', 5),
                budget_priority=priorities.get('budget', 5),
                comfort_priority=priorities.get('comfort', 5),
                user_name=user_profile.get('name', 'User'),
                user_interests=user_profile.get('interests', 'N/A'),
                profile_ack=profile_ack,  # <--- This line fixes the KeyError
                rag_data=rag_data
            )
        except KeyError as e:
            logger.error(f"Missing placeholder in itinerary_prompt.txt: {e}")
            return None

        # 3. Call AI
        draft_plan = self._ask(prompt)
        if draft_plan is None: 
            return None
            
        return self._validate_json_output(draft_plan)

    def refine_plan(self, previous_plan_json: str, feedback_query: str, 
                    rag_data: List[Dict], user_profile: Dict, priorities: Dict, 
                    travelers: int, days: int, budget: int) -> Optional[Dict[str, Any]]:
        
        try:
            prompt = PROMPTS["refine"].format(
                user_profile=user_profile,
                priorities=priorities,
                feedback_query=feedback_query,
                previous_plan_json=previous_plan_json,
                rag_data=rag_data,
                travelers=travelers,
                days=days,
                budget=budget
            )
        except KeyError as e:
            logger.error(f"Missing placeholder in refine_prompt.txt: {e}")
            return None
        
        draft_plan = self._ask(prompt)
        if draft_plan is None: 
            return None
            
        return self._validate_json_output(draft_plan)

    def get_upgrade_suggestions(self, plan_context: str, user_profile: Dict, 
                                rag_data: List[Dict]) -> str:
        
        prompt = PROMPTS["upgrade"].format(
            user_profile=user_profile,
            plan_context=plan_context,
            rag_data=rag_data
        )
        response = self._ask(prompt)
        return response or "Sorry, I couldn't generate upgrades at this time."

    def ask_question(self, plan_context: str, question: str) -> str:
        
        prompt = PROMPTS["question"].format(
            plan_context=plan_context,
            question=question
        )
        response = self._ask(prompt)
        return response or "Sorry, I couldn't process that question. Please try again."

    def generate_packing_list(self, plan_context: str, user_profile: Dict, 
                              list_type: str) -> str:
        
        prompt = PROMPTS["packing"].format(
            user_profile=user_profile,
            plan_context=plan_context,
            list_type=list_type
        )
        response = self._ask(prompt)
        return response or "Sorry, I couldn't generate a packing list at this time."

    def generate_story(self, plan_context: str, user_name: str) -> str:
        
        prompt = PROMPTS["story"].format(
            user_name=user_name,
            plan_context=plan_context
        )
        response = self._ask(prompt)
        return response or "Sorry, I couldn't write your travel story at this time."
        
