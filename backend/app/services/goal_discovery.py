from app.schemas.goal import GoalDiscoveryRequest
from app.schemas.goal_profile import GoalProfile


WEEKLY_HOURS = {
    "less_than_5": 4,
    "5_to_10": 10,
    "10_to_20": 20,
    "20_plus": 20,
}


def create_goal_profile(data: GoalDiscoveryRequest) -> GoalProfile:
    return GoalProfile(
        goal=data.goal.strip(),
        objective=data.objective,
        experience_level=data.experience_level,
        weekly_hours=WEEKLY_HOURS[data.weekly_hours],
        timeline=data.timeline,
        learning_style=data.learning_style,
        difficulty=data.difficulty,
        resource_preference=data.resource_preference,
        motivation=data.motivation.strip(),
        prior_knowledge=data.prior_knowledge.strip(),
    )