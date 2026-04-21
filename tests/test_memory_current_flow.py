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
from app.models.user_memory import UserMemory



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


def test_memory_record_is_created_when_user_sends_first_message(tmp_path) -> None:
    service, memory_repository = build_test_service(tmp_path)

    assert memory_repository.get_by_user("instagram", "user-1") is None

    service.process_message(
        message=ChatMessage(role="user", content="hola"),
        session_id="session-1",
        platform="instagram",
        external_user_id="user-1",
    )

    memory = memory_repository.get_by_user("instagram", "user-1")

    assert memory is not None
    assert memory.platform == "instagram"
    assert memory.external_user_id == "user-1"


def test_name_message_is_stored_as_stable_fact_and_profile(tmp_path) -> None:
    service, memory_repository = build_test_service(tmp_path)

    turn = service.process_message(
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
    assert memory.updated_at is not None
    assert turn.session_metadata["memory_updated"] is True
    assert turn.session_metadata["memory_profile_status"] == "passed"


def test_preference_message_is_stored_as_preference_and_profile(tmp_path) -> None:
    service, memory_repository = build_test_service(tmp_path)

    turn = service.process_message(
        message=ChatMessage(role="user", content="prefiero respuestas cortas"),
        session_id="session-1",
        platform="instagram",
        external_user_id="user-1",
    )

    memory = memory_repository.get_by_user("instagram", "user-1")

    assert memory is not None
    assert memory.user_profile == "prefiero respuestas cortas"
    assert memory.preferences == ["prefiero respuestas cortas"]
    assert memory.stable_facts == []
    assert memory.updated_at is not None
    assert turn.session_metadata["memory_updated"] is True
    assert turn.session_metadata["memory_profile_status"] == "passed"


def test_embedded_preference_message_is_stored_as_clean_preference(tmp_path) -> None:
    service, memory_repository = build_test_service(tmp_path)

    turn = service.process_message(
        message=ChatMessage(
            role="user",
            content="te aviso que prefiero respuestas cortas y sin rodeos, si no me pierdo",
        ),
        session_id="session-1",
        platform="instagram",
        external_user_id="user-1",
    )

    memory = memory_repository.get_by_user("instagram", "user-1")

    assert memory is not None
    assert memory.user_profile == "prefiero respuestas cortas y sin rodeos"
    assert memory.preferences == ["prefiero respuestas cortas y sin rodeos"]
    assert turn.session_metadata["memory_updated"] is True
    assert turn.session_metadata["memory_profile_status"] == "passed"


def test_memory_question_does_not_create_false_preference(tmp_path) -> None:
    service, memory_repository = build_test_service(tmp_path)

    service.process_message(
        message=ChatMessage(role="user", content="prefiero respuestas cortas y sin rodeos"),
        session_id="session-1",
        platform="instagram",
        external_user_id="user-1",
    )

    service.process_message(
        message=ChatMessage(role="user", content="y qué te dije sobre cómo me gusta que me respondan?"),
        session_id="session-1",
        platform="instagram",
        external_user_id="user-1",
    )

    memory = memory_repository.get_by_user("instagram", "user-1")

    assert memory is not None
    assert memory.preferences == ["prefiero respuestas cortas y sin rodeos"]
    assert "me gusta que me respondan" not in memory.preferences


def test_sensitive_message_does_not_update_user_memory(tmp_path) -> None:
    service, memory_repository = build_test_service(tmp_path)

    turn = service.process_message(
        message=ChatMessage(role="user", content="mi contraseña es 1234"),
        session_id="session-1",
        platform="instagram",
        external_user_id="user-1",
    )

    memory = memory_repository.get_by_user("instagram", "user-1")

    assert memory is None
    assert turn.session_metadata["memory_updated"] is False
    assert turn.session_metadata["memory_profile_status"] == "empty"
    assert turn.session_metadata["memory_profile_detail"] == "No candidate memory to validate."
    assert turn.session_metadata["memory_summary_status"] == "blocked"


def test_normal_message_updates_conversation_summary_only(tmp_path) -> None:
    service, memory_repository = build_test_service(tmp_path)

    turn = service.process_message(
        message=ChatMessage(role="user", content="hoy estoy algo cansado, pero quiero seguir avanzando con el proyecto"),
        session_id="session-1",
        platform="instagram",
        external_user_id="user-1",
    )

    memory = memory_repository.get_by_user("instagram", "user-1")

    assert memory is not None
    assert memory.user_profile is None
    assert memory.stable_facts == []
    assert memory.preferences == []
    assert memory.conversation_summary is not None
    assert "The user is tired but still wants to keep making progress with the project." in memory.conversation_summary
    assert "Assistant replied:" not in memory.conversation_summary
    assert memory.updated_at is not None
    assert turn.session_metadata["memory_updated"] is True
    assert turn.session_metadata["memory_profile_status"] == "empty"
    assert turn.session_metadata["memory_profile_detail"] == "No candidate memory to validate."
    assert turn.session_metadata["memory_summary_status"] == "passed"


def test_memory_is_separated_by_platform_and_external_user_id(tmp_path) -> None:
    service, memory_repository = build_test_service(tmp_path)

    service.process_message(
        message=ChatMessage(role="user", content="me llamo Marcos"),
        session_id="session-1",
        platform="instagram",
        external_user_id="user-1",
    )

    service.process_message(
        message=ChatMessage(role="user", content="me llamo Ana"),
        session_id="session-2",
        platform="instagram",
        external_user_id="user-2",
    )

    user_1_memory = memory_repository.get_by_user("instagram", "user-1")
    user_2_memory = memory_repository.get_by_user("instagram", "user-2")

    assert user_1_memory is not None
    assert user_2_memory is not None
    assert user_1_memory.stable_facts == ["me llamo Marcos"]
    assert user_2_memory.stable_facts == ["me llamo Ana"]



def test_memory_loaded_is_true_when_structured_memory_exists_without_profile_or_summary(tmp_path) -> None:
    service, memory_repository = build_test_service(tmp_path)

    memory_repository.save(
        UserMemory(
            platform="instagram",
            external_user_id="user-1",
            stable_facts=["me llamo Marcos"],
        )
    )

    turn = service.process_message(
        message=ChatMessage(role="user", content="te acuerdas de mi nombre?"),
        session_id="session-1",
        platform="instagram",
        external_user_id="user-1",
    )

    assert turn.session_metadata["memory_loaded"] is True


def test_building_context_does_not_create_empty_memory(tmp_path) -> None:
    service, memory_repository = build_test_service(tmp_path)

    assert memory_repository.get_by_user("instagram", "user-1") is None

    service.context_builder.build(
        platform="instagram",
        external_user_id="user-1",
        message=ChatMessage(role="user", content="hola"),
        recent_history=[],
    )

    assert memory_repository.get_by_user("instagram", "user-1") is None


