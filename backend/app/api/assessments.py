from fastapi import APIRouter, Depends, HTTPException

from app.dependencies import get_learner_id
from app.schemas.assessment import (
    AssessmentCreateRequest,
    AssessmentResponse,
    AssessmentResult,
    AssessmentSubmitRequest,
)
from app.services.assessment_service import (
    AssessmentError,
    AssessmentNotFoundError,
    assessment_service,
)

router = APIRouter(prefix="/api/assessments", tags=["assessments"])


@router.post("", response_model=AssessmentResponse)
def create_assessment(
    request: AssessmentCreateRequest,
    learner_id: str = Depends(get_learner_id),
) -> AssessmentResponse:
    try:
        assessment_id, questions = assessment_service.create_assessment(
            request.goal_id,
            request.user_context,
            learner_id,
        )
    except (AssessmentError, KeyError) as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    return AssessmentResponse(
        assessment_id=assessment_id,
        goal_id=request.goal_id,
        questions=questions,
    )


@router.post("/{assessment_id}/submit", response_model=AssessmentResult)
def submit_assessment(
    assessment_id: str,
    request: AssessmentSubmitRequest,
    learner_id: str = Depends(get_learner_id),
) -> AssessmentResult:
    try:
        return assessment_service.submit_assessment(assessment_id, request.answers, learner_id)
    except AssessmentNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except AssessmentError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
