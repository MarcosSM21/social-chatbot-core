from app.channels.http_channel_adapter import HttpChannelAdapter
from app.channels.platform_payload_parser import PlatformPayloadParser
from app.models.platform_payload import PlatformWebhookPayload
from app.services.platform_inbound_result import PlatformInboundResult


class PlatformInboundService:
    def __init__(self, payload_parser: PlatformPayloadParser, http_channel_adapter: HttpChannelAdapter) -> None:
        self.payload_parser = payload_parser
        self.http_channel_adapter = http_channel_adapter

    
    def process_payload(self, payload: PlatformWebhookPayload) -> PlatformInboundResult:

        parse_result = self.payload_parser.parse(payload)

        if parse_result.status == "ignored":
            return PlatformInboundResult(
                status = "ignored",
                detail = parse_result.detail,
                channel_result = None
            )
        
        if parse_result.event is None:
            raise ValueError(
                "Parser return no event for a processable payload"
            )
        
        channel_result = self.http_channel_adapter.process_event(parse_result.event)

        return PlatformInboundResult(
            status = "processed",
            detail = "Webhook event processed successfully.",
            channel_result = channel_result
        )
