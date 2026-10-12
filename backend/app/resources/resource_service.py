import json
from pathlib import Path

from app.roadmap.knowledge_service import KnowledgeService, knowledge_service
from app.schemas.resource import (
    AccessType,
    Difficulty,
    LearningStyle,
    Resource,
    ResourceType,
)


class ResourceGraphError(ValueError):
    """Raised when curated resource data is inconsistent."""


DEFAULT_RESOURCE_PATH = Path(__file__).resolve().parents[3] / "resources" / "curated" / "resources.json"

STYLE_MATCH_SCORE = 3
DIFFICULTY_MATCH_SCORE = 2
ACCESS_MATCH_SCORE = 2
RESOURCE_TYPE_MATCH_SCORE = 1
MAX_RECOMMENDATIONS = 3


class ResourceService:
    def __init__(
        self,
        resource_path: Path = DEFAULT_RESOURCE_PATH,
        knowledge: KnowledgeService = knowledge_service,
    ) -> None:
        self.knowledge = knowledge
        self.resources = self._load_resources(resource_path)
        self._validate_resources()
        self._resources_by_id = {resource.id: resource for resource in self.resources}

    def _load_resources(self, path: Path) -> list[Resource]:
        try:
            with path.open(encoding="utf-8") as file:
                data = json.load(file)
        except FileNotFoundError as error:
            raise ResourceGraphError(f"Resource file not found: {path}") from error
        except json.JSONDecodeError as error:
            raise ResourceGraphError(f"Invalid JSON in {path}: {error.msg}") from error
        if not isinstance(data, list):
            raise ResourceGraphError(f"Expected a JSON array in {path}")
        try:
            return [Resource.model_validate(item) for item in data]
        except Exception as error:
            raise ResourceGraphError(f"Invalid resource data in {path}: {error}") from error

    def _validate_resources(self) -> None:
        seen: set[str] = set()
        valid_skills = {skill.id for skill in self.knowledge.get_all_skills()}
        for resource in self.resources:
            if resource.id in seen:
                raise ResourceGraphError(f"Duplicate resource ID: {resource.id}")
            seen.add(resource.id)
            missing_skills = sorted(set(resource.skill_ids) - valid_skills)
            if missing_skills:
                raise ResourceGraphError(
                    f"Resource '{resource.id}' references missing skills: {', '.join(missing_skills)}"
                )

    def get_resource(self, resource_id: str) -> Resource | None:
        return self._resources_by_id.get(resource_id)

    def find_resources_for_skill(self, skill_id: str) -> list[Resource]:
        return [resource for resource in self.resources if skill_id in resource.skill_ids]

    def filter_resources(
        self,
        resources: list[Resource],
        *,
        access_type: AccessType | None = None,
        difficulty: Difficulty | None = None,
        learning_style: LearningStyle | None = None,
        resource_type: ResourceType | None = None,
    ) -> list[Resource]:
        return [
            resource
            for resource in resources
            if (access_type is None or resource.access_type == access_type)
            and (difficulty is None or resource.difficulty == difficulty)
            and (learning_style is None or learning_style in resource.learning_styles)
            and (resource_type is None or resource.resource_type == resource_type)
        ]

    def recommend_for_skill(
        self,
        skill_id: str,
        *,
        learning_style: LearningStyle | None = None,
        difficulty: Difficulty | None = None,
        resource_preference: str | None = None,
        resource_type: ResourceType | None = None,
    ) -> list[Resource]:
        candidates = self.find_resources_for_skill(skill_id)
        if resource_preference == "free_only":
            candidates = [resource for resource in candidates if resource.access_type == "free"]
        elif resource_preference == "free_and_paid":
            candidates = [resource for resource in candidates if resource.access_type in {"free", "paid", "freemium"}]

        def score(resource: Resource) -> tuple[int, str]:
            ranking = 0
            if learning_style and (learning_style in resource.learning_styles or "mixed" in resource.learning_styles):
                ranking += STYLE_MATCH_SCORE
            if difficulty and resource.difficulty == difficulty:
                ranking += DIFFICULTY_MATCH_SCORE
            if resource_preference == "free_only" and resource.access_type == "free":
                ranking += ACCESS_MATCH_SCORE
            elif resource_preference == "free_and_paid":
                ranking += ACCESS_MATCH_SCORE
            if resource_type and resource.resource_type == resource_type:
                ranking += RESOURCE_TYPE_MATCH_SCORE
            return ranking, resource.id

        return sorted(candidates, key=score, reverse=True)[:MAX_RECOMMENDATIONS]


resource_service = ResourceService()
