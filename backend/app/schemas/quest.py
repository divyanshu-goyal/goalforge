from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field


QuestType = Literal["learning", "practice", "challenge", "recovery", "emergency"]
QuestStatus = Literal["locked", "available", "active", "completed", "expired"]
QuestMode = Literal["normal", "recovery", "emergency"]
DifficultyMode = Literal["casual", "standard", "hunter", "monarch"]


class Quest(BaseModel):
    id: str
    goal_id: str
    roadmap_skill_id: str
    quest_type: QuestType
    title: str
    description: str
    resource_ids: list[str] = Field(default_factory=list)
    difficulty: DifficultyMode
    estimated_minutes: int = Field(gt=0)
    status: QuestStatus
    due_date: date
    prerequisites: list[str] = Field(default_factory=list)
    completed_at: datetime | None = None


class QuestGenerateRequest(BaseModel):
    goal_id: str
    assessment_id: str | None = None
    mode: QuestMode = "normal"


class QuestListResponse(BaseModel):
    goal_id: str
    quests: list[Quest]


class DailyQuestResponse(BaseModel):
    goal_id: str
    date: date
    quests: list[Quest]
