from app.roadmap.knowledge_service import KnowledgeService, knowledge_service
from app.schemas.assessment import AssessmentResult
from app.schemas.personalization import GapAnalysisItem

SKIP_THRESHOLD = 85
REVIEW_THRESHOLD = 60
PREREQUISITE_THRESHOLD = 70


class GapAnalysisError(ValueError):
    """Raised when gap analysis cannot be calculated safely."""


class GapAnalysisService:
    def __init__(self, knowledge: KnowledgeService = knowledge_service) -> None:
        self.knowledge = knowledge

    def analyze(self, goal_id: str, assessment: AssessmentResult) -> list[GapAnalysisItem]:
        goal = self.knowledge.get_goal(goal_id)
        if goal is None:
            raise GapAnalysisError(f"Goal not found: {goal_id}")
        if not goal.required_skills:
            raise GapAnalysisError(f"Goal has no required skills: {goal_id}")

        mastery_by_skill = {result.skill_id: result.score for result in assessment.skill_results}
        required_skills = self.knowledge.get_required_skills(goal_id)
        results: list[GapAnalysisItem] = []

        for skill in required_skills:
            mastery = mastery_by_skill.get(skill.id)
            blocked_by = [
                prerequisite_id
                for prerequisite_id in skill.prerequisites
                if mastery_by_skill.get(prerequisite_id, 0) < PREREQUISITE_THRESHOLD
            ]
            if blocked_by:
                missing_mastery = [
                    f"{prerequisite_id} has mastery {mastery_by_skill.get(prerequisite_id, 0):g}"
                    for prerequisite_id in blocked_by
                ]
                reason = (
                    f"Locked because prerequisite {', '.join(missing_mastery)} "
                    f"is below the required threshold of {PREREQUISITE_THRESHOLD}."
                )
                classification = "locked"
            elif mastery is None:
                classification = "learn"
                reason = "No assessment result exists for this required skill."
            elif mastery >= SKIP_THRESHOLD:
                classification = "skip"
                reason = f"Skipped because mastery is {mastery:g}%, above the skip threshold of {SKIP_THRESHOLD}."
            elif mastery >= REVIEW_THRESHOLD:
                classification = "review"
                reason = f"Review recommended because mastery is {mastery:g}%, within the review range."
            else:
                classification = "learn"
                reason = f"Learning required because mastery is {mastery:g}%, below the learning threshold of {REVIEW_THRESHOLD}."

            results.append(
                GapAnalysisItem(
                    skill_id=skill.id,
                    skill_name=skill.name,
                    mastery=mastery,
                    classification=classification,
                    reason=reason,
                    blocked_by=blocked_by,
                )
            )

        return results


gap_analysis_service = GapAnalysisService()
