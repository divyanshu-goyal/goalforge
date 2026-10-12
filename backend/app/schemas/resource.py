from typing import Literal

from pydantic import BaseModel, Field, HttpUrl


ResourceType = Literal[
    "course",
    "tutorial",
    "documentation",
    "video",
    "article",
    "repository",
    "practice",
    "book",
]
Difficulty = Literal["beginner", "intermediate", "advanced"]
LearningStyle = Literal["video", "reading", "project", "practice", "mixed"]
AccessType = Literal["free", "paid", "freemium"]


class Resource(BaseModel):
    id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    description: str = Field(min_length=1)
    url: HttpUrl
    resource_type: ResourceType
    skill_ids: list[str] = Field(min_length=1)
    difficulty: Difficulty
    estimated_time: int = Field(gt=0)
    learning_styles: list[LearningStyle] = Field(min_length=1)
    access_type: AccessType
    provider: str = Field(min_length=1)


class ResourceResponse(BaseModel):
    skill_id: str
    resources: list[Resource]
