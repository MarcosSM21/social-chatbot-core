from dataclasses import dataclass

from app.models.external import ExternalMessageEvent

@dataclass
class PayloadParserResult:
    status: str
    detail: str
    event: ExternalMessageEvent | None = None

    