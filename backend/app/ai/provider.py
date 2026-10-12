from abc import ABC, abstractmethod

from app.ai.schemas import AIInsightResponse, AIMentorResponse, AIPersonalizationContext, AIMentorContext


class AIProvider(ABC):
    name = "provider"

    @abstractmethod
    def generate_personalization(self, context: AIPersonalizationContext) -> AIInsightResponse:
        raise NotImplementedError

    @abstractmethod
    def generate_mentor_response(self, context: AIMentorContext) -> AIMentorResponse:
        raise NotImplementedError
