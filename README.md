# GoalForge AI

GoalForge is an early working prototype of an adaptive learning platform for programming goals. It combines deterministic learning rules with an optional Gemini advisory layer. GoalForge remains the source of truth for assessments, quests, mastery, Boss Battles, and rewards.

## Implemented Features

- Goal discovery and goal setup
- Deterministic assessments with persisted results
- Personalized learning roadmaps and curated resources
- Daily quests with start, completion, and XP rewards
- Persistent XP, levels, streaks, achievements, ranks, buffs, and mastery
- Deterministic Boss Battles with persisted attempts and duplicate-safe submissions
- Anonymous learner sessions using an HttpOnly cookie
- Optional Gemini personalization with deterministic fallback behavior
- Learner isolation across sessions

## Architecture

```text
frontend/   Next.js 15, React 19, TypeScript, and Tailwind CSS
backend/    FastAPI, SQLAlchemy, and the AI provider abstraction
knowledge/  Static goals, skills, assessments, and Boss Battle question banks
resources/  Curated learning resources
docs/       Architecture, API, persistence, and development notes
```

The frontend calls the backend over HTTP. The backend owns deterministic business rules and persists learner-owned state in SQLite. Gemini is advisory only: unavailable, failed, or malformed provider responses fall back to deterministic recommendations.

## Prerequisites

- Python 3.11 or newer
- Node.js 20 or newer
- npm

## Setup

From the repository root, create a Python environment and install the backend dependencies:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

In a second terminal, install the frontend dependencies:

```bash
cd frontend
npm install
```

## Environment Configuration

The environment templates contain placeholders only:

- Copy `backend/.env.example` to `backend/.env` for backend settings.
- Copy `frontend/.env.example` to `frontend/.env.local` for frontend settings.

Backend settings:

```env
GEMINI_API_KEY=your_api_key_here
DATABASE_URL=sqlite:////absolute/path/to/goalforge.db
```

`GEMINI_API_KEY` is optional. Without it, the backend uses deterministic fallback recommendations. `DATABASE_URL` is optional; when omitted, the backend creates `backend/data/goalforge.db`.

Frontend settings:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

Do not commit `.env`, `.env.local`, API keys, local databases, or generated runtime files.

## Run Locally

Start the backend from `backend/`:

```bash
python -m uvicorn app.main:app --reload
```

The backend health check is available at <http://localhost:8000/api/health>.

Start the frontend from `frontend/` in another terminal:

```bash
npm run dev
```

Open <http://localhost:3000>. The basic demonstration path is: choose a goal, complete the assessment, review the roadmap, open quests, complete a quest, and attempt a Boss Battle. Refreshing the app retains persisted learner state while the same SQLite database and anonymous session cookie are retained.

## Checks

Backend checks:

```bash
cd backend
pytest -q
python3 -m compileall -q app
```

Frontend checks:

```bash
cd frontend
npm run lint
npm run build
```

## Persistence and Limitations

SQLite is initialized automatically when the backend starts. Persisted assessments, quests, Boss Battles, gamification state, and anonymous learner sessions survive backend restarts only when the same database file is retained. The current prototype does not include full authentication, account recovery, user accounts, production migrations, arbitrary code execution, or production-grade operational monitoring.

Anonymous sessions are not equivalent to production authentication. Anyone holding an anonymous session cookie can use that session, and clearing or losing the cookie loses access to the anonymous learner identity. The prototype is suitable for local evaluation and early feedback, not production deployment.
