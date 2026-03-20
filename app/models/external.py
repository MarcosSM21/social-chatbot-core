from dataclasses import asdict, dataclass
from typing import Any

@dataclass
class ExternalMessageEvent:
    platform: str
    conversation_id: str
    user_id: str
    message_text: str
    message_id: str | None = None
    channel_metadata: dict[str,Any] | None = None
    

    def to_dict(self) -> dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> "ExternalMessageEvent":
        return cls(
            platform=data.get("platform", ""),
            conversation_id=data.get("conversation_id", ""),
            user_id=data.get("user_id", ""),
            message_text=data.get("message_text", ""),
            message_id=data.get("message_id", None),
            channel_metadata=data.get("channel_metadata", None)
        )
    
