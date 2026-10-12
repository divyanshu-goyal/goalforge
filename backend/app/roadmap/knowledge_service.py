import json
from pathlib import Path
from typing import Iterable

from app.schemas.knowledge import GoalDefinition, Skill


class KnowledgeGraphError(ValueError):
    """Raised when static knowledge graph data is inconsistent."""


DEFAULT_KNOWLEDGE_ROOT = Path(__file__).resolve().parents[3] / "knowledge"


def _unique_ids(items: Iterable[Skill | GoalDefinition], item_type: str) -> None:
    seen: set[str] = set()
    for item in items:
        if item.id in seen:
            raise KnowledgeGraphError(f"Duplicate {item_type} ID: {item.id}")
        seen.add(item.id)


def validate_knowledge_graph(skills: list[Skill], goals: list[GoalDefinition]) -> None:
    _unique_ids(skills, "skill")
    _unique_ids(goals, "goal")

    skills_by_id = {skill.id: skill for skill in skills}
    for skill in skills:
        for prerequisite_id in skill.prerequisites:
            if prerequisite_id not in skills_by_id:
                raise KnowledgeGraphError(
                    f"Skill '{skill.id}' references missing prerequisite '{prerequisite_id}'"
                )

    for goal in goals:
        for skill_id in goal.required_skills:
            if skill_id not in skills_by_id:
                raise KnowledgeGraphError(
                    f"Goal '{goal.id}' references missing skill '{skill_id}'"
                )

    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(skill_id: str, path: list[str]) -> None:
        if skill_id in visiting:
            cycle_start = path.index(skill_id)
            cycle = " -> ".join(path[cycle_start:] + [skill_id])
            raise KnowledgeGraphError(f"Circular prerequisite dependency: {cycle}")
        if skill_id in visited:
            return

        visiting.add(skill_id)
        for prerequisite_id in skills_by_id[skill_id].prerequisites:
            visit(prerequisite_id, path + [prerequisite_id])
        visiting.remove(skill_id)
        visited.add(skill_id)

    for skill in skills:
        visit(skill.id, [skill.id])


class KnowledgeService:
    def __init__(self, knowledge_root: Path = DEFAULT_KNOWLEDGE_ROOT) -> None:
        self.knowledge_root = knowledge_root
        self.skills = self._load_skills()
        self.goals = self._load_goals()
        validate_knowledge_graph(self.skills, self.goals)
        self._skills_by_id = {skill.id: skill for skill in self.skills}
        self._goals_by_id = {goal.id: goal for goal in self.goals}

    def _load_json(self, path: Path) -> list[dict[str, object]]:
        try:
            with path.open(encoding="utf-8") as file:
                data = json.load(file)
        except FileNotFoundError as error:
            raise KnowledgeGraphError(f"Knowledge file not found: {path}") from error
        except json.JSONDecodeError as error:
            raise KnowledgeGraphError(f"Invalid JSON in {path}: {error.msg}") from error

        if not isinstance(data, list):
            raise KnowledgeGraphError(f"Expected a JSON array in {path}")
        return data

    def _load_skills(self) -> list[Skill]:
        return [Skill.model_validate(item) for item in self._load_json(self.knowledge_root / "skills" / "skills.json")]

    def _load_goals(self) -> list[GoalDefinition]:
        return [GoalDefinition.model_validate(item) for item in self._load_json(self.knowledge_root / "goals" / "goals.json")]

    def get_all_skills(self) -> list[Skill]:
        return self.skills

    def get_skill(self, skill_id: str) -> Skill | None:
        return self._skills_by_id.get(skill_id)

    def get_skills_by_domain(self, domain: str) -> list[Skill]:
        return [skill for skill in self.skills if skill.domain == domain]

    def get_prerequisites(self, skill_id: str) -> list[Skill]:
        skill = self._skills_by_id[skill_id]
        return [self._skills_by_id[prerequisite_id] for prerequisite_id in skill.prerequisites]

    def get_dependents(self, skill_id: str) -> list[Skill]:
        return [skill for skill in self.skills if skill_id in skill.prerequisites]

    def get_goal(self, goal_id: str) -> GoalDefinition | None:
        return self._goals_by_id.get(goal_id)

    def get_required_skills(self, goal_id: str) -> list[Skill]:
        goal = self._goals_by_id[goal_id]
        return [self._skills_by_id[skill_id] for skill_id in goal.required_skills]


knowledge_service = KnowledgeService()
