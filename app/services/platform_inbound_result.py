from dataclasses import dataclass

from app.channels.http_channel_result import HttpChannelResult

@dataclass
class PlatformInboundResult:
    status: str
    detail: str
    channel_result: HttpChannelResult | None = None

