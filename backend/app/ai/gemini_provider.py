import json
import os

from app.ai.provider import AIProvider
from app.ai.prompts import mentor_prompt, personalization_prompt
from app.ai.schemas import AIInsightResponse, AIMentorContext, AIMentorResponse, AIPersonalizationContext

try:
    from google import genai
except ImportError:  # pragma: no cover
    genai = None


class GeminiProvider(AIProvider):
    name = "gemini"

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")

    def is_available(self) -> bool:
        return bool(self.api_key) and genai is not None

    def generate_personalization(self, context: AIPersonalizationContext) -> AIInsightResponse:
        if not self.is_available():
            raise RuntimeError("Gemini API key is not configured.")
        client = genai.Client(api_key=self.api_key)
        prompt = personalization_prompt(context)
        response = client.models.generate_content(
            model="gemini-3.8-flash",
            contents=prompt,
        )
        text = getattr(response, "text", None) or str(response)
        try:
            payload = json.loads(text)
        except json.JSONDecodeError as error:
            raise ValueError(f"Gemini returned invalid JSON: {error}") from error
        return AIInsightResponse(
            summary=str(payload.get("summary") or "Your roadmap is being guided by the deterministic GoalForge system.") ,
            insights=[str(item) for item in payload.get("insights") or []],
            recommended_skill_ids=[str(item) for item in payload.get("recommended_skill_ids") or []],
            recommended_resource_ids=[str(item) for item in payload.get("recommended_resource_ids") or []],
            recommended_quest_types=[str(item) for item in payload.get("recommended_quest_types") or []],
            explanations=[str(item) for item in payload.get("explanations") or []],
            ai_available=True,
        )

    def generate_mentor_response(self, context: AIMentorContext) -> AIMentorResponse:
        if not self.is_available():
            raise RuntimeError("Gemini API key is not configured.")
        client = genai.Client(api_key=self.api_key)
        response = client.models.generate_content(
            model="gemini-3.8-flash",
            contents=mentor_prompt(context),
        )
        text = getattr(response, "text", None) or str(response)
        return AIMentorResponse(
            message=text.strip() or "Use the deterministic roadmap and complete the next available practice task.",
            context_used=[
                "current_goal",
                "current_focus",
                "current_mastery",
                "recent_quest_results",
                "recent_boss_results",
            ],
            ai_available=True,
        )
