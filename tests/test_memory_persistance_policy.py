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


def build_test_service(tmp_path) -> tuple[ConversationService, UserMemoryRepository]:
    settings = Settings.from_env()
    settings.generation_provider = "mock"

    memory_repository = UserMemoryRepository(str(tmp_path / "user_memories.json"))
    chat_repository = LocalChatRepository(str(tmp_path / "chat_history.json"))

    context_builder = ConversationContextBuilder(
        settings=settings,
        user_memory_repository=memory_repository,
    )

    service = ConversationService(
        response_engine=ResponseEngine(MockGenerationProvider(settings)),
        chat_repository=chat_repository,
        context_builder=context_builder,
        user_memory_repository=memory_repository,
        response_safety_validator=AssistantResponseSafetyValidator(),
        memory_safety_validator=UserMemorySafetyValidator(),
    )

    return service, memory_repository


def test_identity_fact_message_persists_only_structured_memory(tmp_path) -> None:
    service, memory_repository = build_test_service(tmp_path)

    service.process_message(
        message=ChatMessage(role="user", content="me llamo Marcos"),
        session_id="session-1",
        platform="instagram",
        external_user_id="user-1",
    )

    memory = memory_repository.get_by_user("instagram", "user-1")

    assert memory is not None
    assert memory.user_profile == "me llamo Marcos"
    assert memory.stable_facts == ["me llamo Marcos"]
    assert memory.preferences == []
    assert memory.conversation_summary is None
    assert memory.working_memory_buffer == []


def test_preference_message_persists_only_preference_memory(tmp_path) -> None:
    service, memory_repository = build_test_service(tmp_path)

    service.process_message(
        message=ChatMessage(role="user", content="prefiero respuestas cortas"),
        session_id="session-1",
        platform="instagram",
        external_user_id="user-1",
    )

    memory = memory_repository.get_by_user("instagram", "user-1")

    assert memory is not None
    assert memory.user_profile == "prefiero respuestas cortas"
    assert memory.stable_facts == []
    assert memory.preferences == ["prefiero respuestas cortas"]
    assert memory.conversation_summary is None
    assert memory.working_memory_buffer == []


def test_situational_message_persists_summary_and_working_memory(tmp_path) -> None:
    service, memory_repository = build_test_service(tmp_path)

    service.process_message(
        message=ChatMessage(
            role="user",
            content="hoy estoy algo cansado, pero quiero seguir avanzando con el proyecto",
        ),
        session_id="session-1",
        platform="instagram",
        external_user_id="user-1",
    )

    memory = memory_repository.get_by_user("instagram", "user-1")

    assert memory is not None
    assert memory.user_profile is None
    assert memory.stable_facts == []
    assert memory.preferences == []
    assert memory.conversation_summary == (
        "The user is tired but still wants to keep making progress with the project."
    )
    assert memory.working_memory_buffer == [
        "The user is tired but still wants to keep making progress with the project."
    ]


def test_sensitive_message_does_not_persist_memory(tmp_path) -> None:
    service, memory_repository = build_test_service(tmp_path)

    service.process_message(
        message=ChatMessage(role="user", content="mi contraseña es 1234"),
        session_id="session-1",
        platform="instagram",
        external_user_id="user-1",
    )

    memory = memory_repository.get_by_user("instagram", "user-1")

    assert memory is None
