from app.models.platform_payload import PlatformWebhookPayload
from app.models.provider_payloads import InstagramWebhookPayload
from app.channels.provider_parser_result import ProviderPayloadParseResult

class InstagramPayloadParser:
    """Transforms provider-specific Instagram payloads into generic platform payloads."""

    def parse(self, payload: InstagramWebhookPayload) -> ProviderPayloadParseResult:
        if not payload.object.strip():
            raise ValueError("Instagram payload is missing object.")

        if not payload.entry_id.strip():
            raise ValueError("Instagram payload is missing entry_id.")

        if not payload.messaging:
            raise ValueError("Instagram payload contains no messaging events.")

        for event in payload.messaging:
            sender_id = event.sender_id.strip()
            recipient_id = event.recipient_id.strip()
            text = (event.text or "").strip()

            if not sender_id:
                continue

            if not recipient_id:
                continue
            if not text:
                continue


            platform_payload = PlatformWebhookPayload(
            platform="instagram",
            event_type="message_received",
            conversation_id=event.sender_id,
            user_id=event.sender_id,
            message_text=event.text,
            message_id=event.message_id,
            payload_id=payload.entry_id,
            raw_payload=payload.to_dict(),
            )

            return ProviderPayloadParseResult(
                status = "processable",
                detail = "Instagram provider payload parsed successfully",
                payload = platform_payload
            )
    
        return ProviderPayloadParseResult(
            status = "ignored",
            detail="No supported text-based messaging event found in provider payload",
            payload = None
        )