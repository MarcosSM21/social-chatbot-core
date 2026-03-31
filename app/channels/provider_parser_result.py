from dataclasses import dataclass, field
from app.models.external import ExternalMessageEvent


@dataclass
class InstagramParsedEvent:
    status: str
    detail: str
    external_conversation_id: str | None
    external_user_id: str | None
    incoming_message_text: str | None
    provider_message_id: str | None = None
    timestamp: int | None = None

    def to_external_message_event(self) -> ExternalMessageEvent | None:
        if self.status != "captured":
            return None
        
        if not self.external_conversation_id or not self.external_user_id or not self.incoming_message_text:
            return None
        
        return ExternalMessageEvent(
            platform="instagram",
            conversation_id=self.external_conversation_id,
            user_id=self.external_user_id,
            message_text=self.incoming_message_text,
            message_id=self.provider_message_id,
            channel_metadata={
                "source": "instagram_webhook",
                "timestamp": self.timestamp,
                "detail": self.detail
            }
        )


@dataclass
class ProviderPayloadParseResult:
    status: str
    detail: str
    events: list[InstagramParsedEvent] = field(default_factory=list)
    
