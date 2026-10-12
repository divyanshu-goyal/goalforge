from typing import Literal

from pydantic import BaseModel, Field


class GoalDiscoveryRequest(BaseModel):
    goal: str = Field(min_length=1)
    objective: Literal["job", "college", "projects", "freelancing", "personal_interest", "other"]
    experience_level: Literal["complete_beginner", "beginner", "intermediate", "advanced"]
    weekly_hours: Literal["less_than_5", "5_to_10", "10_to_20", "20_plus"]
    timeline: Literal["1_month", "3_months", "6_months", "1_year_plus", "no_fixed_deadline"]
    learning_style: Literal["videos", "reading", "projects", "practice", "mixed"]
    difficulty: Literal["casual", "standard", "hunter", "monarch"]
    resource_preference: Literal["free_only", "free_and_paid"]
    motivation: str = Field(min_length=1)
    prior_knowledge: str = Field(min_length=1)