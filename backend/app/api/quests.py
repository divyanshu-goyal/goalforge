from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query

from app.dependencies import get_learner_id
from app.quests.quest_service import QuestError, QuestNotFoundError, quest_service
from app.schemas.quest import DailyQuestResponse, Quest, QuestGenerateRequest, QuestListResponse

router = APIRouter(prefix="/api/quests", tags=["quests"])


@router.post("/generate", response_model=QuestListResponse)
def generate_quests(
    request: QuestGenerateRequest,
    learner_id: str = Depends(get_learner_id),
) -> QuestListResponse:
    try:
        return quest_service.generate(request.goal_id, request.assessment_id, request.mode, learner_id)
    except QuestError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@router.get("", response_model=QuestListResponse)
def get_quests(
    goal_id: Annotated[str | None, Query()] = None,
    learner_id: str = Depends(get_learner_id),
) -> QuestListResponse:
    return quest_service.get_quests(goal_id, learner_id)


@router.get("/daily", response_model=DailyQuestResponse)
def get_daily_quests(
    goal_id: str,
    assessment_id: Annotated[str | None, Query()] = None,
    learner_id: str = Depends(get_learner_id),
) -> DailyQuestResponse:
    try:
        return quest_service.get_daily(goal_id, assessment_id, learner_id)
    except QuestError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@router.get("/{quest_id}", response_model=Quest)
def get_quest(quest_id: str, learner_id: str = Depends(get_learner_id)) -> Quest:
    try:
        return quest_service.get_quest(quest_id, learner_id)
    except QuestNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.post("/{quest_id}/start", response_model=Quest)
def start_quest(quest_id: str, learner_id: str = Depends(get_learner_id)) -> Quest:
    try:
        return quest_service.start(quest_id, learner_id)
    except QuestNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except QuestError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@router.post("/{quest_id}/complete", response_model=Quest)
def complete_quest(quest_id: str, learner_id: str = Depends(get_learner_id)) -> Quest:
    try:
        return quest_service.complete(quest_id, learner_id)
    except QuestNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except QuestError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
