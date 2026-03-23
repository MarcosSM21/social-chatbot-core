from app.channels.http_channel_adapter import HttpChannelAdapter
from app.channels.platform_payload_parser import PlatformPayloadParser
from app.models.platform_payload import PlatformWebhookPayload
from app.services.platform_inbound_result import PlatformInboundResult
from app.outbound.base import OutboundSender

class PlatformInboundService:
    def __init__(self, payload_parser: PlatformPayloadParser, http_channel_adapter: HttpChannelAdapter, outbound_sender: OutboundSender) -> None:
        self.payload_parser = payload_parser
        self.http_channel_adapter = http_channel_adapter
        self.outbound_sender = outbound_sender

    
    def process_payload(self, payload: PlatformWebhookPayload) -> PlatformInboundResult:

        parse_result = self.payload_parser.parse(payload)

        if parse_result.status == "ignored":
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

        return PlatformInboundResult(
            status = "processed",
            detail = "Webhook event processed successfully.",
            channel_result = channel_result,
            outbound_result=outbound_result
        )
