from app.models.platform_payload import PlatformWebhookPayload
from app.models.provider_payloads import InstagramWebhookPayload


class InstagramPayloadParser:
    """Transforms provider-specific Instagram payloads into generic platform payloads."""

    def parse(self, payload: InstagramWebhookPayload) -> PlatformWebhookPayload:
        if not payload.object.strip():
            raise ValueError("Instagram payload is missing object.")

        if not payload.entry_id.strip():
            raise ValueError("Instagram payload is missing entry_id.")

        if not payload.messaging:
            raise ValueError("Instagram payload contains no messaging events.")

        first_event = payload.messaging[0]

        if not first_event.sender_id.strip():
            raise ValueError("Instagram event is missing sender_id.")

        if not first_event.recipient_id.strip():
            raise ValueError("Instagram event is missing recipient_id.")

        return PlatformWebhookPayload(
            platform="instagram",
            event_type="message_received",
            conversation_id=first_event.sender_id,
            user_id=first_event.sender_id,
            message_text=first_event.text,
            message_id=first_event.message_id,
            payload_id=payload.entry_id,
            raw_payload=payload.to_dict(),
        )