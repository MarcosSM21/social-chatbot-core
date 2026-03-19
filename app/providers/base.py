from typing import Protocol

from app.models.chat import ChatMessage, ChatTurn

class GenerationProvider(Protocol):
    def generate_reply(
            self, 
            message:ChatMessage, 
            history:list[ChatTurn]
            ) -> str:
        ...