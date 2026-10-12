from pydantic import BaseModel


class GoalProfile(BaseModel):
    goal: str
    objective: str
    experience_level: str
    weekly_hours: int
    timeline: str
    learning_style: str
    difficulty: str
    resource_preference: str
    motivation: str
    prior_knowledge: str