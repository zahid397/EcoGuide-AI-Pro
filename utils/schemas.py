from pydantic import BaseModel, Field, validator
from typing import List, Dict, Any, Optional

class Activity(BaseModel):
    """Schema for a single activity/hotel from RAG."""
    name: Optional[str] = "Unknown Activity"
    location: Optional[str] = "Unknown Location"
    eco_score: Optional[float] = 0.0
    description: Optional[str] = "No description."
    cost: Optional[float] = 0.0
    cost_type: Optional[str] = "one_time"
    data_type: Optional[str] = "Activity"
    avg_rating: Optional[float] = 0.0
    image_url: Optional[str] = None
    tag: Optional[str] = None

class ItinerarySchema(BaseModel):
    """
    Robust Schema: Makes most fields optional to prevent validation failures.
    """
    plan: Optional[str] = Field(default="## No detailed plan generated.", description="The day-by-day plan.")
    activities: List[Activity] = Field(default_factory=list)
    
    # Metrics (Default to 0/N/A if missing)
    total_cost: Optional[int] = 0
    eco_score: Optional[float] = 0.0
    carbon_saved: Optional[str] = "0kg"
    waste_free_score: Optional[int] = 5
    plan_health_score: Optional[int] = 75
    
    # Reports (Strings default to generic messages)
    budget_breakdown: Optional[Dict[str, Any]] = Field(default_factory=dict)
    carbon_offset_suggestion: Optional[str] = "Plant a tree."
    ai_image_prompt: Optional[str] = "A beautiful eco-travel destination."
    
    ai_time_planner_report: Optional[str] = "Time schedule looks good."
    cost_leakage_report: Optional[str] = "No major cost leaks detected."
    risk_safety_report: Optional[str] = "Standard safety precautions apply."
    weather_contingency: Optional[str] = "Check local forecast."
    duplicate_trip_detector: Optional[str] = "This is a unique trip plan."
    
    experience_highlights: Optional[List[str]] = Field(default_factory=list)
    trip_mood_indicator: Optional[Dict[str, Any]] = Field(default_factory=dict)

    class Config:
        extra = 'ignore'
        
    # Validator to fix generic JSON errors (optional but helpful)
    @validator('budget_breakdown', 'trip_mood_indicator', pre=True)
    def parse_empty_dict(cls, v):
        if not v or v == "null":
            return {}
        return v
        
