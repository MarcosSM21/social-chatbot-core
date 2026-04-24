from app.models.chat import ChatMessage
from app.core.settings import Settings
from app.engine.response_engine import ResponseEngine
from app.providers.mock_provider import MockGenerationProvider
from app.services.assistant_response_safety_validator import AssistantResponseSafetyValidator
from app.services.conversation_context_builder import ConversationContextBuilder
from app.services.conversation_service import ConversationService
from app.services.user_memory_safety_validator import UserMemorySafetyValidator
from app.storage.local_chat_repository import LocalChatRepository
from app.storage.user_memory_repository import UserMemoryRepository


def build_service(tmp_path) -> tuple[ConversationService, UserMemoryRepository]:
    settings = Settings.from_env()
    settings.generation_provider = "mock"

    user_memory_repository = UserMemoryRepository(str(tmp_path / "user_memories.json"))
    service = ConversationService(
        response_engine=ResponseEngine(MockGenerationProvider(settings)),
        chat_repository=LocalChatRepository(str(tmp_path / "chat_history.json")),
        context_builder=ConversationContextBuilder(settings, user_memory_repository),
        user_memory_repository=user_memory_repository,
        response_safety_validator=AssistantResponseSafetyValidator(),
        memory_safety_validator=UserMemorySafetyValidator(),
    )
    return service, user_memory_repository


def test_user_memory_tracks_last_seen_at(tmp_path) -> None:
    service, user_memory_repository = build_service(tmp_path)

    service.process_message(
        message=ChatMessage(role="user", content="hola"),
        session_id="session-1",
        platform="instagram",
        external_user_id="user-1",
    )

    memory = user_memory_repository.get_by_user("instagram", "user-1")

    assert memory is not None
    assert memory.last_seen_at is not None
    assert memory.last_known_username is None
