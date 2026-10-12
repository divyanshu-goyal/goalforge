from fastapi import APIRouter, Depends, HTTPException

from app.ai.schemas import (
    AIMentorContext,
    AIMentorRequest,
    AIMentorResponse,
    AIPersonalizationContext,
    AIPersonalizationRequest,
    AIInsightResponse,
)
from app.ai.service import ai_service
from app.dependencies import get_learner_id
from app.roadmap.knowledge_service import knowledge_service
from app.services.assessment_service import assessment_service
from app.services.personalization_service import personalization_service

router = APIRouter(prefix="/api/ai", tags=["ai"])


@router.post("/personalize", response_model=AIInsightResponse)
def generate_ai_personalization(
    request: AIPersonalizationRequest,
    learner_id: str = Depends(get_learner_id),
) -> AIInsightResponse:
    assessment = assessment_service.get_result(request.assessment_id, learner_id)
    if assessment is None:
        raise HTTPException(status_code=400, detail=f"No submitted assessment exists: {request.assessment_id}")

    assessment_goal_id = assessment_service.get_goal_id(request.assessment_id, learner_id)
    if assessment_goal_id != request.goal_id:
        raise HTTPException(status_code=400, detail="Assessment does not belong to the requested goal")

    goal = knowledge_service.get_goal(request.goal_id)
    if goal is None:
        raise HTTPException(status_code=404, detail=f"Goal not found: {request.goal_id}")

    try:
        deterministic = personalization_service.generate(
            request.goal_id,
            request.assessment_id,
            assessment,
            assessment_service.get_context(request.assessment_id, learner_id),
            learner_id,
        )
    except Exception as error:  # pragma: no cover - deterministic personalization should already validate inputs
        raise HTTPException(status_code=400, detail=str(error)) from error

    resource_ids = []
    for node in deterministic.roadmap:
        for resource in node.resources:
            resource_ids.append(resource.id)

    context = AIPersonalizationContext(
        goal_id=request.goal_id,
        goal_name=goal.name,
        assessment_id=request.assessment_id,
        roadmap=[node.skill_id for node in deterministic.roadmap],
        resource_ids=resource_ids,
        mastery_by_skill={
            node.skill_id: node.mastery if node.mastery is not None else 0.0
            for node in deterministic.roadmap
        },
    )
    return ai_service.generate_personalization(context)


@router.post("/mentor", response_model=AIMentorResponse)
def generate_ai_mentor(
    request: AIMentorRequest,
    learner_id: str = Depends(get_learner_id),
) -> AIMentorResponse:
    goal = knowledge_service.get_goal(request.goal_id)
    goal_name = goal.name if goal is not None else request.goal_id
    context = AIMentorContext(
        goal_id=request.goal_id,
        goal_name=goal_name,
        current_focus=goal_name,
        mastery=None,
        message=request.message,
    )
    return ai_service.generate_mentor_response(context)
