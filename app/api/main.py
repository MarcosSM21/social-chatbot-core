from fastapi import FastAPI, HTTPException, Query

from app.api.schemas import (
    MessageRequest,
    MessageResponse,
    HealthResponse,
    InfoResponse,
    WebhookMessageRequest,
    WebhookVerifyResponse,
    WebhookEventResponse,
    InstagramWebhookPayloadRequest
)

from app.channels.instagram_payload_parser import InstagramPayloadParser
from app.models.provider_payloads import (
    InstagramWebhookMessageEvent,
    InstagramWebhookPayload
)


from app.core.settings import Settings
from app.models.external import ExternalMessageEvent
from app.core.container import build_http_channel_adapter, build_platform_inbound_service
from app.models.platform_payload import PlatformWebhookPayload
from app.providers.exceptions import GenerationProviderError
from app.channels.platform_payload_parser import PlatformPayloadParser
from app.storage.external_trace_repository import ExternalTraceRepository
from app.models.external_trace import ExternalTraceRecord




app = FastAPI(
    title="social-chatbot-core API",
    version="0.1.0",
    description="Interanl API para el chatbot social core project"
)

settings = Settings.from_env()



@app.get("/")
def root() -> dict:
    return {
        "message": "social-chatbot-core API is running",
        "docs_url": "/docs",
        "health_url": "/health",
        "info_url": "/info",
        "internal_messages_url": "/internal/messages",
        "generic_webhook_verify_url": "/webhooks/verify",
        "generic_webhook_messages_url": "/webhooks/messages",
        "instagram_webhook_verify_url": "/providers/instagram/webhook/verify",
        "instagram_webhook_messages_url": "/providers/instagram/webhook/messages",
    }

@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok")

@app.get("/info", response_model=InfoResponse)
def info() -> InfoResponse:
    return InfoResponse(
        service_name="social-chatbot-core",
        version="0.1.0",
        enviroment=settings.app_env,
        llm_provider=settings.llm_provider
    )


@app.post("/internal/messages", response_model=MessageResponse)
def create_internal_message(request: MessageRequest) -> MessageResponse:
    
    event = ExternalMessageEvent(
        platform="api",
        conversation_id=request.session_id,
        user_id="api-user",
        message_text=request.message,
        channel_metadata={
            "source": "internal_api"
        }
    )
    
    http_channel_adapter = build_http_channel_adapter(settings)

    

    try:
        channel_result = http_channel_adapter.process_event(event)
    except GenerationProviderError as exc:
        raise HTTPException(status_code=503, detail=f"Generation provider error: {exc}") from exc

    return MessageResponse(
        user_message=channel_result.turn.user_message.content,
        assistant_message=channel_result.turn.assistant_message.content,
        session_id=channel_result.turn.session_id
    )


@app.get("/webhooks/verify", response_model=WebhookVerifyResponse)
def verify_webhook(
    mode: str = Query(..., description="Modo de verificación"),
    token: str = Query(..., description="Token de verificación"),
    challenge: str = Query(..., description="Desafío de verificación")
) -> WebhookVerifyResponse:
    if mode!="subscribe":
        raise HTTPException(status_code=400, detail="Invalid mode")
    
    if token != settings.webhook_verify_token:
        raise HTTPException(status_code=403, detail="Invalid token")
    
    return WebhookVerifyResponse(challenge=challenge)



@app.post("/webhooks/messages")
def receive_webhook_message(request: WebhookMessageRequest) -> MessageResponse | WebhookEventResponse:
    
    inbound_service = build_platform_inbound_service(settings)

    payload = PlatformWebhookPayload(
        platform=request.platform,
        event_type=request.event_type,
        conversation_id=request.conversation_id,
        user_id=request.user_id,
        message_text=request.message_text,
        message_id=request.message_id,
        payload_id=request.payload_id,
        raw_payload=request.channel_metadata,
    )

    

    try:
        inbound_result = inbound_service.process_payload(payload)

        if inbound_result.status == "ignored":
            return WebhookEventResponse(
                status="ignored",
                detail=inbound_result.detail
            )
        if inbound_result.channel_result is None:
            return HTTPException(
                status_code=500,
                detail = "Parser returned no event for a processable payload"
            )

    except ValueError as exc:
        raise HTTPException(status_code=400, detail=f"Invalid payload: {exc}") from exc
    except GenerationProviderError as exc:
        raise HTTPException(status_code=503, detail=f"Generation provider error: {exc}") from exc

    turn = inbound_result.channel_result.turn

    return MessageResponse(
        session_id=turn.session_id,
        user_message=turn.user_message.content,
        assistant_message=turn.assistant_message.content
    )


@app.post("/providers/instagram/webhook/messages")
def receive_instagram_webhook_message(request: InstagramWebhookPayloadRequest) -> MessageResponse | WebhookEventResponse:

    instagram_parser = InstagramPayloadParser()
    inbound_service = build_platform_inbound_service(settings)
    

    provider_payload = InstagramWebhookPayload(
        object = request.object,
        entry_id = request.entry_id,
        messaging = [
            InstagramWebhookMessageEvent(
                sender_id = item.sender_id,
                recipient_id= item.recipient_id,
                timestamp= item.timestamp,
                message_id = item.message_id,
                text=item.text
            ) for item in request.messaging
        ]
    )

    try:
        provider_parser_result = instagram_parser.parse(provider_payload)
        
    
        if provider_parser_result.status == "ignored":
            trace_repository = ExternalTraceRepository()
            trace_repository.save_records(
                ExternalTraceRecord(
                    platform="instagram",
                    external_conversation_id=provider_payload.messaging[0].sender_id if provider_payload.messaging else "unknown",
                    external_user_id=provider_payload.messaging[0].sender_id if provider_payload.messaging else "unknown",
                    internal_session_id=None,
                    incoming_message_text=provider_payload.messaging[0].text if provider_payload.messaging else None,
                    outgoing_message_text=None,
                    inbound_status="ignored",
                    outbound_status=None,
                    detail= provider_parser_result.detail,
                    provider_message_id=provider_payload.messaging[0].message_id if provider_payload.messaging else None,
                    outbound_message_id=None,
                )
    )
            return WebhookEventResponse(
                status="ignored",
                detail = provider_parser_result.detail
            )
        
        if provider_parser_result.payload is None:
            return WebhookEventResponse(
                status="ignored",
                detail=provider_parser_result.detail
            )
        
        
        inbound_result = inbound_service.process_payload(provider_parser_result.payload) 
        
        if inbound_result.status == "ignored":
            return WebhookEventResponse(
                status="ignored",
                detail = inbound_result.detail
            )


        if inbound_result.channel_result is None:
            raise HTTPException(
                status_code = 500,
                detail= "Inbound service returned no channel result for a processed provider payload"
            )
        
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except GenerationProviderError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    
    turn = inbound_result.channel_result.turn

    return MessageResponse(
        session_id=turn.session_id,
        user_message=turn.user_message.content,
        assistant_message=turn.assistant_message.content
    )

@app.get("/providers/instagram/webhook/verify", response_model=WebhookVerifyResponse)
def verify_instagram_webhook(
    mode: str = Query(..., description="Verification mode"),
    token: str = Query(..., description="Verification token"),
    challenge: str = Query(..., description="Challenge string"),
) -> WebhookVerifyResponse:
    return verify_webhook(mode=mode, token=token, challenge=challenge)

