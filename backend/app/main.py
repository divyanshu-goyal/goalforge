from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.goals import router as goals_router
from app.api.assessments import router as assessments_router
from app.api.knowledge import router as knowledge_router
from app.api.personalization import router as personalization_router
from app.api.resources import router as resources_router
from app.api.quests import router as quests_router
from app.api.gamification import router as gamification_router
from app.api.boss_battles import router as boss_battles_router
from app.api.ai import router as ai_router
from app.api.session import router as session_router
from app.db.database import init_db
from app.services.learner_session_service import (
    SESSION_COOKIE_NAME,
    LearnerSessionError,
    learner_session_service,
)


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield

app = FastAPI(title="GoalForge Backend", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(goals_router)
app.include_router(assessments_router)
app.include_router(knowledge_router)
app.include_router(personalization_router)
app.include_router(resources_router)
app.include_router(quests_router)
app.include_router(gamification_router)
app.include_router(boss_battles_router)
app.include_router(ai_router)
app.include_router(session_router)


@app.middleware("http")
async def anonymous_session_middleware(request, call_next):
    if not request.url.path.startswith("/api/") or request.url.path == "/api/health":
        return await call_next(request)

    token = request.cookies.get(SESSION_COOKIE_NAME)
    new_session = token is None
    try:
        if new_session:
            token, learner_id = learner_session_service.create_session()
        else:
            learner_id = learner_session_service.resolve(token)
    except LearnerSessionError as error:
        return JSONResponse(status_code=401, content={"detail": str(error)})

    request.state.learner_id = learner_id
    response = await call_next(request)
    if new_session:
        response.set_cookie(
            key=SESSION_COOKIE_NAME,
            value=token,
            httponly=True,
            samesite="lax",
            secure=False,
            max_age=60 * 60 * 24 * 30,
        )
    return response


@app.get("/api/health")
def health_check() -> dict[str, str]:
    return {"status": "ok", "service": "goalforge-backend"}
