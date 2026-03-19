from fastapi import FastAPI

from app.api.schemas import (
    MessageRequest,
    MessageResponse,
    HealthResponse,
    InfoResponse)


from app.core.settings import Settings
from app.engine.response_engine import ResponseEngine
from app.models.chat import ChatMessage
from app.orchestrator.chat_orquestrator import ChatOrchestrator
from app.services.conversation_service import ConversationService
from app.storage.local_chat_repository import LocalChatRepository



app = FastAPI(
    title="social-chatbot-core API",
    version="0.1.0",
    description="Interanl API para el chatbot social core project"
)

settings = Settings.from_env()

def build_orchestator() -> ChatOrchestrator:
    response_engine = ResponseEngine(settings=settings)
    chat_repository = LocalChatRepository()
    conversation_service = ConversationService(
        response_engine,
        chat_repository 
    )
    return ChatOrchestrator(conversation_service)

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
    
    orchestrator = build_orchestator()

    turn = orchestrator.handle_message(
        session_id=request.session_id,
        message=user_message
    )

    return MessageResponse(
        user_message=turn.user_message.content,
        assistant_message=turn.assistant_message.content,
        session_id=turn.session_id
    )