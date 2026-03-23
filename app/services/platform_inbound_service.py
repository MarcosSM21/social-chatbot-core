from app.channels.http_channel_adapter import HttpChannelAdapter
from app.channels.platform_payload_parser import PlatformPayloadParser
from app.models.platform_payload import PlatformWebhookPayload
from app.services.platform_inbound_result import PlatformInboundResult
from app.outbound.base import OutboundSender
from app.storage.external_trace_repository import ExternalTraceRecord


class PlatformInboundService:
    def __init__(self, payload_parser: PlatformPayloadParser, http_channel_adapter: HttpChannelAdapter, outbound_sender: OutboundSender, trace_repository: ExternalTraceRecord) -> None:
        self.payload_parser = payload_parser
        self.http_channel_adapter = http_channel_adapter
        self.outbound_sender = outbound_sender
        self.trace_repository = trace_repository

    
    def process_payload(self, payload: PlatformWebhookPayload) -> PlatformInboundResult:

        parse_result = self.payload_parser.parse(payload)

        if parse_result.status == "ignored":
            
            self._save_trace(
                payload=payload,
                internal_session_id=None,
                outgoing_message_text=None,
                inbound_status="ignored",
                outbound_status=None,
                detail=parse_result.detail,
                outbound_message_id=None,
            )
            
            
            return PlatformInboundResult(
                status = "ignored",
                detail = parse_result.detail,
                channel_result = None,
                outbound_result= None

            )
        
        if parse_result.event is None:
            raise ValueError(
                "Parser return no event for a processable payload"
            )
        
        channel_result = self.http_channel_adapter.process_event(parse_result.event)
        outbound_result = self.outbound_sender.send(channel_result.outbound_message)

        self._save_trace(
            payload=payload,
            internal_session_id=channel_result.turn.session_id,
            outgoing_message_text=channel_result.outbound_message.message_text,
            inbound_status="processed",
            outbound_status=outbound_result.status,
            detail="Webhook event processed successfully.",
            outbound_message_id=outbound_result.external_message_id,
        )

        return PlatformInboundResult(
            status = "processed",
            detail = "Webhook event processed successfully.",
            channel_result = channel_result,
            outbound_result=outbound_result
        )
    


    def _save_trace(
        self,
        payload: PlatformWebhookPayload,
        internal_session_id: str | None,
        outgoing_message_text: str | None,
        inbound_status: str,
        outbound_status: str | None,
        detail: str,
        outbound_message_id: str | None,
    ) -> None:
        record = ExternalTraceRecord(
            platform=payload.platform,
            external_conversation_id=payload.conversation_id,
            external_user_id=payload.user_id,
            internal_session_id=internal_session_id,
            incoming_message_text=payload.message_text,
            outgoing_message_text=outgoing_message_text,
            inbound_status=inbound_status,
            outbound_status=outbound_status,
            detail=detail,
            provider_message_id=payload.message_id,
            outbound_message_id=outbound_message_id,
        )
        self.trace_repository.save_records(record)

