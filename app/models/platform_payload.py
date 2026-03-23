from dataclasses import asdict, dataclass
from typing import Any


@dataclass
class PlatformWebhookPayload:
    platform: str
    event_type: str
    conversation_id: str
    user_id: str
    message_text: str | None = None
    message_id: str | None = None
    payload_id: str | None = None
    raw_payload: dict[str, Any] | None = None

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "PlatformWebhookPayload":
        return cls(
            platform=data["platform"],
            event_type=data["event_type"],
            conversation_id=data["conversation_id"],
            user_id=data["user_id"],
            message_text=data.get("message_text"),
            message_id=data.get("message_id"),
            payload_id=data.get("payload_id"),
            raw_payload=data.get("raw_payload"),
        )


