from collections.abc import Callable
from dataclasses import dataclass
from uuid import uuid4

from sqlalchemy import select

from app.db.database import SessionLocal
from app.db.models import (
    AnonymousSession,
    AssessmentSessionRecord,
    BossBattleAttemptRecord,
    GamificationProfileRecord,
    Learner,
    QuestRecord,
)
from app.schemas.assessment import AssessmentResult, UserContext
from app.schemas.boss_battle import BossBattleAttempt
from app.schemas.gamification import GamificationProfile
from app.schemas.quest import Quest


@dataclass
class GamificationState:
    profile: GamificationProfile
    processed_event_ids: set[str]
    shield_milestones_awarded: set[int]


class LearnerSessionRepository:
    def create(self, session_token_hash: str) -> str:
        learner_id = str(uuid4())
        with SessionLocal() as db:
            db.add(Learner(id=learner_id))
            db.add(AnonymousSession(id=session_token_hash, learner_id=learner_id))
            db.commit()
        return learner_id

    def get_learner_id(self, session_token_hash: str) -> str | None:
        with SessionLocal() as db:
            session = db.get(AnonymousSession, session_token_hash)
            if session is None:
                return None
            return session.learner_id


class AssessmentSessionRepository:
    def create(
        self,
        learner_id: str,
        assessment_id: str,
        goal_id: str,
        questions: list[object],
        user_context: UserContext | None,
    ) -> None:
        payload = {
            "goal_id": goal_id,
            "user_context": user_context.model_dump(mode="json") if user_context is not None else {},
            "questions": [question.model_dump(mode="json") for question in questions],
        }
        with SessionLocal() as db:
            record = db.get(AssessmentSessionRecord, assessment_id)
            if record is None:
                db.add(
                    AssessmentSessionRecord(
                        assessment_id=assessment_id,
                        learner_id=learner_id,
                        goal_id=goal_id,
                        context_json=payload,
                    )
                )
            else:
                record.learner_id = learner_id
                record.goal_id = goal_id
                record.context_json = payload
            db.commit()

    def get(self, learner_id: str, assessment_id: str) -> AssessmentSessionRecord | None:
        with SessionLocal() as db:
            record = db.get(AssessmentSessionRecord, assessment_id)
            if record is None or record.learner_id != learner_id:
                return None
            return record

    def get_result(self, learner_id: str, assessment_id: str) -> AssessmentResult | None:
        record = self.get(learner_id, assessment_id)
        if record is None or record.result_json is None:
            return None
        return AssessmentResult.model_validate(record.result_json)

    def get_goal_id(self, learner_id: str, assessment_id: str) -> str | None:
        record = self.get(learner_id, assessment_id)
        if record is None:
            return None
        return record.goal_id

    def get_context(self, learner_id: str, assessment_id: str) -> UserContext | None:
        record = self.get(learner_id, assessment_id)
        if record is None:
            return None
        context_payload = record.context_json or {}
        user_context = context_payload.get("user_context", {})
        return UserContext.model_validate(user_context) if user_context else UserContext()

    def save_result(self, learner_id: str, assessment_id: str, result: AssessmentResult) -> AssessmentResult:
        with SessionLocal() as db:
            record = db.get(AssessmentSessionRecord, assessment_id)
            if record is None or record.learner_id != learner_id:
                raise ValueError(f"Assessment not found: {assessment_id}")
            if record.result_json is None:
                record.result_json = result.model_dump(mode="json")
            db.commit()
            return AssessmentResult.model_validate(record.result_json)

    def get_latest_result_for_goal(self, learner_id: str, goal_id: str) -> tuple[str, AssessmentResult] | None:
        with SessionLocal() as db:
            record = db.scalar(
                select(AssessmentSessionRecord)
                .where(
                    AssessmentSessionRecord.learner_id == learner_id,
                    AssessmentSessionRecord.goal_id == goal_id,
                    AssessmentSessionRecord.result_json.is_not(None),
                )
                .order_by(AssessmentSessionRecord.created_at.desc())
            )
            if record is None or record.result_json is None:
                return None
            return record.assessment_id, AssessmentResult.model_validate(record.result_json)


