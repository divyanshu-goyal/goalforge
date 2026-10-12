# Knowledge

This directory will contain structured domain knowledge used to shape learning experiences.

- `goals/`: goal definitions and discovery content.
- `skills/`: programming skills and prerequisite relationships.
- `schemas/`: schemas for validating knowledge documents.

Sprint 2 stores the initial graph in `skills/skills.json` and `goals/goals.json`. Skill IDs are stable references, and each prerequisite must point to another skill in the graph. The backend validates duplicate IDs, missing references, and circular prerequisite dependencies when it loads these files.
