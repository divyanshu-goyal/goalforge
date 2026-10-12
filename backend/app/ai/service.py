import logging
from typing import Any

from app.ai.gemini_provider import GeminiProvider
from app.ai.provider import AIProvider
from app.ai.schemas import AIInsightResponse, AIMentorContext, AIMentorResponse, AIPersonalizationContext
from app.roadmap.knowledge_service import knowledge_service
from app.resources.resource_service import resource_service

logger = logging.getLogger(__name__)


class FallbackProvider(AIProvider):
    name = "fallback"

    def generate_personalization(self, context: AIPersonalizationContext) -> AIInsightResponse:
        focus_skill = context.roadmap[0] if context.roadmap else "general learning"
        resource_ids = [rid for rid in context.resource_ids[:2]]
        summary = f"GoalForge's deterministic roadmap is active for {context.goal_name}. Focus on {focus_skill}."
        return AIInsightResponse(
            summary=summary,
            insights=[
                "The deterministic roadmap remains the source of truth for your current learning path.",
                "Your best next step is to complete the highest-priority available task before moving further.",
            ],
            recommended_skill_ids=context.roadmap[:3],
            recommended_resource_ids=resource_ids,
            recommended_quest_types=["practice", "learning"],
            explanations=[
                "GoalForge selected the next skill based on the deterministic roadmap and your current mastery.",
                "This recommendation is advisory only and does not override the roadmap.",
            ],
            ai_available=False,
        )

    def generate_mentor_response(self, context: AIMentorContext) -> AIMentorResponse:
        mastery = context.mastery if context.mastery is not None else 0
        focus = context.current_focus or "the next available learning task"
        return AIMentorResponse(
            message=(
                f"Your current focus is {focus}. "
                f"Your current mastery is {mastery}%. "
                "Continue with the deterministic roadmap, complete the highest-priority practice task, and retry the relevant Boss Battle when eligible."
            ),
            context_used=["current_goal", "current_focus", "current_mastery"],
            ai_available=False,
        )


class AIService:
    def __init__(self, provider: AIProvider | None = None):
        self.provider = provider or GeminiProvider() if GeminiProvider().is_available() else FallbackProvider()
        self.cache: dict[str, AIInsightResponse] = {}

    def generate_personalization(self, context: AIPersonalizationContext) -> AIInsightResponse:
        key = f"{context.goal_id}:{context.assessment_id}:{':'.join(context.roadmap)}:{':'.join(sorted(context.resource_ids))}"
        cached = self.cache.get(key)
        if cached is not None:
            return cached
        try:
            response = self.provider.generate_personalization(context)
            if not self._validate_personalization(response):
                raise ValueError("Gemini returned invalid recommendations.")
            self.cache[key] = response
            return response
        except Exception as exc:  # pragma: no cover - fallback path
            logger.warning("AI personalization failed; falling back to deterministic recommendations: %s", exc)
            fallback = FallbackProvider().generate_personalization(context)
            self.cache[key] = fallback
            return fallback

    def generate_mentor_response(self, context: AIMentorContext) -> AIMentorResponse:
        try:
            return self.provider.generate_mentor_response(context)
        except Exception as exc:  # pragma: no cover - fallback path
            logger.warning("AI mentor failed; falling back to deterministic mentoring guidance: %s", exc)
            return FallbackProvider().generate_mentor_response(context)

    @staticmethod
    def _validate_personalization(payload: AIInsightResponse) -> bool:
        if payload.recommended_skill_ids:
            for skill_id in payload.recommended_skill_ids:
                if knowledge_service.get_skill(skill_id) is None:
                    return False
        if payload.recommended_resource_ids:
            for resource_id in payload.recommended_resource_ids:
                if resource_service.get_resource(resource_id) is None:
                    return False
        valid_quest_types = {"learning", "practice", "challenge"}
        if any(quest_type not in valid_quest_types for quest_type in payload.recommended_quest_types):
            return False
        return True


ai_service = AIService()
