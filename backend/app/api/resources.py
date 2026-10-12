from typing import Annotated

from fastapi import APIRouter, HTTPException, Query

from app.resources.resource_service import resource_service
from app.schemas.resource import (
    AccessType,
    Difficulty,
    LearningStyle,
    Resource,
    ResourceResponse,
    ResourceType,
)

router = APIRouter(prefix="/api/resources", tags=["resources"])


@router.get("/skills/{skill_id}", response_model=ResourceResponse)
def get_skill_resources(
    skill_id: str,
    learning_style: Annotated[LearningStyle | None, Query()] = None,
    access_type: Annotated[AccessType | None, Query()] = None,
    difficulty: Annotated[Difficulty | None, Query()] = None,
    resource_type: Annotated[ResourceType | None, Query()] = None,
) -> ResourceResponse:
    resources = resource_service.find_resources_for_skill(skill_id)
    if not resources:
        raise HTTPException(status_code=404, detail=f"No resources found for skill: {skill_id}")
    resources = resource_service.filter_resources(
        resources,
        access_type=access_type,
        difficulty=difficulty,
        learning_style=learning_style,
        resource_type=resource_type,
    )
    return ResourceResponse(skill_id=skill_id, resources=resources)


@router.get("/{resource_id}", response_model=Resource)
def get_resource(resource_id: str) -> Resource:
    resource = resource_service.get_resource(resource_id)
    if resource is None:
        raise HTTPException(status_code=404, detail=f"Resource not found: {resource_id}")
    return resource
