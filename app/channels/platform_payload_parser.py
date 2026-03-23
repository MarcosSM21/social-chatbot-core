from app.models.external import ExternalMessageEvent
from app.models.platform_payload import PlatformWebhookPayload
from app.channels.parser_result import PayloadParserResult 



class PlatformPayloadParser:
    """Clase responsable de convertir payloads de web a eventos"""

    def parse(self, payload: PlatformWebhookPayload) -> ExternalMessageEvent:
        if not payload.platform.strip():
            raise ValueError("Platform payload is missing platform")
        
        if not payload.event_type.strip():
            raise ValueError("Platform payload is missing event_type")
        
        if not payload.conversation_id.strip():
            raise ValueError("Platform payload is missiong conversation_id")
        
        if not payload.user_id.strip():
            raise ValueError("Platform payload is missing user_id")
        
        if payload.event_type != "message_received":
            return PayloadParserResult(
                status="ignored",
                detail=f"Event type '{payload.event_type}' is not supported",
                event=None,
            )
        
        
        
        
        message_text = (payload.message_text or "").strip()

        if not message_text:
            return PayloadParserResult(
                status="ignored",
                detail="Event does not contain a usable text message",
                event = None
            )
        
        channel_metadata = {
            "event_type": payload.event_type,
            "payload_id": payload.payload_id,
        }

        if payload.raw_payload is not None:
            channel_metadata["raw_payload"] = payload.raw_payload

        event = ExternalMessageEvent(
            platform=payload.platform,
            conversation_id=payload.conversation_id,
            user_id=payload.user_id,
            message_text=message_text,
            message_id=payload.message_id,
            channel_metadata=channel_metadata
        )

        return PayloadParserResult(
            status="processable",
            detail = "Payload parsed successfully",
            event = event,
        )
    
    
