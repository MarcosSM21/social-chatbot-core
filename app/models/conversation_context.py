from dataclasses import asdict, dataclass
from typing import Any

from app.models.chat import ChatMessage, ChatTurn
from app.models.conversation_style import ConversationStyle

@dataclass
class ConversationContext:
    current_message: ChatMessage
    recent_history: list[ChatTurn]
    system_instructions: str
    style: ConversationStyle
    style_instructions: str
    user_profile: str | None = None
    conversation_summary: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "current_message": self.current_message.to_dict(),
            "recent_history": [turn.to_dict() for turn in self.recent_history],
            "system_instructions": self.system_instructions,
            "style": self.style.to_dict(),
            "style_instructions": self.style_instructions,
            "user_profile": self.user_profile,
            "conversation_summary": self.conversation_summary,
        }