from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any

class Activity(BaseModel):
    name: str = ""
    location: str = ""
    eco_score: float = 0.0
    description: str = ""
    cost: float = 0.0
    cost_type: str = "one_time"
    data_type: str = "Activity"
    avg_rating: float = 0.0
    image_url: str = ""
    tag: Optional[str] = None

class ItinerarySchema(BaseModel):
    plan: str = "No plan available."
    activities: List[Activity] = []
    total_cost: int = 0
    eco_score: float = 0
    carbon_saved: str = "0kg"
    waste_free_score: int = 5
    plan_health_score: int = 50
    budget_breakdown: Dict[str, Any] = {}
    carbon_offset_suggestion: str = ""
    ai_image_prompt: str = ""
    ai_time_planner_report: str = ""
    cost_leakage_report: str = ""
    risk_safety_report: str = ""
    weather_contingency: str = ""
    duplicate_trip_detector: str = ""
    experience_highlights: List[str] = []
    trip_mood_indicator: Dict[str, Any] = {}

    class Config:
        extra = "ignore"
