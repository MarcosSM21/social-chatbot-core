from dataclasses import asdict, dataclass
from typing import Any


@dataclass
class ChatMessage:
    role: str
    content: str

    def to_dict(self) -> dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) ->"ChatMessage":
        return cls(
            role=data['role'], 
            content=data['content']
            )

@dataclass
class ChatTurn:
    session_id: str
    user_message: ChatMessage
    assistant_message: ChatMessage
    session_metadata: dict[str, Any] | None = None

    def to_dict(self) -> dict:
        return {
            "session_id": self.session_id,
            "user_message": self.user_message.to_dict(),
            "assistant_message": self.assistant_message.to_dict(),
            "session_metadata": self.session_metadata,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "ChatTurn":
        return cls(
            session_id=data['session_id'],
            user_message=ChatMessage.from_dict(data['user_message']),
            assistant_message=ChatMessage.from_dict(data['assistant_message']),
            session_metadata=data.get("session_metadata"),
        )
