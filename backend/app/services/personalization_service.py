from app.roadmap.knowledge_service import KnowledgeService, knowledge_service
from app.schemas.personalization import (
    PersonalizationResponse,
    PersonalizationSummary,
    RoadmapNode,
)
from app.schemas.assessment import UserContext
from app.resources.resource_service import ResourceService, resource_service
from app.services.gap_analysis_service import GapAnalysisService, gap_analysis_service
from app.services.gamification_service import GamificationService, gamification_service


class PersonalizationError(ValueError):
    """Raised when a personalized roadmap cannot be generated."""


class PersonalizationService:
    def __init__(
        self,
        knowledge: KnowledgeService = knowledge_service,
        gap_analysis: GapAnalysisService = gap_analysis_service,
        resources: ResourceService = resource_service,
        gamification: GamificationService = gamification_service,
    ) -> None:
        self.knowledge = knowledge
        self.gap_analysis = gap_analysis
        self.resources = resources
        self.gamification = gamification

    def generate(
        self,
        goal_id: str,
        assessment_id: str,
        assessment,
        user_context: UserContext | None = None,
        learner_id: str | None = None,
    ) -> PersonalizationResponse:
        gap_analysis = self.gap_analysis.analyze(goal_id, assessment)
        gap_by_skill = {item.skill_id: item for item in gap_analysis}
        required_skills = self.knowledge.get_required_skills(goal_id)
        required_ids = {skill.id for skill in required_skills}
        ordered_skills = self._topological_order(required_skills)
        learning_style, difficulty, resource_preference = self._resource_preferences(user_context)

        roadmap: list[RoadmapNode] = []
        for skill in ordered_skills:
            gap = gap_by_skill[skill.id]
            if gap.classification == "skip":
                continue
            roadmap.append(
                RoadmapNode(
                    order=len(roadmap) + 1,
                    skill_id=skill.id,
                    skill_name=skill.name,
                    mastery=gap.mastery,
                    classification=gap.classification,
                    status="locked" if gap.classification == "locked" else "available",
                    estimated_effort=None,
                    prerequisites=[
                        prerequisite_id
                        for prerequisite_id in skill.prerequisites
                        if prerequisite_id in required_ids
                    ],
                    reason=gap.reason,
                    resources=self.resources.recommend_for_skill(
                        skill.id,
                        learning_style=learning_style,
                        difficulty=difficulty,
                        resource_preference=resource_preference,
                    ),
                    boss_battle_status=(
                        "completed"
                        if skill.id in self.gamification.get_profile(learner_id).passed_boss_skills
                        else
                        "locked"
                        if gap.classification == "locked"
                        else "available"
                        if gap.mastery is not None and gap.mastery >= 60
                        else "unavailable"
                    ),
                )
            )

        counts = {
            classification: sum(item.classification == classification for item in gap_analysis)
            for classification in ("skip", "review", "learn", "locked")
        }
        return PersonalizationResponse(
            goal_id=goal_id,
            assessment_id=assessment_id,
            summary=PersonalizationSummary(
                skills_to_skip=counts["skip"],
                skills_to_review=counts["review"],
                skills_to_learn=counts["learn"],
                skills_locked=counts["locked"],
            ),
            gap_analysis=gap_analysis,
            roadmap=roadmap,
        )

    @staticmethod
    def _resource_preferences(context: UserContext | None) -> tuple[str, str, str]:
        if context is None:
            return "mixed", "intermediate", "free_and_paid"
        style_map = {"videos": "video", "projects": "project"}
        difficulty_map = {"casual": "beginner", "standard": "intermediate", "hunter": "advanced", "monarch": "advanced"}
        return (
            style_map.get(context.learning_style or "", context.learning_style or "mixed"),
            difficulty_map.get(context.difficulty or "", "intermediate"),
            context.resource_preference or "free_and_paid",
        )

    @staticmethod
    def _topological_order(skills):
        skills_by_id = {skill.id: skill for skill in skills}
        ordered = []
        visiting: set[str] = set()
        visited: set[str] = set()

        def visit(skill_id: str) -> None:
            if skill_id in visiting:
                raise PersonalizationError(f"Circular dependency in roadmap: {skill_id}")
            if skill_id in visited:
                return
            visiting.add(skill_id)
            for prerequisite_id in skills_by_id[skill_id].prerequisites:
                if prerequisite_id in skills_by_id:
                    visit(prerequisite_id)
            visiting.remove(skill_id)
            visited.add(skill_id)
            ordered.append(skills_by_id[skill_id])

        for skill in skills:
            visit(skill.id)
        return ordered


personalization_service = PersonalizationService()