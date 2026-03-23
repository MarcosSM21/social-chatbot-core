from dataclasses import dataclass

from app.models.chat import ChatTurn
from app.models.outbound import OutboundChannelMessage


@dataclass
class HttpChannelResult:
    turn: ChatTurn
    outbound_message: OutboundChannelMessage