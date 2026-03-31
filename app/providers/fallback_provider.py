from app.models.conversation_context import ConversationContext
from app.providers.base import GenerationProvider
from app.providers.exceptions import GenerationProviderError


class FallbackGenerationProvider:
    def __init__(self, primary_provider: GenerationProvider,fallback_provider: GenerationProvider) -> None:
        self.primary_provider = primary_provider
        self.fallback_provider = fallback_provider

    def generate_reply(self, context: ConversationContext) -> str:
        try:
            return self.primary_provider.generate_reply(context)
        except GenerationProviderError as exc:
            # Log the error from the primary provider here if desired
            return self.fallback_provider.generate_reply(context)