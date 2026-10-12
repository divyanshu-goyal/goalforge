from typing import Literal

from pydantic import BaseModel, Field


class AssessmentQuestion(BaseModel):
    id: str
    skill_id: str
    difficulty: Literal["beginner", "intermediate", "advanced"]
    question_type: Literal["multiple_choice"] = "multiple_choice"
    question: str
    options: list[str]


class AssessmentQuestionBankItem(AssessmentQuestion):
    correct_answer: str
    explanation: str


class UserContext(BaseModel):
    experience_level: str | None = None
    learning_style: str | None = None
    resource_preference: str | None = None
    difficulty: str | None = None


class AssessmentCreateRequest(BaseModel):
    goal_id: str
    user_context: UserContext | None = None


class AssessmentResponse(BaseModel):
    assessment_id: str
    goal_id: str
    questions: list[AssessmentQuestion]


class AssessmentAnswer(BaseModel):
    question_id: str
    answer: str


class AssessmentSubmitRequest(BaseModel):
    answers: list[AssessmentAnswer] = Field(default_factory=list)


class SkillResult(BaseModel):
    skill_id: str
    questions_attempted: int
    correct: int
    score: float
    classification: Literal["weak", "developing", "strong"]


class QuestionResult(BaseModel):
    question_id: str
    skill_id: str
    correct: bool
    explanation: str


class AssessmentResult(BaseModel):
    assessment_id: str
    total_questions: int
    total_correct: int
    overall_score: float
    overall_classification: Literal["weak", "developing", "strong"]
    skill_results: list[SkillResult]
    weak_skills: list[str]
    strong_skills: list[str]
    question_results: list[QuestionResult]
