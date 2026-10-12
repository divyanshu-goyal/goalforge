from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field


Rank = Literal["E", "D", "C", "B", "A", "S"]


class Achievement(BaseModel):
    achievement_id: str
    name: str
    description: str
    hidden: bool
    unlocked: bool
    unlocked_at: datetime | None = None


class GamificationProfile(BaseModel):
    total_xp: int = Field(default=0, ge=0)
    current_xp: int = Field(default=0, ge=0)
    level: int = Field(default=1, ge=1)
    next_level: int = Field(default=2, ge=2)
    xp_for_next_level: int = Field(default=200, ge=0)
    xp_progress: int = Field(default=0, ge=0)
    current_streak: int = Field(default=0, ge=0)
    longest_streak: int = Field(default=0, ge=0)
    last_active_date: date | None = None
    streak_shields: int = Field(default=0, ge=0, le=1)
    current_rank: Rank = "E"
    eligible_rank: Rank = "E"
    rank_requirements: dict[str, int]
    active_xp_multiplier: int = Field(default=100, ge=100)
    active_buff: str = "No streak buff"
    achievements: list[Achievement]
    recovery_required: bool = False
    roadmap_review_required: bool = False
    consecutive_missed_days: int = Field(default=0, ge=0)
    last_xp_awarded: int = Field(default=0, ge=0)
    last_xp_reason: str = "No quest completed yet."
    last_completed_quest_id: str | None = None
    mastery_by_skill: dict[str, float] = Field(default_factory=dict)
    passed_boss_skills: list[str] = Field(default_factory=list)
    completed_goals: list[str] = Field(default_factory=list)
    last_boss_xp_awarded: int = Field(default=0, ge=0)
    last_boss_reason: str = "No Boss Battle completed yet."


class AchievementListResponse(BaseModel):
    achievements: list[Achievement]
