from dataclasses import asdict, dataclass


@dataclass
class ExternalTraceRecord:
    platform: str
    external_conversation_id: str
    external_user_id: str
    internal_session_id: str | None
    incoming_message_text: str | None
    outgoing_message_text: str | None
    inbound_status: str
    outbound_status: str | None
    detail: str
    provider_message_id: str | None = None
    outbound_message_id: str | None = None
    memory_loaded: bool | None = None
    memory_updated: bool | None = None

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "ExternalTraceRecord":
        return cls(
            platform=data["platform"],
            external_conversation_id=data["external_conversation_id"],
            external_user_id=data["external_user_id"],
            internal_session_id=data.get("internal_session_id"),
            incoming_message_text=data.get("incoming_message_text"),
            outgoing_message_text=data.get("outgoing_message_text"),
            inbound_status=data["inbound_status"],
            outbound_status=data.get("outbound_status"),
            detail=data["detail"],
            provider_message_id=data.get("provider_message_id"),
            outbound_message_id=data.get("outbound_message_id"),
            memory_loaded=data.get("memory_loaded"),
            memory_updated =data.get("memory_updated")
        )