from fastapi import APIRouter, HTTPException

from app.roadmap.knowledge_service import knowledge_service
from app.schemas.knowledge import GoalDefinition, Skill

router = APIRouter(prefix="/api/knowledge", tags=["knowledge"])


@router.get("/skills", response_model=list[Skill])
def get_skills() -> list[Skill]:
    return knowledge_service.get_all_skills()


@router.get("/skills/{skill_id}", response_model=Skill)
def get_skill(skill_id: str) -> Skill:
    skill = knowledge_service.get_skill(skill_id)
    if skill is None:
        raise HTTPException(status_code=404, detail=f"Skill not found: {skill_id}")
    return skill


@router.get("/domains/{domain}", response_model=list[Skill])
def get_domain_skills(domain: str) -> list[Skill]:
    skills = knowledge_service.get_skills_by_domain(domain)
    if not skills:
        raise HTTPException(status_code=404, detail=f"Domain not found: {domain}")
    return skills


@router.get("/goals/{goal_id}", response_model=GoalDefinition)
def get_goal(goal_id: str) -> GoalDefinition:
    goal = knowledge_service.get_goal(goal_id)
    if goal is None:
        raise HTTPException(status_code=404, detail=f"Goal not found: {goal_id}")
    return goal
