from app.ai.schemas import AIPersonalizationContext, AIMentorContext


def personalization_prompt(context: AIPersonalizationContext) -> str:
    roadmap_text = ", ".join(context.roadmap) if context.roadmap else "No roadmap provided."
    mastery_text = ", ".join(f"{skill_id}: {value}%" for skill_id, value in sorted(context.mastery_by_skill.items())) or "No mastery data."
    resources_text = ", ".join(context.resource_ids) if context.resource_ids else "No resources provided."
    return (
        "You are GoalForge's learning mentor. "
        "You provide recommendations only from the provided learner context. "
        "Do not change XP, mastery, rank, streaks, prerequisites, quest generation, or Boss Battle scoring. "
        "Return only structured JSON matching the schema.\n\n"
        f"Goal: {context.goal_id}\n"
        f"Goal name: {context.goal_name}\n"
        f"Assessment ID: {context.assessment_id or 'n/a'}\n"
        f"Learning style: {context.learning_style or 'mixed'}\n"
        f"Difficulty preference: {context.difficulty or 'mixed'}\n"
        f"Weekly time: {context.weekly_time or 'not specified'}\n"
        f"Motivation: {context.motivation or 'not specified'}\n"
        f"Mastery by skill: {mastery_text}\n"
        f"Deterministic roadmap: {roadmap_text}\n"
        f"Resource candidates: {resources_text}\n"
        f"Recent quest results: {', '.join(context.recent_quest_results) or 'none'}\n"
        f"Recent boss results: {', '.join(context.recent_boss_results) or 'none'}\n"
        "Provide concise, supportive recommendations in JSON with: summary, insights, recommended_skill_ids, recommended_resource_ids, recommended_quest_types, explanations. "
        "Each recommended_skill_id and recommended_resource_id must already exist in GoalForge, and recommended_quest_types must be one of learning, practice, challenge."
    )


def mentor_prompt(context: AIMentorContext) -> str:
    mastery_text = f"{context.mastery}%" if context.mastery is not None else "unknown"
    return (
        "You are the GoalForge AI mentor. "
        "You explain learning progress, keep advice grounded in the learner's current deterministic state, and never claim to have changed system state. "
        "Do not mention unavailable capabilities. Return a short, helpful response grounded in the current goal and mastery.\n\n"
        f"Goal: {context.goal_id}\n"
        f"Goal name: {context.goal_name}\n"
        f"Current focus: {context.current_focus or 'general learning'}\n"
        f"Current mastery: {mastery_text}\n"
        f"Current rank: {context.rank or 'unranked'}\n"
        f"Recent quest results: {', '.join(context.recent_quest_results) or 'none'}\n"
        f"Recent boss results: {', '.join(context.recent_boss_results) or 'none'}\n"
        f"User message: {context.message}\n"
        "Explain the likely cause of the learner's challenge and recommend the next step based on their actual state. "
        "Keep it concise and supportive."
    )
