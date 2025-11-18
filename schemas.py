from pydantic import BaseModel, Field, validator
from typing import List, Dict, Any, Optional


class Activity(BaseModel):
    """Schema for each activity/hotel/place coming from RAG data."""
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

    class Config:
        extra = "ignore"   # ignore unexpected fields from AI


class ItinerarySchema(BaseModel):
    """
    Ultra-Stable Trip Itinerary Schema.
    This will NEVER crash the app even if AI misses a field.
    """
    # Main fields
    plan: str = Field(default="### No plan generated.\nTry again.")
    activities: List[Activity] = Field(default_factory=list)

    # Metrics
    total_cost: int = Field(default=0)
    eco_score: float = Field(default=0.0)
    carbon_saved: str = Field(default="0kg")
    waste_free_score: int = Field(default=5)
    plan_health_score: int = Field(default=70)

    # Budget breakdown
    budget_breakdown: Dict[str, Any] = Field(default_factory=lambda: {
        "Accommodation": 0,
        "Food": 0,
        "Transport": 0,
        "Activities": 0
    })

    # AI-generated reports
    carbon_offset_suggestion: str = Field(default="Plant a tree to offset your carbon footprint.")
    ai_image_prompt: str = Field(default="A scenic eco-friendly travel destination.")
    ai_time_planner_report: str = Field(default="Schedule looks balanced.")
    cost_leakage_report: str = Field(default="No cost issues detected.")
    risk_safety_report: str = Field(default="Follow regular safety guidelines.")
    weather_contingency: str = Field(default="Check local weather updates.")
    duplicate_trip_detector: str = Field(default="This trip is unique.")

    # Experience
    experience_highlights: List[str] = Field(default_factory=list)
    trip_mood_indicator: Dict[str, Any] = Field(default_factory=lambda: {
        "Adventure": 50,
        "Relax": 50,
        "Culture": 50
    })

    class Config:
        extra = 'ignore'  # ignore unknown AI-generated keys

    # Auto-clean null / "null" / bad values
    @validator('*', pre=True)
    def handle_nulls(cls, v):
        if v is None or v == "null":
            return ""
        return v
