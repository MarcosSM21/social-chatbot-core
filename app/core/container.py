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
from app.storage.conversation_mapping_repository import ConversationMappingRepository
from app.channels.platform_payload_parser import PlatformPayloadParser
from app.services.platform_inbound_service import PlatformInboundService
from app.outbound.mock_sender import MockOutboundSender
from app.storage.external_trace_repository import ExternalTraceRepository
from app.services.conversation_context_builder import ConversationContextBuilder
from app.storage.user_memory_repository import UserMemoryRepository
from app.services.assistant_response_safety_validator import AssistantResponseSafetyValidator
from app.services.user_memory_safety_validator import UserMemorySafetyValidator


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
    user_memory_repository = UserMemoryRepository()
    context_builder = ConversationContextBuilder(settings, user_memory_repository=user_memory_repository)
    response_safety_validator = AssistantResponseSafetyValidator()
    memory_safety_validator = UserMemorySafetyValidator()

    conversation_service = ConversationService(
        response_engine,
        chat_repository,
        context_builder,
        user_memory_repository,
        response_safety_validator,
        memory_safety_validator,
    )
    return ChatOrchestrator(conversation_service)


def build_local_channel(settings: Settings) -> LocalChannel:
    orchestrator = build_chat_orchestrator(settings)
    session_id = str(uuid.uuid4())
    return LocalChannel(orchestrator, settings=settings, session_id=session_id)

def build_http_channel_adapter(settings: Settings) -> HttpChannelAdapter:
    orchestrator = build_chat_orchestrator(settings)
    mapping_repository = ConversationMappingRepository()
    return HttpChannelAdapter(orchestrator, mapping_repository)


def build_platform_inbound_service(settings: Settings) -> PlatformInboundService:
    http_channel_adapter = build_http_channel_adapter(settings)
    payload_parser = PlatformPayloadParser()
    outbound_sender = MockOutboundSender()
    trace_repository = ExternalTraceRepository()
    return PlatformInboundService(
        payload_parser = payload_parser,
        http_channel_adapter= http_channel_adapter,
        outbound_sender=outbound_sender,
        trace_repository=trace_repository
    )

