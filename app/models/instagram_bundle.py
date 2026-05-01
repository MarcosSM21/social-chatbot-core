from dataclasses import dataclass, field

from app.models.external import ExternalMessageEvent


@dataclass
class PendingInstagramBundle:
    bundle_key: str
    platform: str
    conversation_id: str
    user_id: str
    events: list[ExternalMessageEvent] = field(default_factory=list)
