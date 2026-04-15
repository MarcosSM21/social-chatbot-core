from app.core.settings import Settings
from app.engine.response_engine import ResponseEngine
from app.models.chat import ChatMessage
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


def test_conversation_service_updates_normal_memory(tmp_path) -> None:
    service, user_memory_repository = build_service(tmp_path)

    turn = service.process_message(
        message=ChatMessage(role="user", content="me llamo Marcos"),
        session_id="session-1",
        platform="instagram",
        external_user_id="user-1",
    )
    memory = user_memory_repository.get_or_create("instagram", "user-1")

    assert memory.user_profile == "me llamo Marcos"
    assert memory.conversation_summary is not None
    assert turn.session_metadata["memory_updated"] is True
    assert turn.session_metadata["memory_profile_status"] == "passed"
    assert turn.session_metadata["memory_summary_status"] == "passed"
    assert turn.session_metadata["style_preset"]
    assert turn.session_metadata["safety_policy_active"] is True
    assert turn.session_metadata["safety_validation_status"] == "passed"
    assert turn.session_metadata["character_id"]
    assert turn.session_metadata["character_name"]
    assert turn.session_metadata["character_snapshot"]



def test_conversation_service_does_not_store_sensitive_memory(tmp_path) -> None:
    service, user_memory_repository = build_service(tmp_path)

    turn = service.process_message(
        message=ChatMessage(role="user", content="mi contraseña es 1234"),
        session_id="session-1",
        platform="instagram",
        external_user_id="user-1",
    )
    memory = user_memory_repository.get_or_create("instagram", "user-1")

    assert memory.user_profile is None
    assert memory.conversation_summary is None
    assert turn.session_metadata["memory_updated"] is False
    assert turn.session_metadata["memory_summary_status"] == "blocked"
    assert turn.session_metadata["memory_summary_matched_rule"] == "password_es"
