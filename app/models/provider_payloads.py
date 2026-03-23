from dataclasses import asdict, dataclass, field


@dataclass
class InstagramWebhookMessageEvent:
    sender_id: str
    recipient_id: str
    timestamp: int | None = None
    message_id: str | None = None
    text: str | None = None

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "InstagramWebhookMessageEvent":
        return cls(
            sender_id=data["sender_id"],
            recipient_id=data["recipient_id"],
            timestamp=data.get("timestamp"),
            message_id=data.get("message_id"),
            text=data.get("text"),
        )