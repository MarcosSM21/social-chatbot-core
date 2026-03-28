from dataclasses import asdict, dataclass, field


@dataclass
class InstagramWebhookUser:
    id: str

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "InstagramWebhookUser":
        return cls(
            id=data["id"],
        )


@dataclass
class InstagramWebhookMessage:
    mid: str | None = None
    text: str | None = None
    is_echo: bool | None = None

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "InstagramWebhookMessage":
        return cls(
            mid=data.get("mid"),
            text=data.get("text"),
            is_echo=data.get("is_echo"),
        )


@dataclass
class InstagramWebhookMessagingEvent:
    sender: InstagramWebhookUser
    recipient: InstagramWebhookUser
    timestamp: int | None = None
    message: InstagramWebhookMessage | None = None

    def to_dict(self) -> dict:
        return {
            "sender": self.sender.to_dict(),
            "recipient": self.recipient.to_dict(),
            "timestamp": self.timestamp,
            "message": self.message.to_dict() if self.message is not None else None,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "InstagramWebhookMessagingEvent":
        message = data.get("message")

        return cls(
            sender=InstagramWebhookUser.from_dict(data["sender"]),
            recipient=InstagramWebhookUser.from_dict(data["recipient"]),
            timestamp=data.get("timestamp"),
            message=InstagramWebhookMessage.from_dict(message) if message is not None else None,
        )


@dataclass
class InstagramWebhookChangeValue:
    sender: InstagramWebhookUser | None = None
    recipient: InstagramWebhookUser | None = None
    timestamp: int | str | None = None
    message: InstagramWebhookMessage | None = None

    def to_dict(self) -> dict:
        return {
            "sender": self.sender.to_dict() if self.sender is not None else None,
            "recipient": self.recipient.to_dict() if self.recipient is not None else None,
            "timestamp": self.timestamp,
            "message": self.message.to_dict() if self.message is not None else None,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "InstagramWebhookChangeValue":
        sender = data.get("sender")
        recipient = data.get("recipient")
        message = data.get("message")

        return cls(
            sender=InstagramWebhookUser.from_dict(sender) if sender is not None else None,
            recipient=InstagramWebhookUser.from_dict(recipient) if recipient is not None else None,
            timestamp=data.get("timestamp"),
            message=InstagramWebhookMessage.from_dict(message) if message is not None else None,
        )


@dataclass
class InstagramWebhookChange:
    field: str
    value: InstagramWebhookChangeValue | None = None

    def to_dict(self) -> dict:
        return {
            "field": self.field,
            "value": self.value.to_dict() if self.value is not None else None,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "InstagramWebhookChange":
        value = data.get("value")

        return cls(
            field=data["field"],
            value=InstagramWebhookChangeValue.from_dict(value) if value is not None else None,
        )


@dataclass
class InstagramWebhookEntry:
    id: str
    time: int | None = None
    messaging: list[InstagramWebhookMessagingEvent] = field(default_factory=list)
    changes: list[InstagramWebhookChange] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "time": self.time,
            "messaging": [event.to_dict() for event in self.messaging],
            "changes": [change.to_dict() for change in self.changes],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "InstagramWebhookEntry":
        return cls(
            id=data["id"],
            time=data.get("time"),
            messaging=[
                InstagramWebhookMessagingEvent.from_dict(item)
                for item in data.get("messaging", [])
            ],
            changes=[
                InstagramWebhookChange.from_dict(item)
                for item in data.get("changes", [])
            ],
        )


@dataclass
class InstagramWebhookPayload:
    object: str
    entry: list[InstagramWebhookEntry] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "object": self.object,
            "entry": [entry.to_dict() for entry in self.entry],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "InstagramWebhookPayload":
        return cls(
            object=data["object"],
            entry=[
                InstagramWebhookEntry.from_dict(item)
                for item in data.get("entry", [])
            ],
        )
