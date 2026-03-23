from dataclasses import dataclass

from app.models.chat import ChatTurn

@dataclass
class PlatformInboundResult:
    status: str
    detail: str
    turn: ChatTurn | None = None

