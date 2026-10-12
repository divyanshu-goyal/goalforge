# Persistence and Anonymous Sessions

GoalForge uses SQLAlchemy with SQLite for the first persistence slice.

## Development database

The default database is:

```text
backend/data/goalforge.db
```

Override it with `DATABASE_URL`:

```env
DATABASE_URL=sqlite:////absolute/path/to/goalforge.db
```

The schema is created during FastAPI startup. The database directory and files
are ignored by Git. There is no migration framework yet; schema changes require
an explicit reviewed migration step before production use.

## Anonymous learner identity

The backend issues an opaque random `goalforge_session` HttpOnly cookie. The
cookie is hashed and matched to an anonymous learner record in SQLite. The
frontend initializes the session at application startup and sends credentials
with API requests.

This is session continuity, not authentication. A person who obtains the cookie
can use that learner's progress, and clearing the cookie loses the ability to
recover the anonymous session. A future authenticated account should replace
the cookie-to-learner mapping while keeping learner-owned records.

## Persistence boundary

Persistent now:

- Learner and anonymous session identity.
- Gamification profile, XP, level, streak, buffs, achievements, rank, mastery,
  and processed completion event IDs.

Still process-local, but learner-scoped:

- Assessment questions, contexts, and results.
- Generated quests and daily quest lists.
- Boss Battle attempts and results.
- AI personalization cache.

Static JSON remains authoritative for the knowledge graph, resources, assessment
question bank, and Boss Battle question bank.

## Tests

Run the isolated SQLite persistence tests with:

```bash
cd backend
pytest -q
```

The persistence test suite verifies session identity, learner isolation,
malformed-cookie rejection, XP idempotency, repository reopen behavior, and
cross-learner assessment access.