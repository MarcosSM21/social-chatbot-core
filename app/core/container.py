import uuid 

from app.channels.local_channel import LocalChannel
from app.core.settings import Settings
from app.engine.response_engine import ResponseEngine
from app.orchestrator.chat_orquestrator import ChatOrchestrator
from app.services.conversation_service import ConversationService
from app.storage.local_chat_repository import LocalChatRepository
from app.providers.mock_provider import MockGenerationProvider
from app.providers.local_llm_provider import LocalLLMGenerationProvider
from app.providers.fallback_provider import FallbackGenerationProvider
from app.channels.http_channel_adapter import HttpChannelAdapter


def build_generation_provider(settings: Settings):
    mock_provider = MockGenerationProvider(settings)
    
    if settings.generation_provider == "ollama":
        ollama_provider = LocalLLMGenerationProvider(settings)
        if settings.enable_provider_fallback:
            return FallbackGenerationProvider(
                primary_provider=ollama_provider,
                fallback_provider=mock_provider
            )
        return ollama_provider
    
    return mock_provider

def build_chat_orchestrator(settings: Settings) -> ChatOrchestrator:
    generation_provider = build_generation_provider(settings)
    response_engine = ResponseEngine(generation_provider)
    chat_repository = LocalChatRepository()
    conversation_service = ConversationService(
        response_engine,
        chat_repository 
    )
    return ChatOrchestrator(conversation_service)


def build_local_channel(settings: Settings) -> LocalChannel:
    orchestrator = build_chat_orchestrator(settings)
    session_id = str(uuid.uuid4())
    return LocalChannel(orchestrator, settings=settings, session_id=session_id)

def build_http_channel_adapter(settings: Settings) -> HttpChannelAdapter:
    orchestrator = build_chat_orchestrator(settings)
    return HttpChannelAdapter(orchestrator)


