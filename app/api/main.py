from fastapi import FastAPI, HTTPException, Query

from app.api.schemas import (
    MessageRequest,
    MessageResponse,
    HealthResponse,
    InfoResponse,
    WebhookMessageRequest,
    WebhookVerifyResponse
)


from app.core.settings import Settings
from app.models.external import ExternalMessageEvent
from app.core.container import build_http_channel_adapter
from app.providers.exceptions import GenerationProviderError




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


@app.post("/messages", response_model=MessageResponse)
def create_message(request: MessageRequest) -> MessageResponse:
    
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
        turn = http_channel_adapter.process_event(event)
    except GenerationProviderError as exc:
        raise HTTPException(status_code=503, detail=f"Generation provider error: {exc}") from exc

    return MessageResponse(
        user_message=turn.user_message.content,
        assistant_message=turn.assistant_message.content,
        session_id=turn.session_id
    )


@app.get("/webhook/verify", response_model=WebhookVerifyResponse)
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



@app.post("/webhook/messages", response_model=MessageResponse)
def create_webhook_message(request: WebhookMessageRequest) -> MessageResponse:
    
    event = ExternalMessageEvent(
        platform=request.platform,
        conversation_id=request.conversation_id,
        user_id=request.user_id,
        message_text=request.message_text,
        message_id=request.message_id,
        channel_metadata=request.channel_metadata
    )
    
    http_channel= build_http_channel_adapter(settings)

    

    try:
        turn = http_channel.process_event(event)
    except GenerationProviderError as exc:
        raise HTTPException(status_code=503, detail=f"Generation provider error: {exc}") from exc

    return MessageResponse(
        user_message=turn.user_message.content,
        assistant_message=turn.assistant_message.content,
        session_id=turn.session_id
    )




