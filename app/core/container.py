import uuid 

from app.channels.local_channel import LocalChannel
from app.core.settings import Settings
from app.engine.response_engine import ResponseEngine
from app.orchestrator.chat_orquestrator import ChatOrchestrator
from app.services.conversation_service import ConversationService
from app.storage.local_chat_repository import LocalChatRepository
from app.providers.mock_provider import MockGenerationProvider

def build_chat_orchestrator(settings: Settings) -> ChatOrchestrator:
    generation_provider = MockGenerationProvider(settings)
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
    return LocalChannel(
        orchestrator, 
        settings=settings, 
        session_id=session_id
        )


