import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from app.db.repositories import BossBattleRepository
from app.roadmap.knowledge_service import KnowledgeService, knowledge_service
from app.schemas.boss_battle import (
    BossBattleAnswer,
    BossBattleAttempt,
    BossBattleAttemptResponse,
    BossBattleQuestion,
    BossBattleQuestionBankItem,
    BossBattleResult,
)
from app.services.assessment_service import AssessmentService, assessment_service
from app.services.gamification_service import GamificationService, gamification_service

PASS_THRESHOLD = 80
BOSS_QUESTION_COUNT = 5
DEFAULT_BANK_PATH = Path(__file__).resolve().parents[3] / "knowledge" / "boss_battles" / "questions.json"


class BossBattleError(ValueError):
    """Raised when a Boss Battle cannot be started or submitted."""


class BossBattleNotFoundError(BossBattleError):
    pass


class BossBattleService:
    LEGACY_LEARNER_ID = "legacy"

    def __init__(
        self,
        knowledge: KnowledgeService = knowledge_service,
        assessments: AssessmentService = assessment_service,
        gamification: GamificationService = gamification_service,
        bank_path: Path = DEFAULT_BANK_PATH,
        repository: BossBattleRepository | None = None,
    ) -> None:
        self.knowledge = knowledge
        self.assessments = assessments
        self.gamification = gamification
        self.repository = repository or BossBattleRepository()
        self.questions = self._load_questions(bank_path)
        self._validate_question_bank()
        self._questions_by_id = {question.id: question for question in self.questions}
        self._attempts: dict[tuple[str, str], BossBattleAttempt] = {}

    def _load_questions(self, path: Path) -> list[BossBattleQuestionBankItem]:
        try:
            with path.open(encoding="utf-8") as file:
                data = json.load(file)
        except (FileNotFoundError, json.JSONDecodeError) as error:
            raise BossBattleError(f"Unable to load Boss Battle question bank: {path}") from error
        if not isinstance(data, list):
            raise BossBattleError("Boss Battle question bank must be a JSON array")
        try:
            return [BossBattleQuestionBankItem.model_validate(item) for item in data]
        except Exception as error:
            raise BossBattleError(f"Invalid Boss Battle question data: {error}") from error

    def _validate_question_bank(self) -> None:
        seen: set[str] = set()
        valid_skills = {skill.id for skill in self.knowledge.get_all_skills()}
        for question in self.questions:
            if question.id in seen:
                raise BossBattleError(f"Duplicate Boss Battle question ID: {question.id}")
            seen.add(question.id)
            if question.skill_id not in valid_skills:
                raise BossBattleError(f"Boss question references missing skill: {question.skill_id}")
            if not question.options or question.correct_answer not in question.options:
                raise BossBattleError(f"Boss question has an invalid answer option: {question.id}")
        for skill_id in {question.skill_id for question in self.questions}:
            if len([q for q in self.questions if q.skill_id == skill_id]) < BOSS_QUESTION_COUNT:
                raise BossBattleError(f"Skill '{skill_id}' has fewer than {BOSS_QUESTION_COUNT} Boss Battle questions")

    def start(
        self,
        goal_id: str,
        skill_id: str,
        learner_id: str | None = None,
    ) -> BossBattleAttemptResponse:
        learner_key = learner_id or self.LEGACY_LEARNER_ID
        goal = self.knowledge.get_goal(goal_id)
        if goal is None:
            raise BossBattleError(f"Goal not found: {goal_id}")
        skill = self.knowledge.get_skill(skill_id)
        if skill is None:
            raise BossBattleError(f"Skill not found: {skill_id}")
        if skill_id not in goal.required_skills:
            raise BossBattleError(f"Skill '{skill_id}' is not required by goal '{goal_id}'")

        latest = self.assessments.get_latest_result_for_goal(goal_id, learner_key)
        mastery = self._mastery_map(latest[1] if latest else None)
        mastery[skill_id] = max(mastery.get(skill_id, 0), self.gamification.get_mastery(learner_key).get(skill_id, 0))
        blocked = [prerequisite for prerequisite in skill.prerequisites if mastery.get(prerequisite, 0) < 70]
        if blocked:
            raise BossBattleError(f"Boss Battle locked: prerequisite mastery below 70: {', '.join(blocked)}")
        if mastery.get(skill_id, 0) < 60:
            raise BossBattleError(f"Boss Battle unavailable: {skill_id} mastery is below 60")

        questions = [question for question in self.questions if question.skill_id == skill_id]
        attempt_id = str(uuid4())
        attempt = BossBattleAttempt(
            attempt_id=attempt_id,
            goal_id=goal_id,
            skill_id=skill_id,
            question_ids=[question.id for question in questions[:BOSS_QUESTION_COUNT]],
            started_at=datetime.now(timezone.utc),
        )
        self._attempts[(learner_key, attempt_id)] = attempt
        self.repository.save(learner_key, attempt)
        return self._public_attempt(attempt)

    def get(self, attempt_id: str, learner_id: str | None = None) -> BossBattleAttemptResponse:
        return self._public_attempt(self._get_attempt(attempt_id, learner_id))

    def submit(
        self,
        attempt_id: str,
        answers: list[BossBattleAnswer | dict[str, str]],
        learner_id: str | None = None,
    ) -> BossBattleResult:
        learner_key = learner_id or self.LEGACY_LEARNER_ID
        attempt = self._get_attempt(attempt_id, learner_key)
        if attempt.status in {"passed", "failed"}:
            if attempt.result is None:
                raise BossBattleError("Completed Boss Battle has no result")
            return attempt.result
        normalized_answers = [
            BossBattleAnswer.model_validate(answer) if isinstance(answer, dict) else answer for answer in answers
        ]
        answer_map = {answer.question_id: answer.answer for answer in normalized_answers}
        if set(answer_map) != set(attempt.question_ids) or len(answer_map) != len(answers):
            raise BossBattleError("Submit exactly one answer for each Boss Battle question")

        questions = [self._questions_by_id[question_id] for question_id in attempt.question_ids]
        correct = [question for question in questions if answer_map[question.id] == question.correct_answer]
        score = round(len(correct) / len(questions) * 100, 2)
        passed = score >= PASS_THRESHOLD
        latest = self.assessments.get_latest_result_for_goal(attempt.goal_id, learner_key)
        mastery_map = self._mastery_map(latest[1] if latest else None)
        mastery_before = max(mastery_map.get(attempt.skill_id, 0), self.gamification.get_mastery(learner_key).get(attempt.skill_id, 0))
        mastery_after = max(mastery_before, score) if passed else mastery_before
        weak_areas = [question.question for question in questions if answer_map[question.id] != question.correct_answer]
        rank_before = self.gamification.get_profile(learner_key).current_rank
        goal = self.knowledge.get_goal(attempt.goal_id)
        current_mastery = self.gamification.get_mastery(learner_key)
        required_mastery = {skill_id: max(mastery_map.get(skill_id, 0), current_mastery.get(skill_id, 0)) for skill_id in goal.required_skills}
        required_mastery[attempt.skill_id] = mastery_after
        final_skill_id = goal.required_skills[-1]
        goal_completed = passed and all(value >= 85 for value in required_mastery.values()) and attempt.skill_id == final_skill_id
        if passed:
            self.gamification.record_boss_completion(
                attempt_id=attempt.attempt_id,
                goal_id=attempt.goal_id,
                skill_id=attempt.skill_id,
                score=score,
                mastery_before=mastery_before,
                required_skill_mastery=required_mastery,
                final_skill_id=final_skill_id,
                goal_final_boss_passed=goal_completed,
                learner_id=learner_key,
            )
        else:
            self.gamification.record_boss_failure(learner_key)
        rank_after = self.gamification.get_profile(learner_key).current_rank
        result = BossBattleResult(
            attempt_id=attempt.attempt_id,
            goal_id=attempt.goal_id,
            skill_id=attempt.skill_id,
            score=score,
            passed=passed,
            questions_correct=len(correct),
            questions_incorrect=len(questions) - len(correct),
            mastery_before=mastery_before,
            mastery_after=mastery_after,
            xp_awarded=500 if passed else 0,
            rank_before=rank_before,
            rank_after=rank_after,
            weak_areas=weak_areas,
            next_action="Continue to the next available skill." if passed else "Review the weak concepts, complete additional practice, then retry the Boss Battle.",
            goal_completed=goal_completed,
        )
        attempt.status = "passed" if passed else "failed"
        attempt.score = score
        attempt.completed_at = datetime.now(timezone.utc)
        attempt.result = result
        self.repository.save(learner_key, attempt)
        self._attempts[(learner_key, attempt_id)] = attempt
        return result

    def _get_attempt(self, attempt_id: str, learner_id: str | None = None) -> BossBattleAttempt:
        learner_key = learner_id or self.LEGACY_LEARNER_ID
        attempt = self._attempts.get((learner_key, attempt_id))
        if attempt is not None:
            return attempt
        attempt = self.repository.get(learner_key, attempt_id)
        if attempt is None:
            raise BossBattleNotFoundError(f"Boss Battle attempt not found: {attempt_id}")
        self._attempts[(learner_key, attempt_id)] = attempt
        return attempt

    def _public_attempt(self, attempt: BossBattleAttempt) -> BossBattleAttemptResponse:
        return BossBattleAttemptResponse(
            attempt_id=attempt.attempt_id,
            goal_id=attempt.goal_id,
            skill_id=attempt.skill_id,
            questions=[self._public_question(self._questions_by_id[question_id]) for question_id in attempt.question_ids],
            status=attempt.status,
            current_question=attempt.current_question,
            score=attempt.score,
            started_at=attempt.started_at,
            completed_at=attempt.completed_at,
            result=attempt.result,
        )

    @staticmethod
    def _public_question(question: BossBattleQuestionBankItem) -> BossBattleQuestion:
        return BossBattleQuestion(**question.model_dump(exclude={"correct_answer", "explanation"}))

    @staticmethod
    def _mastery_map(assessment) -> dict[str, float]:
        return {result.skill_id: result.score for result in assessment.skill_results} if assessment else {}


boss_battle_service = BossBattleService()
