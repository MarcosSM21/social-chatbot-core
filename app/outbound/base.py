from typing import Protocol

from app.models.outbound import OutboundChannelMessage
from app.outbound.result import OutboundSendResult


class OutboundSender(Protocol):
    def send(self, message: OutboundChannelMessage) -> OutboundSendResult:
        ...
    
    