from dataclasses import asdict, dataclass, field
from typing import Any

from app.models.chat import ChatTurn
from app.models.external import ExternalMessageEvent
from app.models.outbound import OutboundChannelMessage


@dataclass
class PendingOutboundMessage:
    pending_id: str
    bundle_key: str
    platform: str
    conversation_id: str
    user_id: str
    turn: ChatTurn
    outbound_message: OutboundChannelMessage
    original_events: list[ExternalMessageEvent] = field(default_factory=list)
    preferred_language: str | None = None
    created_at_ts: float = 0.0
    send_at_ts: float = 0.0
    status: str = "pending"
    last_error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["turn"] = self.turn.to_dict()
        data["outbound_message"] = self.outbound_message.to_dict()
        data["original_events"] = [event.to_dict() for event in self.original_events]
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PendingOutboundMessage":
        return cls(
            pending_id=data["pending_id"],
            bundle_key=data["bundle_key"],
            platform=data["platform"],
            conversation_id=data["conversation_id"],
            user_id=data["user_id"],
            turn=ChatTurn.from_dict(data["turn"]),
            outbound_message=OutboundChannelMessage.from_dict(data["outbound_message"]),
            original_events=[
                ExternalMessageEvent.from_dict(item)
                for item in data.get("original_events", [])
            ],
            preferred_language=data.get("preferred_language"),
            created_at_ts=float(data.get("created_at_ts", 0.0)),
            send_at_ts=float(data.get("send_at_ts", 0.0)),
            status=data.get("status", "pending"),
            last_error=data.get("last_error"),
        )
