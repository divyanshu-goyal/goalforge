from datetime import date

from fastapi.testclient import TestClient

from app.db.database import init_db
from app.db.repositories import GamificationRepository, LearnerSessionRepository
from app.main import app
from app.schemas.assessment import AssessmentAnswer
from app.schemas.boss_battle import BossBattleAnswer
from app.services.assessment_service import AssessmentService
from app.services.boss_battle_service import BossBattleService
from app.services.gamification_service import GamificationService
from app.quests.quest_service import QuestService


def test_database_initialization_and_stable_session_identity():
    init_db()
    with TestClient(app) as client:
        first = client.get("/api/session")
        second = client.get("/api/session")

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["learner_id"] == second.json()["learner_id"]
    assert client.cookies.get("goalforge_session")


def test_different_clients_receive_independent_learners():
    with TestClient(app) as first_client, TestClient(app) as second_client:
        first = first_client.get("/api/session").json()["learner_id"]
        second = second_client.get("/api/session").json()["learner_id"]

    assert first != second


def test_invalid_session_cookie_is_rejected():
    with TestClient(app) as client:
        client.cookies.set("goalforge_session", "malformed")
        response = client.get("/api/session")

    assert response.status_code == 401


def test_gamification_profiles_are_independent_and_idempotent():
    sessions = LearnerSessionRepository()
    first_id = sessions.create("first-test-session-hash")
    second_id = sessions.create("second-test-session-hash")
    service = GamificationService(GamificationRepository())

    service.record_quest_completion(
        quest_id="quest-1",
        quest_type="learning",
        completion_date=date(2026, 10, 10),
        goal_id="learn_python",
        learner_id=first_id,
    )
    service.record_quest_completion(
        quest_id="quest-1",
        quest_type="learning",
        completion_date=date(2026, 10, 10),
        goal_id="learn_python",
        learner_id=first_id,
    )

    assert service.get_profile(first_id).total_xp == 50
    assert service.get_profile(first_id).current_streak == 1
    assert service.get_profile(second_id).total_xp == 0


def test_gamification_survives_repository_reopen():
    sessions = LearnerSessionRepository()
    learner_id = sessions.create("restart-test-session-hash")
    GamificationService(GamificationRepository()).record_quest_completion(
        quest_id="restart-quest",
        quest_type="practice",
        completion_date=date(2026, 10, 10),
        goal_id="learn_python",
        learner_id=learner_id,
    )

    reopened_service = GamificationService(GamificationRepository())
    profile = reopened_service.get_profile(learner_id)

    assert profile.total_xp == 50
    assert profile.last_completed_quest_id == "restart-quest"


def test_assessment_cannot_be_submitted_by_another_learner():
    with TestClient(app) as first_client, TestClient(app) as second_client:
        first_client.get("/api/session")
        second_client.get("/api/session")
        assessment = first_client.post(
            "/api/assessments",
            json={"goal_id": "learn_python"},
        )
        assessment_id = assessment.json()["assessment_id"]
        response = second_client.post(
            f"/api/assessments/{assessment_id}/submit",
            json={"answers": []},
        )

    assert assessment.status_code == 200
    assert response.status_code == 404


def test_assessment_session_and_result_survive_service_reopen():
    learner_id = LearnerSessionRepository().create("assessment-restart-session")
    service = AssessmentService()
    assessment_id, questions = service.create_assessment("learn_python", learner_id=learner_id)
    correct_answers = [
        AssessmentAnswer(question_id=question.id, answer=next(item.correct_answer for item in service.questions if item.id == question.id))
        for question in questions
    ]
    service.submit_assessment(assessment_id, correct_answers, learner_id=learner_id)

    reopened = AssessmentService()
    result = reopened.get_result(assessment_id, learner_id)

    assert result is not None
    assert result.assessment_id == assessment_id
    assert reopened.get_latest_result_for_goal("learn_python", learner_id)[1].assessment_id == assessment_id


def test_quest_generation_and_completion_persist_across_service_reopen():
    learner_id = LearnerSessionRepository().create("quest-restart-session")
    assessment = AssessmentService()
    assessment_id, questions = assessment.create_assessment("learn_python", learner_id=learner_id)
    correct_answers = [
        AssessmentAnswer(question_id=question.id, answer=next(item.correct_answer for item in assessment.questions if item.id == question.id))
        for question in questions
    ]
    assessment.submit_assessment(assessment_id, correct_answers, learner_id=learner_id)

    service = QuestService(assessments=assessment)
    quests = service.generate("learn_python", assessment_id=assessment_id, learner_id=learner_id)
    quest_id = quests.quests[0].id
    service.start(quest_id, learner_id=learner_id)
    service.complete(quest_id, learner_id=learner_id)

    reopened = QuestService(assessments=AssessmentService())
    assert reopened.get_quest(quest_id, learner_id=learner_id).status == "completed"


def test_boss_battle_attempt_survives_service_reopen():
    learner_id = LearnerSessionRepository().create("boss-restart-session")
    assessment = AssessmentService()
    assessment_id, questions = assessment.create_assessment("learn_python", learner_id=learner_id)
    correct_answers = [
        AssessmentAnswer(question_id=question.id, answer=next(item.correct_answer for item in assessment.questions if item.id == question.id))
        for question in questions
    ]
    assessment.submit_assessment(assessment_id, correct_answers, learner_id=learner_id)

    service = BossBattleService(assessments=assessment)
    attempt = service.start("learn_python", "python_basics", learner_id=learner_id)
    answers = [
        BossBattleAnswer(
            question_id=question.id,
            answer=next(item.correct_answer for item in service.questions if item.id == question.id),
        )
        for question in attempt.questions
    ]
    service.submit(attempt.attempt_id, answers, learner_id=learner_id)

    reopened = BossBattleService(assessments=AssessmentService())
    stored = reopened.get(attempt.attempt_id, learner_id=learner_id)
    assert stored.status in {"passed", "failed"}
