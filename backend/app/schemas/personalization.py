from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.resource import Resource


Classification = Literal["skip", "review", "learn", "locked"]
RoadmapStatus = Literal["locked", "available", "in_progress", "completed", "skipped"]
BossBattleStatus = Literal["locked", "unavailable", "available", "completed"]


class PersonalizationRequest(BaseModel):
    goal_id: str
    assessment_id: str


class GapAnalysisItem(BaseModel):
    skill_id: str
    skill_name: str
    mastery: float | None
    classification: Classification
    reason: str
    blocked_by: list[str] = Field(default_factory=list)


class RoadmapNode(BaseModel):
    order: int
    skill_id: str
    skill_name: str
    mastery: float | None
    classification: Classification
    status: RoadmapStatus
    estimated_effort: str | None
    prerequisites: list[str]
    reason: str
    resources: list[Resource] = Field(default_factory=list)
    boss_battle_status: BossBattleStatus = "unavailable"


class PersonalizationSummary(BaseModel):
    skills_to_skip: int
    skills_to_review: int
    skills_to_learn: int
    skills_locked: int


class PersonalizationResponse(BaseModel):
    goal_id: str
    assessment_id: str
    summary: PersonalizationSummary
    gap_analysis: list[GapAnalysisItem]
    roadmap: list[RoadmapNode]
