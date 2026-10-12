from datetime import date, datetime, timezone
from zoneinfo import ZoneInfo

from app.db.repositories import QuestRepository
from app.quests.quest_generator import QuestGenerator
from app.schemas.quest import DailyQuestResponse, Quest, QuestMode, QuestListResponse
from app.services.assessment_service import AssessmentService, assessment_service
from app.services.personalization_service import PersonalizationError, PersonalizationService, personalization_service
from app.services.gamification_service import GamificationService, gamification_service

QUEST_TIMEZONE = ZoneInfo("UTC")


class QuestError(ValueError):
    """Raised when quests cannot be generated or updated."""


class QuestNotFoundError(QuestError):
    """Raised when a quest ID is not known."""


class QuestService:
    LEGACY_LEARNER_ID = "legacy"

    def __init__(
        self,
        assessments: AssessmentService = assessment_service,
        personalization: PersonalizationService = personalization_service,
        generator: QuestGenerator | None = None,
        gamification: GamificationService = gamification_service,
        repository: QuestRepository | None = None,
    ) -> None:
        self.assessments = assessments
        self.personalization = personalization
        self.generator = generator or QuestGenerator()
        self.gamification = gamification
        self.repository = repository or QuestRepository()
        self._quests: dict[tuple[str, str], Quest] = {}
        self._daily_lists: dict[tuple[str, str, date, QuestMode], list[str]] = {}

    def generate(
        self,
        goal_id: str,
        assessment_id: str | None = None,
        mode: QuestMode = "normal",
        learner_id: str | None = None,
    ) -> QuestListResponse:
        learner_key = learner_id or self.LEGACY_LEARNER_ID
        resolved_assessment_id, assessment = self._resolve_assessment(goal_id, assessment_id, learner_key)
        context = self.assessments.get_context(resolved_assessment_id, learner_key)
        difficulty = self._difficulty_mode(context.difficulty if context else None)
        today = datetime.now(QUEST_TIMEZONE).date()
        daily_key = (learner_key, goal_id, today, mode)
        existing_ids = self._daily_lists.get(daily_key)
        if existing_ids is not None:
            return QuestListResponse(
                goal_id=goal_id,
                quests=[self._quests[(learner_key, quest_id)] for quest_id in existing_ids],
            )

        persisted = self.repository.get_daily(learner_key, goal_id, today)
        if persisted:
            saved_ids = [quest.id for quest in persisted]
            self._daily_lists[daily_key] = saved_ids
            for quest in persisted:
                self._quests[(learner_key, quest.id)] = quest
            return QuestListResponse(goal_id=goal_id, quests=persisted)

        roadmap = self.personalization.generate(
            goal_id,
            resolved_assessment_id,
            assessment,
            context,
            learner_key,
        )
        quests = self.generator.generate(goal_id, roadmap.roadmap, difficulty, today, mode)
        self._daily_lists[daily_key] = [quest.id for quest in quests]
        for quest in quests:
            self._quests[(learner_key, quest.id)] = quest
            self.repository.save(learner_key, quest)
        return QuestListResponse(goal_id=goal_id, quests=quests)

    def get_daily(
        self,
        goal_id: str,
        assessment_id: str | None = None,
        learner_id: str | None = None,
    ) -> DailyQuestResponse:
        generated = self.generate(goal_id, assessment_id, "normal", learner_id)
        return DailyQuestResponse(
            goal_id=goal_id,
            date=datetime.now(QUEST_TIMEZONE).date(),
            quests=generated.quests,
        )

    def get_quests(self, goal_id: str | None = None, learner_id: str | None = None) -> QuestListResponse:
        learner_key = learner_id or self.LEGACY_LEARNER_ID
        quests = self.repository.list(learner_key, goal_id)
        for quest in quests:
            self._quests[(learner_key, quest.id)] = quest
        return QuestListResponse(goal_id=goal_id or "all", quests=quests)

    def get_quest(self, quest_id: str, learner_id: str | None = None) -> Quest:
        learner_key = learner_id or self.LEGACY_LEARNER_ID
        quest = self._quests.get((learner_key, quest_id))
        if quest is None:
            quest = self.repository.get(learner_key, quest_id)
            if quest is None:
                raise QuestNotFoundError(f"Quest not found: {quest_id}")
            self._quests[(learner_key, quest_id)] = quest
        return quest

    def start(self, quest_id: str, learner_id: str | None = None) -> Quest:
        quest = self.get_quest(quest_id, learner_id)
        if quest.status != "available":
            raise QuestError(f"Quest cannot be started from status '{quest.status}'")
        quest.status = "active"
        self.repository.save(learner_id or self.LEGACY_LEARNER_ID, quest)
        self._quests[(learner_id or self.LEGACY_LEARNER_ID, quest_id)] = quest
        return quest

    def complete(self, quest_id: str, learner_id: str | None = None) -> Quest:
        learner_key = learner_id or self.LEGACY_LEARNER_ID
        quest = self.get_quest(quest_id, learner_key)
        if quest.status == "completed":
            return quest
        if quest.status != "active":
            raise QuestError(f"Quest cannot be completed from status '{quest.status}'")
        quest.status = "completed"
        quest.completed_at = datetime.now(timezone.utc)
        latest = self.assessments.get_latest_result_for_goal(quest.goal_id, learner_key)
        mastery_by_skill = (
            {result.skill_id: result.score for result in latest[1].skill_results}
            if latest is not None
            else {}
        )
        self.gamification.record_quest_completion(
            quest_id=quest.id,
            quest_type=quest.quest_type,
            completion_date=quest.completed_at.astimezone(QUEST_TIMEZONE).date(),
            goal_id=quest.goal_id,
            mastery_by_skill=mastery_by_skill,
            learner_id=learner_key,
        )
        self.repository.save(learner_key, quest)
        self._quests[(learner_key, quest_id)] = quest
        return quest

    def _resolve_assessment(self, goal_id: str, assessment_id: str | None, learner_id: str):
        if assessment_id:
            assessment = self.assessments.get_result(assessment_id, learner_id)
            if assessment is None:
                raise QuestError(f"No submitted assessment exists: {assessment_id}")
            if self.assessments.get_goal_id(assessment_id, learner_id) != goal_id:
                raise QuestError("Assessment does not belong to the requested goal")
            return assessment_id, assessment
        latest = self.assessments.get_latest_result_for_goal(goal_id, learner_id)
        if latest is None:
            raise QuestError(f"No submitted assessment exists for goal: {goal_id}")
        return latest

    @staticmethod
    def _difficulty_mode(value: str | None) -> str:
        return value if value in {"casual", "standard", "hunter", "monarch"} else "standard"


quest_service = QuestService()
