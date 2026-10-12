import os
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import requests


PORT = 8012


def _find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _wait_for_health(url: str, timeout: float = 30.0) -> None:
    deadline = time.time() + timeout
    last_error = None
    while time.time() < deadline:
        try:
            response = requests.get(url, timeout=2)
            if response.status_code == 200:
                return
            last_error = RuntimeError(f"health check returned {response.status_code}: {response.text}")
        except Exception as error:  # pragma: no cover - infrastructure wait path
            last_error = error
        time.sleep(0.5)
    raise AssertionError(f"backend did not become healthy at {url}: {last_error}")


def _read_assessment_answers() -> dict[str, str]:
    knowledge_root = Path(__file__).resolve().parents[2] / "knowledge" / "assessments" / "questions.json"
    data = __import__("json").loads(knowledge_root.read_text(encoding="utf-8"))
    return {item["id"]: item["correct_answer"] for item in data}


def _read_boss_answers() -> dict[str, str]:
    knowledge_root = Path(__file__).resolve().parents[2] / "knowledge" / "boss_battles" / "questions.json"
    data = __import__("json").loads(knowledge_root.read_text(encoding="utf-8"))
    return {item["id"]: item["correct_answer"] for item in data}


def test_two_process_restart_persistence():
    db_dir = Path(tempfile.mkdtemp(prefix="goalforge-restart-"))
    db_path = db_dir / "goalforge.db"
    port = _find_free_port()
    base_url = f"http://127.0.0.1:{port}"
    env = os.environ.copy()
    env["DATABASE_URL"] = f"sqlite:///{db_path}"

    process_a = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", str(port)],
        cwd=Path(__file__).resolve().parents[1],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    try:
        _wait_for_health(f"{base_url}/api/health")

        session = requests.Session()
        response = session.get(f"{base_url}/api/session")
        assert response.status_code == 200, response.text
        learner_id = response.json()["learner_id"]
        assert learner_id
        cookie_value = session.cookies.get("goalforge_session")
        assert cookie_value, "session cookie missing after creation"

        response = session.post(f"{base_url}/api/assessments", json={"goal_id": "learn_python"})
        assert response.status_code == 200, response.text
        assessment_id = response.json()["assessment_id"]
        assessment_questions = response.json()["questions"]
        answers = {question["id"]: _read_assessment_answers()[question["id"]] for question in assessment_questions}
        response = session.post(
            f"{base_url}/api/assessments/{assessment_id}/submit",
            json={"answers": [{"question_id": question_id, "answer": answer} for question_id, answer in answers.items()]},
        )
        assert response.status_code == 200, response.text
        assessment_result = response.json()
        assert assessment_result["assessment_id"] == assessment_id

        response = session.post(f"{base_url}/api/quests/generate", json={"goal_id": "learn_python", "assessment_id": assessment_id})
        assert response.status_code == 200, response.text
        quest_list = response.json()["quests"]
        assert quest_list
        quest_id = quest_list[0]["id"]
        response = session.post(f"{base_url}/api/quests/{quest_id}/start")
        assert response.status_code == 200, response.text
        assert response.json()["status"] == "active"
        response = session.post(f"{base_url}/api/quests/{quest_id}/complete")
        assert response.status_code == 200, response.text
        assert response.json()["status"] == "completed"

        response = session.get(f"{base_url}/api/gamification/profile")
        assert response.status_code == 200, response.text
        profile_before = response.json()

        response = session.post(f"{base_url}/api/boss-battles", json={"goal_id": "learn_python", "skill_id": "python_basics"})
        assert response.status_code == 200, response.text
        boss_attempt = response.json()
        boss_attempt_id = boss_attempt["attempt_id"]
        boss_questions = boss_attempt["questions"]
        boss_answers = [{"question_id": question["id"], "answer": _read_boss_answers()[question["id"]]} for question in boss_questions]
        response = session.post(f"{base_url}/api/boss-battles/{boss_attempt_id}/submit", json={"answers": boss_answers})
        assert response.status_code == 200, response.text
        boss_result = response.json()
        assert boss_result["attempt_id"] == boss_attempt_id

        process_a.terminate()
        process_a.wait(timeout=20)

        env_b = os.environ.copy()
        env_b["DATABASE_URL"] = f"sqlite:///{db_path}"
        process_b = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", str(port)],
            cwd=Path(__file__).resolve().parents[1],
            env=env_b,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        try:
            _wait_for_health(f"{base_url}/api/health")
            session_b = requests.Session()
            session_b.cookies.set("goalforge_session", cookie_value, domain="127.0.0.1", path="/")

            response = session_b.get(f"{base_url}/api/session")
            assert response.status_code == 200, response.text
            assert response.json()["learner_id"] == learner_id

            response = session_b.get(f"{base_url}/api/gamification/profile")
            assert response.status_code == 200, response.text
            profile_after = response.json()
            assert profile_after["total_xp"] >= profile_before["total_xp"]

            response = session_b.get(f"{base_url}/api/quests")
            assert response.status_code == 200, response.text
            quests_after = response.json()["quests"]
            assert any(quest["id"] == quest_id for quest in quests_after)
            quest_after = next(quest for quest in quests_after if quest["id"] == quest_id)
            assert quest_after["status"] == "completed"

            response = session_b.get(f"{base_url}/api/boss-battles/{boss_attempt_id}")
            assert response.status_code == 200, response.text
            assert response.json()["status"] in {"passed", "failed"}

            response = session_b.post(
                f"{base_url}/api/assessments/{assessment_id}/submit",
                json={"answers": [{"question_id": question["id"], "answer": _read_assessment_answers()[question["id"]]} for question in assessment_questions]},
            )
            assert response.status_code == 200, response.text
            assert response.json()["assessment_id"] == assessment_id

            response = session_b.post(f"{base_url}/api/quests/{quest_id}/complete")
            assert response.status_code == 200, response.text
            assert response.json()["status"] == "completed"

            response = session_b.post(f"{base_url}/api/boss-battles/{boss_attempt_id}/submit", json={"answers": boss_answers})
            assert response.status_code == 200, response.text
            assert response.json()["attempt_id"] == boss_attempt_id

            response = session_b.get(f"{base_url}/api/gamification/profile")
            assert response.status_code == 200, response.text
            final_profile = response.json()
            assert final_profile["total_xp"] == profile_after["total_xp"]
        finally:
            process_b.terminate()
            process_b.wait(timeout=20)
    finally:
        if process_a.poll() is None:
            process_a.terminate()
            process_a.wait(timeout=20)
        if process_a.stdout is not None:
            process_a.stdout.close()
