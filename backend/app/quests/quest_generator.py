from collections.abc import Sequence

from app.schemas.personalization import RoadmapNode
from app.schemas.quest import DifficultyMode, Quest, QuestMode

DAILY_QUEST_COUNTS: dict[DifficultyMode, int] = {
    "casual": 1,
    "standard": 2,
    "hunter": 3,
    "monarch": 5,
}

LEARNING_MINUTES = 45
PRACTICE_MINUTES = 30
CHALLENGE_MINUTES = 45
RECOVERY_MINUTES = 60
EMERGENCY_MINUTES = 30


class QuestGenerator:
    def generate(
        self,
        goal_id: str,
        roadmap: Sequence[RoadmapNode],
        difficulty: DifficultyMode,
        due_date,
        mode: QuestMode = "normal",
    ) -> list[Quest]:
        if mode in {"recovery", "emergency"}:
            return self._generate_special_quest(goal_id, roadmap, difficulty, due_date, mode)

        eligible = [node for node in roadmap if node.status == "available"]
        learn_nodes = [node for node in eligible if node.classification == "learn"]
        review_nodes = [node for node in eligible if node.classification == "review"]
        ordered_nodes = learn_nodes + review_nodes
        target_count = DAILY_QUEST_COUNTS[difficulty]
        quests: list[Quest] = []

        for node in ordered_nodes:
            quests.append(self._make_quest(goal_id, node, difficulty, due_date, "learning" if node.classification == "learn" else "practice"))
            if len(quests) >= target_count:
                return quests

        # Fill the daily target with deterministic practice and challenge reinforcement.
        for node in ordered_nodes:
            if len(quests) >= target_count:
                break
            if node.classification == "learn":
                quests.append(self._make_quest(goal_id, node, difficulty, due_date, "practice"))
        for node in ordered_nodes:
            if len(quests) >= target_count:
                break
            quests.append(self._make_quest(goal_id, node, difficulty, due_date, "challenge"))
        return quests

    def _generate_special_quest(self, goal_id, roadmap, difficulty, due_date, mode):
        weak_nodes = [node for node in roadmap if node.status == "available" and node.classification == "learn"]
        if not weak_nodes:
            return []
        node = weak_nodes[0]
        quest_type = mode
        title = f"{mode.title()} {node.skill_name}"
        objective = (
            f"Rebuild confidence in {node.skill_name} with a focused recovery study session."
            if mode == "recovery"
            else f"Complete an urgent focused practice session for {node.skill_name}."
        )
        return [
            self._make_quest(
                goal_id,
                node,
                difficulty,
                due_date,
                quest_type,
                title=title,
                description=objective,
                estimated_minutes=RECOVERY_MINUTES if mode == "recovery" else EMERGENCY_MINUTES,
            )
        ]

    def _make_quest(
        self,
        goal_id,
        node,
        difficulty,
        due_date,
        quest_type,
        *,
        title=None,
        description=None,
        estimated_minutes=None,
    ) -> Quest:
        defaults = {
            "learning": (
                f"Learn {node.skill_name}",
                f"Study the core concepts for {node.skill_name} using a recommended resource.",
                LEARNING_MINUTES,
            ),
            "practice": (
                f"Practice {node.skill_name}",
                f"Complete focused practice exercises for {node.skill_name}.",
                PRACTICE_MINUTES,
            ),
            "challenge": (
                f"{node.skill_name} Challenge",
                f"Build or solve a small challenge that applies {node.skill_name}.",
                CHALLENGE_MINUTES,
            ),
            "recovery": (
                f"Recovery {node.skill_name}",
                f"Revisit the core concepts for {node.skill_name}.",
                RECOVERY_MINUTES,
            ),
            "emergency": (
                f"Emergency {node.skill_name}",
                f"Complete a focused practice session for {node.skill_name}.",
                EMERGENCY_MINUTES,
            ),
        }
        default_title, default_description, default_minutes = defaults[quest_type]
        quest_id = f"{due_date.isoformat()}_{goal_id}_{node.skill_id}_{quest_type}"
        return Quest(
            id=quest_id,
            goal_id=goal_id,
            roadmap_skill_id=node.skill_id,
            quest_type=quest_type,
            title=title or default_title,
            description=description or default_description,
            resource_ids=[resource.id for resource in node.resources],
            difficulty=difficulty,
            estimated_minutes=estimated_minutes or default_minutes,
            status="available",
            due_date=due_date,
            prerequisites=node.prerequisites,
        )
