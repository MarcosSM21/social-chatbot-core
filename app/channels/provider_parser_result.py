from dataclasses import dataclass

from app.models.platform_payload import PlatformWebhookPayload


@dataclass
class ProviderPayloadParseResult:
    status: str
    detail: str
    payload: PlatformWebhookPayload | None = None
    