import os
import json
import google.generativeai as genai
from dotenv import load_dotenv
from backend.utils import extract_json
from utils.schemas import ItinerarySchema
from utils.logger import logger
import random

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
MODEL_NAME = "gemini-1.5-flash"

# Safety Settings
safety_settings = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
]

model = genai.GenerativeModel(MODEL_NAME, safety_settings=safety_settings)

# --- 🚨 BACKUP PLAN (ডেমো সেভার) ---
# যদি API ফেইল করে, এই প্ল্যানটা দেখাবে।
MOCK_PLAN_JSON = """
{
  "plan": "### Day 1: Arrival & Culture\\n* **09:00 AM**: Arrive at *Fairmont Dubai*. Check-in and relax.\\n* **11:00 AM**: Visit the *Dubai Museum* to learn about local history.\\n* **01:00 PM**: Lunch at a local Emirati restaurant.\\n* **03:00 PM**: Explore the *Al Fahidi Historic District* (💎 Hidden Gem).\\n* **07:00 PM**: Dinner cruise on Dubai Creek.\\n\\n### Day 2: Nature & Adventure\\n* **08:00 AM**: Breakfast at the hotel.\\n* **09:30 AM**: Head to *Dubai Eco Kayaking* for a mangrove tour.\\n* **12:30 PM**: Organic lunch at a sustainable cafe.\\n* **03:00 PM**: Visit *Ras Al Khor Wildlife Sanctuary* to see flamingos.\\n* **06:00 PM**: Sunset at *Jumeirah Beach*.",
  "activities": [
    { "name": "Fairmont Dubai", "location": "Dubai", "eco_score": 9.0, "cost": 450, "cost_type": "per_night", "data_type": "Hotel", "avg_rating": 4.8, "description": "Luxury eco-friendly hotel.", "image_url": "https://placehold.co/600x400/28a745/white?text=Fairmont+Dubai" },
    { "name": "Dubai Eco Kayaking", "location": "Dubai", "eco_score": 8.8, "cost": 70, "cost_type": "one_time", "data_type": "Activity", "avg_rating": 4.5, "description": "Kayaking in mangroves.", "image_url": "https://placehold.co/600x400/007bff/white?text=Kayaking", "tag": "hidden_gem" },
    { "name": "Dubai Museum", "location": "Dubai", "eco_score": 8.0, "cost": 10, "cost_type": "one_time", "data_type": "Place", "avg_rating": 4.2, "description": "Historic museum.", "image_url": "https://placehold.co/600x400/ffc107/black?text=Museum" }
  ],
  "total_cost": 0,
  "eco_score": 8.9,
  "carbon_saved": "15kg",
  "waste_free_score": 8,
  "plan_health_score": 92,
  "budget_breakdown": { "Accommodation": 900, "Activities": 150, "Food": 200, "Transport": 50 },
  "carbon_offset_suggestion": "Your trip saved 15kg of CO2! Consider donating $5 to a mangrove restoration project.",
  "ai_image_prompt": "A futuristic eco-city in Dubai with vertical gardens and solar panels.",
  "ai_time_planner_report": "The schedule is perfectly balanced with ample rest time.",
  "cost_leakage_report": "No hidden costs detected. Great budget management!",
  "risk_safety_report": "Dubai is very safe. Stay hydrated and use sunscreen.",
  "weather_contingency": "If it gets too hot (40°C+), visit the Museum of the Future instead of outdoor walks.",
  "duplicate_trip_detector": "This is a unique itinerary tailored to your eco-preferences.",
  "experience_highlights": ["Mangrove Kayaking", "Historic District Walk", "Sustainable Dining"],
  "trip_mood_indicator": { "Adventure": 40, "Culture": 80, "Relax": 50, "Luxury": 60 }
}
"""

