from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class Activity(BaseModel):
    """Schema for a single activity/hotel from RAG."""
    name: str
    location: str
    eco_score: float
    description: str
    cost: float
    cost_type: str
    data_type: str
    avg_rating: float
    image_url: Optional[str] = None
    tag: Optional[str] = None

class ItinerarySchema(BaseModel):
    """
    Pydantic Schema to validate the AI's JSON output (Fix 4).
    This ensures the AI response is always in the correct format.
    """
    plan: str = Field(..., description="The day-by-day plan in Markdown.")
    activities: List[Activity] = Field(..., description="List of all activities, hotels, and places.")
    total_cost: int = Field(default=0, description="Must be 0, will be calculated later.")
    eco_score: float = Field(..., ge=0, le=10, description="Average eco score of the plan.")
    carbon_saved: str = Field(..., description="Calculated carbon savings, e.g., '20kg'.")
    waste_free_score: int = Field(..., ge=0, le=10, description="Score for waste-free activities.")
    plan_health_score: int = Field(..., ge=0, le=100, description="Overall plan health score.")
    
    budget_breakdown: Dict[str, Any] = Field(..., description="JSON object for budget categories.")
    carbon_offset_suggestion: str = Field(..., description="1-sentence suggestion for offsetting carbon.")
    ai_image_prompt: str = Field(..., description="A prompt for a DALL-E style image generator.")
    
    ai_time_planner_report: str = Field(..., description="Markdown report on time conflicts.")
    cost_leakage_report: str = Field(..., description="Markdown report on missing costs.")
    risk_safety_report: str = Field(..., description="Markdown report on travel risks.")
    weather_contingency: str = Field(..., description="1-sentence weather plan.")
    duplicate_trip_detector: str = Field(..., description="Report on plan similarity to profile.")
    
    experience_highlights: List[str] = Field(..., description="List of top 3 string highlights.")
    trip_mood_indicator: Dict[str, Any] = Field(..., description="JSON object for trip moods.")

    class Config:
        # This allows extra fields from RAG to be included in 'activities'
        # without causing a validation error.
        extra = 'ignore' 
