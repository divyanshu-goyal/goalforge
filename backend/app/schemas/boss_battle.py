from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


BossQuestionType = Literal["mcq", "code_output", "conceptual"]
BossDifficulty = Literal["medium", "hard", "advanced"]
BossAttemptStatus = Literal["available", "in_progress", "passed", "failed"]


class BossBattleQuestion(BaseModel):
    id: str
    skill_id: str
    question: str
    question_type: BossQuestionType
    options: list[str]
    difficulty: BossDifficulty


class BossBattleQuestionBankItem(BossBattleQuestion):
    correct_answer: str
    explanation: str


class BossBattleStartRequest(BaseModel):
    goal_id: str
    skill_id: str


class BossBattleAttempt(BaseModel):
    attempt_id: str
    goal_id: str
    skill_id: str
    question_ids: list[str]
    current_question: int = 0
    answers: dict[str, str] = Field(default_factory=dict)
    score: float | None = None
    status: BossAttemptStatus = "in_progress"
    started_at: datetime
    completed_at: datetime | None = None
    result: "BossBattleResult | None" = None


class BossBattleAttemptResponse(BaseModel):
    attempt_id: str
    goal_id: str
    skill_id: str
    questions: list[BossBattleQuestion]
    status: BossAttemptStatus
    current_question: int
    score: float | None = None
    started_at: datetime
    completed_at: datetime | None = None
    result: "BossBattleResult | None" = None


class BossBattleAnswer(BaseModel):
    question_id: str
    answer: str


class BossBattleSubmitRequest(BaseModel):
    answers: list[BossBattleAnswer]


class BossBattleResult(BaseModel):
    attempt_id: str
    goal_id: str
    skill_id: str
    score: float
    passed: bool
    questions_correct: int
    questions_incorrect: int
    mastery_before: float
    mastery_after: float
    xp_awarded: int
    rank_before: str
    rank_after: str
    weak_areas: list[str]
    next_action: str
    goal_completed: bool
