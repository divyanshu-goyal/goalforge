from fastapi import HTTPException, Request


def get_learner_id(request: Request) -> str:
    learner_id = getattr(request.state, "learner_id", None)
    if not learner_id:
        raise HTTPException(status_code=401, detail="A valid anonymous learner session is required")
    return learner_id
