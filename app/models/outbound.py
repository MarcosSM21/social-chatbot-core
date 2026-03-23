from dataclasses import asdict, dataclass
from typing import Any


@dataclass
class OutboundChannelMessage:
    platform: str
    conversation_id: str
    user_id: str
    message_text: str
    message_id: str | None = None
    channel_metadata: dict[str, Any] | None = None

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "OutboundChannelMessage":
        return cls(
            platform=data["platform"],
            conversation_id=data["conversation_id"],
            user_id=data["user_id"],
            message_text=data["message_text"],
            message_id=data.get("message_id"),
            channel_metadata=data.get("channel_metadata"),
        )