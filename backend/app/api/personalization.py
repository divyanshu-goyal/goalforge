from fastapi import APIRouter, Depends, HTTPException

from app.dependencies import get_learner_id
from app.schemas.personalization import PersonalizationRequest, PersonalizationResponse
from app.services.assessment_service import assessment_service
from app.services.gap_analysis_service import GapAnalysisError
from app.services.personalization_service import PersonalizationError, personalization_service

router = APIRouter(prefix="/api/personalization", tags=["personalization"])


@router.post("/analyze", response_model=PersonalizationResponse)
def analyze_personalization(
    request: PersonalizationRequest,
    learner_id: str = Depends(get_learner_id),
) -> PersonalizationResponse:
    assessment = assessment_service.get_result(request.assessment_id, learner_id)
    if assessment is None:
        raise HTTPException(
            status_code=400,
            detail=f"No submitted assessment exists: {request.assessment_id}",
        )

    assessment_goal_id = assessment_service.get_goal_id(request.assessment_id, learner_id)
    if assessment_goal_id != request.goal_id:
        raise HTTPException(
            status_code=400,
            detail="Assessment does not belong to the requested goal",
        )

    try:
        return personalization_service.generate(
            request.goal_id,
            request.assessment_id,
            assessment,
            assessment_service.get_context(request.assessment_id, learner_id),
            learner_id,
        )
    except (GapAnalysisError, PersonalizationError, KeyError) as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
