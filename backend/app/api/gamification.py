from fastapi import APIRouter, Depends

from app.dependencies import get_learner_id
from app.schemas.gamification import AchievementListResponse, GamificationProfile
from app.services.gamification_service import gamification_service

router = APIRouter(prefix="/api/gamification", tags=["gamification"])


@router.get("/profile", response_model=GamificationProfile)
def get_gamification_profile(learner_id: str = Depends(get_learner_id)) -> GamificationProfile:
    return gamification_service.get_profile(learner_id)


@router.get("/achievements", response_model=AchievementListResponse)
def get_achievements(learner_id: str = Depends(get_learner_id)) -> AchievementListResponse:
    return AchievementListResponse(achievements=gamification_service.get_achievements(learner_id))
