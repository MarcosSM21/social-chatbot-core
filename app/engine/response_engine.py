from app.models.chat import ChatMessage, ChatTurn
from app.providers.base import GenerationProvider


class ResponseEngine:
    def __init__(self, generation_provider: GenerationProvider) -> None:
        self.generation_provider = generation_provider

    def generate_response(
        self,
        message: ChatMessage,
        history: list[ChatTurn],
    ) -> ChatMessage:
        
        reply_text = self.generation_provider.generate_reply(
            message, 
            history
            )
        return ChatMessage(role="assistant", content=reply_text)
    
