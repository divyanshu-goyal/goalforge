from typing import Literal

from pydantic import BaseModel, Field


QuestTypeRecommendation = Literal["learning", "practice", "challenge"]


class AIPersonalizationContext(BaseModel):
    goal_id: str
    goal_name: str
    assessment_id: str | None = None
    learning_style: str | None = None
    difficulty: str | None = None
    weekly_time: str | None = None
    motivation: str | None = None
    mastery_by_skill: dict[str, float] = Field(default_factory=dict)
    roadmap: list[str] = Field(default_factory=list)
    resource_ids: list[str] = Field(default_factory=list)
    recent_quest_results: list[str] = Field(default_factory=list)
    recent_boss_results: list[str] = Field(default_factory=list)


class AIMentorContext(BaseModel):
    goal_id: str
    goal_name: str
    current_focus: str | None = None
    mastery: float | None = None
    rank: str | None = None
    recent_quest_results: list[str] = Field(default_factory=list)
    recent_boss_results: list[str] = Field(default_factory=list)
    message: str


class AIInsightResponse(BaseModel):
    summary: str = "GoalForge AI is unavailable. Using deterministic recommendations."
    insights: list[str] = Field(default_factory=list)
    recommended_skill_ids: list[str] = Field(default_factory=list)
    recommended_resource_ids: list[str] = Field(default_factory=list)
    recommended_quest_types: list[QuestTypeRecommendation] = Field(default_factory=list)
    explanations: list[str] = Field(default_factory=list)
    ai_available: bool = False


class AIMentorResponse(BaseModel):
    message: str
    context_used: list[str] = Field(default_factory=list)
    ai_available: bool = False


class AIPersonalizationRequest(BaseModel):
    goal_id: str
    assessment_id: str


class AIMentorRequest(BaseModel):
    goal_id: str
    message: str


class AIEnhancedPersonalizationResponse(BaseModel):
    goal_id: str
    assessment_id: str
    deterministic: dict
    ai_available: bool = False
    summary: str = ""
    insights: list[str] = Field(default_factory=list)
    recommended_skill_ids: list[str] = Field(default_factory=list)
    recommended_resource_ids: list[str] = Field(default_factory=list)
    recommended_quest_types: list[QuestTypeRecommendation] = Field(default_factory=list)
    explanations: list[str] = Field(default_factory=list)
