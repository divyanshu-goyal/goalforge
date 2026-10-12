from fastapi import APIRouter, Request

router = APIRouter(prefix="/api", tags=["session"])


@router.get("/session")
def get_session(request: Request) -> dict[str, str]:
    return {"learner_id": request.state.learner_id}
