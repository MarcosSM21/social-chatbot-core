from app.models.chat import ChatMessage, ChatTurn
from app.providers.base import GenerationProvider
from app.models.conversation_context import ConversationContext


class ResponseEngine:
    def __init__(self, generation_provider: GenerationProvider) -> None:
        self.generation_provider = generation_provider

    def generate_response(self, context: ConversationContext) -> ChatMessage:
        reply_text = self.generation_provider.generate_reply(context)
        return ChatMessage(role="assistant", content=reply_text)
    
