from fastapi import APIRouter

from app.schemas.goal import GoalDiscoveryRequest
from app.schemas.goal_profile import GoalProfile
from app.services.goal_discovery import create_goal_profile

router = APIRouter(prefix="/api/goals", tags=["goals"])


@router.post("/discover", response_model=GoalProfile)
def discover_goal(data: GoalDiscoveryRequest) -> GoalProfile:
    return create_goal_profile(data)