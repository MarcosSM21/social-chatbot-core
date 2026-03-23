from dataclasses import dataclass


@dataclass
class OutboundSendResult:
    status: str
    detail: str
    external_message_id: str | None = None