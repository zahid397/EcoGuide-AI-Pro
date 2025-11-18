from pydantic import BaseModel, Field, validator
from typing import List, Dict, Any, Optional

class Activity(BaseModel):
    """Schema for a single activity/hotel from RAG."""
    name: str = Field(default="Unknown Activity")
    location: str = Field(default="Unknown Location")
    eco_score: float = Field(default=0.0)
    description: str = Field(default="No description available.")
    cost: float = Field(default=0.0)
    cost_type: str = Field(default="one_time")
    data_type: str = Field(default="Activity")
    avg_rating: float = Field(default=0.0)
    image_url: str = Field(default="https://placehold.co/600x400/grey/white?text=No+Image")
    tag: Optional[str] = None

class ItinerarySchema(BaseModel):
    """
    Ultra-Robust Schema: All fields are optional with safe defaults.
    This prevents the app from crashing if AI misses a field.
    """
    # Detailed Plan
    plan: str = Field(default="## No detailed plan generated.\n\nPlease try refining your request.")
    activities: List[Activity] = Field(default_factory=list)
    
    # Metrics (Safe Defaults)
    total_cost: int = Field(default=0)
    eco_score: float = Field(default=0.0)
    carbon_saved: str = Field(default="0kg")
    waste_free_score: int = Field(default=5)
    plan_health_score: int = Field(default=70)
    
    # Reports (Safe Strings)
    budget_breakdown: Dict[str, Any] = Field(default_factory=lambda: {"Note": "Data missing"})
    carbon_offset_suggestion: str = Field(default="Plant a tree to offset your carbon footprint.")
    ai_image_prompt: str = Field(default="A beautiful sustainable travel destination.")
    
    # Analysis Reports
    ai_time_planner_report: str = Field(default="Schedule looks okay.")
    cost_leakage_report: str = Field(default="No cost warnings.")
    risk_safety_report: str = Field(default="Standard travel safety applies.")
    weather_contingency: str = Field(default="Check local weather forecast.")
    duplicate_trip_detector: str = Field(default="This appears to be a unique trip.")
    
    # Extras
    experience_highlights: List[str] = Field(default_factory=list)
    trip_mood_indicator: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        extra = 'ignore' # Ignore unexpected fields from AI
        
    # Validator to handle "null" or empty values from AI
    @validator('*', pre=True)
    def handle_nulls(cls, v):
        if v is None or v == "null":
            return 0 if isinstance(v, int) else "" 
        return v
        
