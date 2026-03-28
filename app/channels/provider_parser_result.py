from dataclasses import dataclass, field


@dataclass
class InstagramParsedEvent:
    status: str
    detail: str
    external_conversation_id: str | None
    external_user_id: str | None
    incoming_message_text: str | None
    provider_message_id: str | None = None
    timestamp: int | None = None


@dataclass
class ProviderPayloadParseResult:
    status: str
    detail: str
    events: list[InstagramParsedEvent] = field(default_factory=list)
    
