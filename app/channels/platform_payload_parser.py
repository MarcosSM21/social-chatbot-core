from app.models.external import ExternalMessageEvent
from app.models.platform_payload import PlatformWebhookPayload

class PlatformPayloadParser:
    """Clase responsable de convertir payloads de web a eventos"""

    def parse(self, payload: PlatformWebhookPayload) -> ExternalMessageEvent:
        message_text = (payload.message_text or "").strip()

        if not message_text:
            raise ValueError("El payload no contiene texto de mensaje válido")
        
        channel_metadata = {
            "event_type": payload.event_type,
            "payload_id": payload.payload_id,
        }

        if payload.raw_payload is not None:
            channel_metadata["raw_payload"] = payload.raw_payload

        return ExternalMessageEvent(
            platform=payload.platform,
            conversation_id=payload.conversation_id,
            user_id=payload.user_id,
            message_text=message_text,
            message_id=payload.message_id,
            channel_metadata=channel_metadata
        )