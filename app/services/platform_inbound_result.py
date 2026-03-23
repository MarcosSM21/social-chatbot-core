from dataclasses import dataclass

from app.channels.http_channel_result import HttpChannelResult
from app.outbound.result import OutboundSendResult

@dataclass
class PlatformInboundResult:
    status: str
    detail: str
    channel_result: HttpChannelResult | None = None
    outbound_result: OutboundSendResult | None = None

    

