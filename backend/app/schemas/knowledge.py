from pydantic import BaseModel, ConfigDict


class Skill(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str
    name: str
    domain: str
    description: str
    prerequisites: list[str]
    difficulty: str


class GoalDefinition(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str
    name: str
    description: str
    required_skills: list[str]