class QuestRepository:
    def save(self, learner_id: str, quest: Quest) -> None:
        with SessionLocal() as db:
            record = db.scalar(
                select(QuestRecord).where(
                    QuestRecord.learner_id == learner_id,
                    QuestRecord.quest_id == quest.id,
                )
            )
            if record is None:
                db.add(
                    QuestRecord(
                        learner_id=learner_id,
                        quest_id=quest.id,
                        payload_json=quest.model_dump(mode="json"),
                        status=quest.status,
                    )
                )
            else:
                record.payload_json = quest.model_dump(mode="json")
                record.status = quest.status
            db.commit()

    def get(self, learner_id: str, quest_id: str) -> Quest | None:
        with SessionLocal() as db:
            record = db.scalar(
                select(QuestRecord).where(
                    QuestRecord.learner_id == learner_id,
                    QuestRecord.quest_id == quest_id,
                )
            )
            if record is None:
                return None
            return Quest.model_validate(record.payload_json)

    def list(self, learner_id: str, goal_id: str | None = None) -> list[Quest]:
        with SessionLocal() as db:
            query = select(QuestRecord).where(QuestRecord.learner_id == learner_id)
            records = db.scalars(query.order_by(QuestRecord.id)).all()
            quests = [Quest.model_validate(record.payload_json) for record in records]
            if goal_id is not None:
                quests = [quest for quest in quests if quest.goal_id == goal_id]
            return quests

    def get_daily(self, learner_id: str, goal_id: str, due_date) -> list[Quest]:
        quests = self.list(learner_id, goal_id)
        return [quest for quest in quests if quest.goal_id == goal_id and quest.due_date == due_date]


class BossBattleRepository:
    def save(self, learner_id: str, attempt: BossBattleAttempt) -> None:
        with SessionLocal() as db:
            record = db.scalar(
                select(BossBattleAttemptRecord).where(
                    BossBattleAttemptRecord.learner_id == learner_id,
                    BossBattleAttemptRecord.attempt_id == attempt.attempt_id,
                )
            )
            payload = attempt.model_dump(mode="json")
            if record is None:
                db.add(
                    BossBattleAttemptRecord(
                        learner_id=learner_id,
                        attempt_id=attempt.attempt_id,
                        payload_json=payload,
                        status=attempt.status,
                    )
                )
            else:
                record.payload_json = payload
                record.status = attempt.status
            db.commit()

    def get(self, learner_id: str, attempt_id: str) -> BossBattleAttempt | None:
        with SessionLocal() as db:
            record = db.scalar(
                select(BossBattleAttemptRecord).where(
                    BossBattleAttemptRecord.learner_id == learner_id,
                    BossBattleAttemptRecord.attempt_id == attempt_id,
                )
            )
            if record is None:
                return None
            return BossBattleAttempt.model_validate(record.payload_json)


class GamificationRepository:
    def load(self, learner_id: str, default_factory: Callable[[], GamificationProfile]) -> GamificationState:
        with SessionLocal() as db:
            record = db.scalar(
                select(GamificationProfileRecord).where(GamificationProfileRecord.learner_id == learner_id)
            )
            if record is None:
                return GamificationState(default_factory(), set(), set())
            return GamificationState(
                profile=GamificationProfile.model_validate(record.profile_json),
                processed_event_ids=set(record.processed_event_ids or []),
                shield_milestones_awarded={int(value) for value in (record.shield_milestones_awarded or [])},
            )

    def save(self, learner_id: str, state: GamificationState) -> None:
        with SessionLocal() as db:
            record = db.scalar(
                select(GamificationProfileRecord).where(GamificationProfileRecord.learner_id == learner_id)
            )
            if record is None:
                record = GamificationProfileRecord(
                    learner_id=learner_id,
                    profile_json=state.profile.model_dump(mode="json"),
                    processed_event_ids=sorted(state.processed_event_ids),
                    shield_milestones_awarded=sorted(state.shield_milestones_awarded),
                )
                db.add(record)
            else:
                record.profile_json = state.profile.model_dump(mode="json")
                record.processed_event_ids = sorted(state.processed_event_ids)
                record.shield_milestones_awarded = sorted(state.shield_milestones_awarded)
            db.commit()
