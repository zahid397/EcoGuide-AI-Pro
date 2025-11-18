from pydantic import BaseModel, Field, validator
from typing import List, Dict, Any, Optional

class Activity(BaseModel):
    name: str = Field(default="Unknown Activity")
    eco_score: float = Field(default=0.0)
    cost: float = Field(default=0.0)
    cost_type: str = Field(default="one_time")
    data_type: str = Field(default="Activity")
    description: str = Field(default="")
    image_url: str = Field(default="https://placehold.co/600x400?text=No+Image")
    tag: Optional[str] = None

class ItinerarySchema(BaseModel):
    plan: str = Field(default="## No plan generated.")
    activities: List[Activity] = Field(default_factory=list)
    total_cost: int = 0
    eco_score: float = 0.0
    carbon_saved: str = "0kg"
    waste_free_score: int = 5
    plan_health_score: int = 75
    
    budget_breakdown: Dict[str, Any] = Field(default_factory=dict)
    carbon_offset_suggestion: str = "Plant a tree."
    ai_image_prompt: str = "Nature travel."
    
    ai_time_planner_report: str = "Schedule looks fine."
    cost_leakage_report: str = "No leaks."
    risk_safety_report: str = "Safe trip."
    weather_contingency: str = "Check forecast."
    duplicate_trip_detector: str = "Unique trip."
    
    experience_highlights: List[str] = Field(default_factory=list)
    trip_mood_indicator: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        extra = 'ignore'

    @validator('*', pre=True)
    def handle_nulls(cls, v):
        return {} if v is None else v
      