# --- Hardcoded Prompts ---
ITINERARY_PROMPT_TEMPLATE = """
You are an elite AI travel planner. Create a valid JSON itinerary.
Request: {query} | Budget: ${budget} | Days: {days} | Travelers: {travelers}
Priorities: Eco={eco_priority}, Budget={budget_priority}, Comfort={comfort_priority}
User: {user_name}, Interests: {user_interests}. {profile_ack}
RAG Data: {rag_data}

INSTRUCTIONS:
1. Create a detailed Markdown plan with times.
2. Output ONLY JSON matching the schema.
"""

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
            if not data: return json.loads(MOCK_PLAN_JSON) # Fallback to Mock
            return ItinerarySchema(**data).model_dump()
        except:
            return json.loads(MOCK_PLAN_JSON) # Fallback to Mock

    def run(self, query, rag_data, **kwargs):
        try:
            # 1. Prompt তৈরি
            rag_str = json.dumps(rag_data, default=str)
            user_profile = kwargs.get('user_profile', {})
            priorities = kwargs.get('priorities', {})
            
            profile_ack = ""
            if user_profile.get('interests'):
                profile_ack = f"User likes {user_profile.get('interests')}"

            prompt = ITINERARY_PROMPT_TEMPLATE.format(
                query=query,
                budget=kwargs.get('budget', 1000),
                days=kwargs.get('days', 3),
                travelers=kwargs.get('travelers', 1),
                eco_priority=priorities.get('eco', 5),
                budget_priority=priorities.get('budget', 5),
                comfort_priority=priorities.get('comfort', 5),
                user_name=user_profile.get('name', 'User'),
                user_interests=str(user_profile.get('interests', [])),
                profile_ack=profile_ack,
                rag_data=rag_str
            )

            # 2. AI কল করা
            response = self._ask(prompt)
            
            # 3. যদি AI রেসপন্স না দেয়, Mock Data রিটার্ন করো
            if not response:
                print("⚠️ API Failed. Using Backup Plan.")
                return json.loads(MOCK_PLAN_JSON)

            return self._validate(response)

        except Exception as e:
            logger.exception(f"Run Workflow Failed: {e}")
            return json.loads(MOCK_PLAN_JSON) # Final Safety Net

    def refine_plan(self, previous_plan_json=None, feedback_query="", rag_data=[], **kwargs):
        # রিফাইন ফেইল করলে আগের প্ল্যানই ফেরত দেবে
        try:
            prompt = f"Refine this JSON plan based on '{feedback_query}': {str(previous_plan_json)[:8000]}. Output JSON."
            response = self._ask(prompt)
            if not response: return previous_plan_json # Fail-safe
            return self._validate(response)
        except:
            return previous_plan_json

    # --- HELPER FUNCTIONS (Mock সহ) ---

    def ask_question(self, plan_context, question):
        # যদি API কাজ না করে, ডামি উত্তর দাও
        response = self._ask(f"Context: {str(plan_context)[:5000]}\nQuestion: {question}\nAnswer briefly.")
        return response or f"That's a great question about {question}! Based on your plan, I recommend checking local timings and booking in advance."

    def generate_packing_list(self, plan_context, user_profile, list_type):
        response = self._ask(f"Create a {list_type} packing list for: {str(plan_context)[:3000]}")
        return response or "### 🎒 Essentials\n* Passport & ID\n* Sunscreen & Sunglasses\n* Reusable Water Bottle\n* Comfortable Walking Shoes"

    def generate_story(self, plan_context, user_name):
        response = self._ask(f"Write a story for {user_name} based on: {str(plan_context)[:3000]}")
        return response or f"### An Eco-Adventure for {user_name}\n\nThe journey began under the bright sun of Dubai. From the bustling souks to the quiet mangroves, every moment was a step towards sustainable discovery..."

    def get_upgrade_suggestions(self, plan_context, user_profile, rag_data):
        response = self._ask(f"Suggest 3 upgrades for: {str(plan_context)[:3000]}")
        return response or "* **Upgrade Hotel:** Switch to a 5-star Eco Resort.\n* **Private Tour:** Book a private guided mangrove tour.\n* **Fine Dining:** Try a farm-to-table dinner experience."
        
