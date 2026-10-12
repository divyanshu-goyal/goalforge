from fastapi import APIRouter, Depends, HTTPException

from app.schemas.boss_battle import (
    BossBattleAttemptResponse,
    BossBattleResult,
    BossBattleStartRequest,
    BossBattleSubmitRequest,
)
from app.services.boss_battle_service import BossBattleError, BossBattleNotFoundError, boss_battle_service
from app.dependencies import get_learner_id

router = APIRouter(prefix="/api/boss-battles", tags=["boss-battles"])


@router.post("", response_model=BossBattleAttemptResponse)
def start_boss_battle(
    request: BossBattleStartRequest,
    learner_id: str = Depends(get_learner_id),
) -> BossBattleAttemptResponse:
    try:
        return boss_battle_service.start(request.goal_id, request.skill_id, learner_id)
    except BossBattleError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@router.get("/{attempt_id}", response_model=BossBattleAttemptResponse)
def get_boss_battle(attempt_id: str, learner_id: str = Depends(get_learner_id)) -> BossBattleAttemptResponse:
    try:
        return boss_battle_service.get(attempt_id, learner_id)
    except BossBattleNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.post("/{attempt_id}/submit", response_model=BossBattleResult)
def submit_boss_battle(
    attempt_id: str,
    request: BossBattleSubmitRequest,
    learner_id: str = Depends(get_learner_id),
) -> BossBattleResult:
    try:
        return boss_battle_service.submit(attempt_id, request.answers, learner_id)
    except BossBattleNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except BossBattleError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
