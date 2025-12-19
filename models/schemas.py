from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from enum import Enum

class ABTestGroup(str, Enum):
    A = "A"
    B = "B"

class LikeRequest(BaseModel):
    user_id: str
    note_id: str
    ab_test: ABTestGroup

class LikeRecord(BaseModel):
    user_id: str
    note_id: str
    ab_group: ABTestGroup
    timestamp: datetime
    liked_note_id: str

class RecommendationResponse(BaseModel):
    user_id: str
    recommended_notes: List[dict]
    algorithm_used: str

class ABTestCounts(BaseModel):
    ab_test_a_like_count: int
    ab_test_b_like_count: int
    last_updated: str

class HealthResponse(BaseModel):
    success: Optional[str] = None
    failure: Optional[str] = None