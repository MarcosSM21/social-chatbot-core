import uuid

from app.models.outbound import OutboundChannelMessage
from app.outbound.result import OutboundSendResult


class MockOutboundSender:
    def send(self, message: OutboundChannelMessage) -> OutboundSendResult:
        if not message.message_text.strip():
            return OutboundSendResult(
                status="failed",
                detail="Outbound message text is empty.",
                external_message_id=None,
            )

        return OutboundSendResult(
            status="sent",
            detail=(
                f"Mock outbound message sent to platform='{message.platform}', "
                f"conversation_id='{message.conversation_id}'."
            ),
            external_message_id=f"mock-out-{uuid.uuid4()}",
        )