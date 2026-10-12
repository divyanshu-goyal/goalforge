# GoalForge Backend

FastAPI service for GoalForge. Run from this directory with:

```bash
python -m uvicorn app.main:app --reload
```

## Database and anonymous sessions

The backend uses SQLite through SQLAlchemy. With no `DATABASE_URL`, the development
database is created at `backend/data/goalforge.db`. To use another database URL,
set it in the environment before starting the server:

```env
DATABASE_URL=sqlite:////absolute/path/to/goalforge.db
```

The application creates the current schema automatically at startup. Schema
changes should be introduced through explicit SQLAlchemy model changes and a
reviewed migration step before production deployment; a migration framework is
not included yet.

The backend issues an opaque, HttpOnly `goalforge_session` cookie for anonymous
learners. The cookie is validated against the database and maps to a stable
learner record. It is not authentication: anyone holding the cookie can use that
anonymous session, there is no account recovery, and cookies can be cleared or
stolen. A future authenticated identity provider can replace this session mapping.

Gamification profiles, XP, streaks, achievements, ranks, buffs, and mastery are
persistent and learner-scoped. Assessment sessions/results, generated quests,
and Boss Battle attempts are also persisted in SQLite and scoped by learner
session. The knowledge graph, resources, and question banks remain static JSON
data.

Run the backend tests with:

```bash
pytest -q
```
