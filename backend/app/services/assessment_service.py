import json
from pathlib import Path
from uuid import uuid4

from app.db.repositories import AssessmentSessionRepository
from app.roadmap.knowledge_service import KnowledgeService, knowledge_service
from app.schemas.assessment import (
    AssessmentAnswer,
    AssessmentQuestion,
    AssessmentQuestionBankItem,
    AssessmentResult,
    QuestionResult,
    SkillResult,
    UserContext,
)


class AssessmentError(ValueError):
    """Raised when an assessment cannot be created or submitted."""


class AssessmentNotFoundError(AssessmentError):
    """Raised when a submitted assessment session does not exist."""


class AssessmentService:
    LEGACY_LEARNER_ID = "legacy"

    def __init__(
        self,
        knowledge: KnowledgeService = knowledge_service,
        repository: AssessmentSessionRepository | None = None,
    ) -> None:
        self.knowledge = knowledge
        self.repository = repository or AssessmentSessionRepository()
        question_path = knowledge.knowledge_root / "assessments" / "questions.json"
        try:
            with question_path.open(encoding="utf-8") as file:
                raw_questions = json.load(file)
        except (FileNotFoundError, json.JSONDecodeError) as error:
            raise AssessmentError(f"Unable to load assessment question bank: {question_path}") from error

        if not isinstance(raw_questions, list):
            raise AssessmentError("Assessment question bank must contain a JSON array")
        self.questions = [AssessmentQuestionBankItem.model_validate(item) for item in raw_questions]
        self._validate_question_bank()
        self._questions_by_id = {question.id: question for question in self.questions}
        self._assessments: dict[tuple[str, str], list[AssessmentQuestionBankItem]] = {}
        self._assessment_goals: dict[tuple[str, str], str] = {}
        self._assessment_contexts: dict[tuple[str, str], UserContext] = {}
        self._assessment_results: dict[tuple[str, str], AssessmentResult] = {}

    def _key(self, learner_id: str | None, assessment_id: str) -> tuple[str, str]:
        return learner_id or self.LEGACY_LEARNER_ID, assessment_id

    def _validate_question_bank(self) -> None:
        question_ids: set[str] = set()
        valid_skills = {skill.id for skill in self.knowledge.get_all_skills()}
        for question in self.questions:
            if question.id in question_ids:
                raise AssessmentError(f"Duplicate assessment question ID: {question.id}")
            question_ids.add(question.id)
            if question.skill_id not in valid_skills:
                raise AssessmentError(
                    f"Question '{question.id}' references missing skill '{question.skill_id}'"
                )
            if question.correct_answer not in question.options:
                raise AssessmentError(
                    f"Question '{question.id}' has a correct answer that is not an option"
                )

    def create_assessment(
        self,
        goal_id: str,
        user_context: UserContext | None = None,
        learner_id: str | None = None,
    ) -> tuple[str, list[AssessmentQuestion]]:
        required_skills = self.knowledge.get_required_skills(goal_id)
        required_skill_ids = {skill.id for skill in required_skills}
        selected = [question for question in self.questions if question.skill_id in required_skill_ids]
        if not selected:
            raise AssessmentError(f"No assessment questions available for goal: {goal_id}")

        assessment_id = str(uuid4())
        key = self._key(learner_id, assessment_id)
        self._assessments[key] = selected
        self._assessment_goals[key] = goal_id
        self._assessment_contexts[key] = user_context or UserContext()
        self.repository.create(learner_id, assessment_id, goal_id, selected, user_context or UserContext())
        public_questions = [
            AssessmentQuestion(
                id=question.id,
                skill_id=question.skill_id,
                difficulty=question.difficulty,
                question_type=question.question_type,
                question=question.question,
                options=question.options,
            )
            for question in selected
        ]
        return assessment_id, public_questions

    def submit_assessment(
        self,
        assessment_id: str,
        answers: list[AssessmentAnswer],
        learner_id: str | None = None,
    ) -> AssessmentResult:
        key = self._key(learner_id, assessment_id)
        existing = self._assessment_results.get(key)
        if existing is not None:
            return existing
        existing = self.repository.get_result(learner_id or self.LEGACY_LEARNER_ID, assessment_id)
        if existing is not None:
            self._assessment_results[key] = existing
            return existing

        assessment_questions = self._assessments.get(key)
        if assessment_questions is None:
            saved = self.repository.get(learner_id, assessment_id)
            if saved is None:
                raise AssessmentNotFoundError(f"Assessment not found: {assessment_id}")
            assessment_questions = [
                AssessmentQuestionBankItem.model_validate(question)
                for question in (saved.context_json or {}).get("questions", [])
            ]
            self._assessments[key] = assessment_questions
            self._assessment_goals[key] = saved.goal_id
            self._assessment_contexts[key] = UserContext.model_validate((saved.context_json or {}).get("user_context", {})) if (saved.context_json or {}).get("user_context") else UserContext()

        question_map = {question.id: question for question in assessment_questions}
        submitted_ids = [answer.question_id for answer in answers]
        invalid_ids = sorted(set(submitted_ids) - set(question_map))
        if invalid_ids:
            raise AssessmentError(f"Question IDs do not belong to this assessment: {', '.join(invalid_ids)}")
        if len(submitted_ids) != len(set(submitted_ids)):
            raise AssessmentError("Each question may only be answered once")
        if len(answers) != len(assessment_questions):
            raise AssessmentError("Please answer every question before submitting")

        question_results: list[QuestionResult] = []
        by_skill: dict[str, list[bool]] = {}
        for answer in answers:
            question = question_map[answer.question_id]
            is_correct = answer.answer == question.correct_answer
            question_results.append(
                QuestionResult(
                    question_id=question.id,
                    skill_id=question.skill_id,
                    correct=is_correct,
                    explanation=question.explanation,
                )
            )
            by_skill.setdefault(question.skill_id, []).append(is_correct)

        skill_results = []
        for skill_id, outcomes in by_skill.items():
            correct = sum(outcomes)
            score = round(correct / len(outcomes) * 100, 2)
            skill_results.append(
                SkillResult(
                    skill_id=skill_id,
                    questions_attempted=len(outcomes),
                    correct=correct,
                    score=score,
                    classification=self._classification(score),
                )
            )

        total_correct = sum(result.correct for result in question_results)
        overall_score = round(total_correct / len(question_results) * 100, 2)
        result = AssessmentResult(
            assessment_id=assessment_id,
            total_questions=len(question_results),
            total_correct=total_correct,
            overall_score=overall_score,
            overall_classification=self._classification(overall_score),
            skill_results=skill_results,
            weak_skills=[result.skill_id for result in skill_results if result.classification == "weak"],
            strong_skills=[result.skill_id for result in skill_results if result.classification == "strong"],
            question_results=question_results,
        )
        self._assessment_results[key] = result
        self.repository.save_result(learner_id, assessment_id, result)
        return result

    def get_result(self, assessment_id: str, learner_id: str | None = None) -> AssessmentResult | None:
        key = self._key(learner_id, assessment_id)
        if key in self._assessment_results:
            return self._assessment_results[key]
        result = self.repository.get_result(learner_id or self.LEGACY_LEARNER_ID, assessment_id)
        if result is None:
            return None
        self._assessment_results[key] = result
        return result

    def get_goal_id(self, assessment_id: str, learner_id: str | None = None) -> str | None:
        key = self._key(learner_id, assessment_id)
        if key in self._assessment_goals:
            return self._assessment_goals[key]
        goal_id = self.repository.get_goal_id(learner_id or self.LEGACY_LEARNER_ID, assessment_id)
        if goal_id is not None:
            self._assessment_goals[key] = goal_id
        return goal_id

    def get_context(self, assessment_id: str, learner_id: str | None = None) -> UserContext | None:
        key = self._key(learner_id, assessment_id)
        if key in self._assessment_contexts:
            return self._assessment_contexts[key]
        context = self.repository.get_context(learner_id or self.LEGACY_LEARNER_ID, assessment_id)
        if context is not None:
            self._assessment_contexts[key] = context
        return context

    def get_latest_result_for_goal(
        self,
        goal_id: str,
        learner_id: str | None = None,
    ) -> tuple[str, AssessmentResult] | None:
        learner_key = learner_id or self.LEGACY_LEARNER_ID
        for learner_and_assessment in reversed(self._assessment_results):
            if learner_and_assessment[0] != learner_key:
                continue
            if self._assessment_goals.get(learner_and_assessment) == goal_id:
                return learner_and_assessment[1], self._assessment_results[learner_and_assessment]
        latest = self.repository.get_latest_result_for_goal(learner_key, goal_id)
        if latest is not None:
            self._assessment_results[(learner_key, latest[0])] = latest[1]
            self._assessment_goals[(learner_key, latest[0])] = goal_id
        return latest

    @staticmethod
    def _classification(score: float) -> str:
        if score < 60:
            return "weak"
        if score < 85:
            return "developing"
        return "strong"


assessment_service = AssessmentService()
