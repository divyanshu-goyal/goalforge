from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, JSON, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class Learner(Base):
    __tablename__ = "learners"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    sessions: Mapped[list["AnonymousSession"]] = relationship(back_populates="learner", cascade="all, delete-orphan")
    gamification_profile: Mapped["GamificationProfileRecord | None"] = relationship(
        back_populates="learner",
        uselist=False,
        cascade="all, delete-orphan",
    )


class AnonymousSession(Base):
    __tablename__ = "anonymous_sessions"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    learner_id: Mapped[str] = mapped_column(ForeignKey("learners.id", ondelete="CASCADE"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    learner: Mapped[Learner] = relationship(back_populates="sessions")


class GamificationProfileRecord(Base):
    __tablename__ = "gamification_profiles"

    id: Mapped[int] = mapped_column(primary_key=True)
    learner_id: Mapped[str] = mapped_column(ForeignKey("learners.id", ondelete="CASCADE"), unique=True, index=True)
    profile_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    processed_event_ids: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    shield_milestones_awarded: Mapped[list[int]] = mapped_column(JSON, nullable=False, default=list)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    learner: Mapped[Learner] = relationship(back_populates="gamification_profile")


class LearnerGoal(Base):
    __tablename__ = "learner_goals"
    __table_args__ = (UniqueConstraint("learner_id", "goal_id", name="uq_learner_goal"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    learner_id: Mapped[str] = mapped_column(ForeignKey("learners.id", ondelete="CASCADE"), index=True)
    goal_id: Mapped[str] = mapped_column(String(120), index=True)
    profile_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class AssessmentSessionRecord(Base):
    __tablename__ = "assessment_sessions"
    __table_args__ = (Index("ix_assessment_sessions_learner_id", "learner_id"),)

    assessment_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    learner_id: Mapped[str] = mapped_column(ForeignKey("learners.id", ondelete="CASCADE"))
    goal_id: Mapped[str] = mapped_column(String(120), index=True)
    context_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    result_json: Mapped[dict | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class QuestRecord(Base):
    __tablename__ = "quests"
    __table_args__ = (UniqueConstraint("learner_id", "quest_id", name="uq_learner_quest"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    learner_id: Mapped[str] = mapped_column(ForeignKey("learners.id", ondelete="CASCADE"), index=True)
    quest_id: Mapped[str] = mapped_column(String(200), index=True)
    payload_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)


class BossBattleAttemptRecord(Base):
    __tablename__ = "boss_battle_attempts"
    __table_args__ = (UniqueConstraint("learner_id", "attempt_id", name="uq_learner_boss_attempt"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    learner_id: Mapped[str] = mapped_column(ForeignKey("learners.id", ondelete="CASCADE"), index=True)
    attempt_id: Mapped[str] = mapped_column(String(36), index=True)
    payload_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
