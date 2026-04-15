from dataclasses import asdict, dataclass
from typing import Any

from app.models.chat import ChatMessage, ChatTurn
from app.models.conversation_safety import ConversationSafetyPolicy
from app.models.conversation_style import ConversationStyle
from app.models.conversation_character import ConversationCharacter


@dataclass
class ConversationContext:
    current_message: ChatMessage
    recent_history: list[ChatTurn]
    system_instructions: str
    safety_policy: ConversationSafetyPolicy
    safety_instructions: str
    character: ConversationCharacter
    character_instructions: str
    style: ConversationStyle
    style_instructions: str
    user_profile: str | None = None
    conversation_summary: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "current_message": self.current_message.to_dict(),
            "recent_history": [turn.to_dict() for turn in self.recent_history],
            "system_instructions": self.system_instructions,
            "safety_policy": self.safety_policy.to_dict(),
            "safety_instructions": self.safety_instructions,
            "character": self.character.to_dict(),
            "character_instructions": self.character_instructions,
            "style": self.style.to_dict(),
            "style_instructions": self.style_instructions,
            "user_profile": self.user_profile,
            "conversation_summary": self.conversation_summary,
        }