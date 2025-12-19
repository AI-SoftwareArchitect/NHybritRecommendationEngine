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


class NoteFromAPI(BaseModel):
    """Schema for notes fetched from external API."""
    id: str
    title: str
    shortDescription: Optional[str] = None
    rating: float = 0
    downloadCount: int = 0
    viewCount: int = 0
    commentCount: int = 0
    isPopular: bool = False
    coverImageUrl: Optional[str] = None
    createdDate: Optional[str] = None
    creatorAppUser: Optional[dict] = None


class RecommendationResponse(BaseModel):
    """Response containing only note_ids for recommendations."""
    user_id: str
    note_ids: List[str]


class ABTestCounts(BaseModel):
    ab_test_a_like_count: int
    ab_test_b_like_count: int
    last_updated: str


class HealthResponse(BaseModel):
    success: Optional[str] = None
    failure: Optional[str] = None