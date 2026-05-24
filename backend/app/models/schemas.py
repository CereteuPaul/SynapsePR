from typing import List, Optional
from pydantic import BaseModel, Field


class Summary(BaseModel):
    intent: str
    cognitive_load_score: str
    total_impacted_modules: int


class RoadmapItem(BaseModel):
    file_path: str
    review_priority: int
    change_type: str
    architectural_impact: Optional[str] = None
    risk_flags: List[str] = []


class ArchitecturalDrift(BaseModel):
    violates_patterns: bool
    explanation: Optional[str] = None


class AnalyzeDiffResponse(BaseModel):
    summary: Summary
    review_roadmap: List[RoadmapItem]
    architectural_drift: ArchitecturalDrift


class AnalyzeDiffRequest(BaseModel):
    diff_text: str
    repo: Optional[str] = None
    tenant: Optional[str] = None


class CoachMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str


class CoachRequest(BaseModel):
    message: str
    intent: Optional[str] = None
    repo: Optional[str] = None
    tenant: Optional[str] = None
    conversation_history: List[CoachMessage] = Field(default_factory=list)


class CoachResponse(BaseModel):
    response: str
    metadata: Optional[dict] = None
