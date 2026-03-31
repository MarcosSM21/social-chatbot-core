from typing import Protocol

from app.models.conversation_context import ConversationContext

class GenerationProvider(Protocol):
    def generate_reply(self, conversation_context: ConversationContext) -> str:
        ...