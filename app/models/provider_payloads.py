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
    


@dataclass
class InstagramWebhookPayload:
    object: str
    entry_id: str
    messaging: list[InstagramWebhookMessageEvent] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "object": self.object,
            "entry_id": self.entry_id,
            "messaging": [event.to_dict() for event in self.messaging],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "InstagramWebhookPayload":
        return cls(
            object=data["object"],
            entry_id=data["entry_id"],
            messaging=[
                InstagramWebhookMessageEvent.from_dict(item)
                for item in data.get("messaging", [])
            ],
        )