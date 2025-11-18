from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional


class Activity(BaseModel):
    """Schema for a single RAG-based activity, hotel, or place."""
    name: str
    location: str
    eco_score: float
    cost: Optional[float] = 0.0
    cost_type: Optional[str] = "one_time"
    data_type: str
    avg_rating: Optional[float] = 0.0
    description: Optional[str] = ""
    image_url: Optional[str] = ""
    tag: Optional[str] = None


class ItinerarySchema(BaseModel):
    """
    FINAL MASTER SCHEMA — EXACTLY MATCHING itinerary_prompt.txt
    Required to avoid plan failure & PDF failure.
    """

    # REQUIRED
    plan: str
    activities: List[Activity]

    # EXACT nums from your prompt structure
    total_cost: int = 0
    eco_score: float = 0.0
    carbon_saved: str = "0kg"
    waste_free_score: int = 5
    plan_health_score: int = 70

    # Budget Breakdown
    budget_breakdown: Dict[str, Any] = Field(default_factory=dict)

    # Additional Reports
    carbon_offset_suggestion: str = ""
    ai_image_prompt: str = ""
    ai_time_planner_report: str = ""
    cost_leakage_report: str = ""
    risk_safety_report: str = ""
    weather_contingency: str = ""
    duplicate_trip_detector: str = ""

    # Highlights
    experience_highlights: List[str] = Field(default_factory=list)

    # Mood indicator
    trip_mood_indicator: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        extra = "ignore"
