from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class Activity(BaseModel):
    name: str = ""
    location: str = ""
    eco_score: float = 0
    description: str = ""
    cost: float = 0
    cost_type: str = "one_time"
    data_type: str = "Activity"
    avg_rating: float = 0
    image_url: str = ""
    tag: Optional[str] = None

class ItinerarySchema(BaseModel):
    plan: str = ""
    activities: List[Activity] = []
    total_cost: int = 0

    class Config:
        extra = "ignore"
