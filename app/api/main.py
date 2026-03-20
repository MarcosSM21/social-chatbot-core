from fastapi import FastAPI, HTTPException

from app.api.schemas import (
    MessageRequest,
    MessageResponse,
    HealthResponse,
    InfoResponse)


from app.core.settings import Settings
from app.models.chat import ChatMessage
from app.core.container import build_chat_orchestrator
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
    
    user_message = ChatMessage(role="user", content=request.message)
    
    orchestrator = build_chat_orchestrator(settings)


    try:
        turn = orchestrator.handle_message(
            session_id=request.session_id,
            message=user_message
        )
    except GenerationProviderError as exc:
        raise HTTPException(status_code=503, detail=f"Generation provider error: {exc}") from exc

    return MessageResponse(
        user_message=turn.user_message.content,
        assistant_message=turn.assistant_message.content,
        session_id=turn.session_id
    )