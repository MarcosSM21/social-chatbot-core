from pathlib import Path

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


def build_service(tmp_path, character_file: str | None = None) -> tuple[ConversationService, UserMemoryRepository]:
    settings = Settings.from_env()
    settings.generation_provider = "mock"
    if character_file is not None:
        settings.character_file = character_file

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
    assert memory.stable_facts == ["me llamo Marcos"]
    assert memory.conversation_summary is None
    assert memory.working_memory_buffer == []
    assert turn.session_metadata["memory_updated"] is True
    assert turn.session_metadata["memory_profile_status"] == "passed"
    assert turn.session_metadata["memory_summary_status"] == "passed"
    assert turn.session_metadata["safety_policy_active"] is True
    assert turn.session_metadata["safety_validation_status"] == "passed"
    assert turn.session_metadata["character_id"]
    assert turn.session_metadata["character_name"]
    assert turn.session_metadata["character_snapshot"]
    assert "style_preset" not in turn.session_metadata



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
    assert turn.session_metadata["memory_summary_matched_rule"] is not None


def test_conversation_service_stores_preferences_separately(tmp_path) -> None:
    service, user_memory_repository = build_service(tmp_path)

    service.process_message(
        message=ChatMessage(role="user", content="prefiero respuestas cortas"),
        session_id="session-1",
        platform="instagram",
        external_user_id="user-1",
    )
    memory = user_memory_repository.get_or_create("instagram", "user-1")

    assert memory.preferences == ["prefiero respuestas cortas"]
    assert memory.stable_facts == []
    assert memory.conversation_summary is None
    assert memory.working_memory_buffer == []



def test_conversation_service_does_not_duplicate_structured_memory(tmp_path) -> None:
    service, user_memory_repository = build_service(tmp_path)

    for _ in range(2):
        service.process_message(
            message=ChatMessage(role="user", content="me llamo Marcos"),
            session_id="session-1",
            platform="instagram",
            external_user_id="user-1",
        )

    memory = user_memory_repository.get_or_create("instagram", "user-1")

    assert memory.stable_facts == ["me llamo Marcos"]


def test_conversation_service_loads_structured_memory_on_followup(tmp_path) -> None:
    service, user_memory_repository = build_service(tmp_path)

    service.process_message(
        message=ChatMessage(role="user", content="me llamo Marcos"),
        session_id="session-1",
        platform="instagram",
        external_user_id="user-1",
    )

    turn = service.process_message(
        message=ChatMessage(role="user", content="te acuerdas de mi nombre?"),
        session_id="session-1",
        platform="instagram",
        external_user_id="user-1",
    )

    memory = user_memory_repository.get_or_create("instagram", "user-1")

    assert memory.stable_facts == ["me llamo Marcos"]
    assert turn.session_metadata["memory_loaded"] is True


def test_working_memory_buffer_drops_oldest_novel_item_when_full(tmp_path) -> None:
    service, _ = build_service(tmp_path)

    updated = service._update_working_memory_buffer(
        items=[
            "The user is tired and wants to keep making progress.",
            "The user is worried about the architecture.",
            "The user wants concrete next steps.",
            "The user is exploring memory retrieval.",
            "The user is thinking about latency tradeoffs.",
        ],
        candidate="The user also wants an easy way to inspect SQLite memory.",
        limit=5,
    )

    assert updated == [
        "The user is worried about the architecture.",
        "The user wants concrete next steps.",
        "The user is exploring memory retrieval.",
        "The user is thinking about latency tradeoffs.",
        "The user also wants an easy way to inspect SQLite memory.",
    ]


def test_working_memory_buffer_rejects_low_novelty_candidate_when_full(tmp_path) -> None:
    service, _ = build_service(tmp_path)

    items = [
        "The user is tired and wants to keep making progress.",
        "The user is worried about the architecture.",
        "The user wants concrete next steps.",
        "The user is exploring memory retrieval.",
        "The user is thinking about latency tradeoffs.",
    ]

    updated = service._update_working_memory_buffer(
        items=items,
        candidate="The user wants concrete next steps.",
        limit=5,
    )

    assert updated == items


def test_working_memory_buffer_consolidates_overlapping_fragment_with_more_context(tmp_path) -> None:
    service, _ = build_service(tmp_path)

    updated = service._update_working_memory_buffer(
        items=[
            "The user is worried about the memory architecture.",
        ],
        candidate="The user is worried about the memory architecture and retrieval quality.",
        limit=5,
    )

    assert updated == [
        "The user is worried about the memory architecture and retrieval quality."
    ]


def test_working_memory_buffer_keeps_existing_fragment_when_overlap_adds_no_real_value(tmp_path) -> None:
    service, _ = build_service(tmp_path)

    items = [
        "The user is worried about the memory architecture and retrieval quality.",
    ]

    updated = service._update_working_memory_buffer(
        items=items,
        candidate="The user is worried about the memory architecture.",
        limit=5,
    )

    assert updated == items


def test_working_memory_buffer_rejects_reformulation_of_existing_buffer_theme(tmp_path) -> None:
    service, _ = build_service(tmp_path)

    items = [
        "The user is worried about the memory architecture.",
        "The user is thinking about retrieval quality.",
        "The user wants to organize the system clearly.",
    ]

    updated = service._update_working_memory_buffer(
        items=items,
        candidate="The user is worried about organizing the memory architecture and retrieval clearly.",
        limit=5,
    )

    assert updated == items



def test_working_memory_buffer_allows_distinct_candidate_when_not_reformulation(tmp_path) -> None:
    service, _ = build_service(tmp_path)

    items = [
        "The user is worried about the memory architecture.",
        "The user is thinking about retrieval quality.",
        "The user wants to organize the system clearly.",
    ]

    updated = service._update_working_memory_buffer(
        items=items,
        candidate="The user wants an easy visual way to inspect SQLite memory.",
        limit=5,
    )

    assert updated == [
        "The user is worried about the memory architecture.",
        "The user is thinking about retrieval quality.",
        "The user wants to organize the system clearly.",
        "The user wants an easy visual way to inspect SQLite memory.",
    ]


def test_instagram_redirect_policy_replaces_response_for_sexual_trigger(tmp_path) -> None:
    service, _ = build_service(
        tmp_path,
        character_file="characters/laia_instagram_sirena.json",
    )

    turn = service.process_message(
        message=ChatMessage(role="user", content="me pones mucho"),
        session_id="session-1",
        platform="api",
        external_user_id="user-1",
    )

    assert "https://mock-laia.com" in turn.assistant_message.content
    assert turn.session_metadata["instagram_redirect_policy_applied"] is True
    assert turn.session_metadata["instagram_redirect_trigger"] == "sexual_private_direct"


def test_instagram_redirect_policy_replaces_response_for_turn_limit_trigger(tmp_path) -> None:
    service, _ = build_service(
        tmp_path,
        character_file="characters/laia_instagram_sirena.json",
    )

    service.process_message(
        message=ChatMessage(role="user", content="hola"),
        session_id="session-1",
        platform="api",
        external_user_id="user-1",
    )
    service.process_message(
        message=ChatMessage(role="user", content="que tal"),
        session_id="session-1",
        platform="api",
        external_user_id="user-1",
    )
    turn = service.process_message(
        message=ChatMessage(role="user", content="bueno"),
        session_id="session-1",
        platform="api",
        external_user_id="user-1",
    )

    assert "https://mock-laia.com" in turn.assistant_message.content
    assert turn.session_metadata["instagram_redirect_policy_applied"] is True
    assert turn.session_metadata["instagram_redirect_trigger"] == "turn_limit"


def test_instagram_redirect_policy_replaces_response_for_repetitive_low_value_trigger(tmp_path) -> None:
    service, _ = build_service(
        tmp_path,
        character_file="characters/laia_instagram_sirena.json",
    )

    service.process_message(
        message=ChatMessage(role="user", content="hola"),
        session_id="session-1",
        platform="api",
        external_user_id="user-1",
    )
    turn = service.process_message(
        message=ChatMessage(role="user", content="y que mas"),
        session_id="session-1",
        platform="api",
        external_user_id="user-1",
    )

    assert "https://mock-laia.com" in turn.assistant_message.content
    assert turn.session_metadata["instagram_redirect_policy_applied"] is True
    assert turn.session_metadata["instagram_redirect_trigger"] == "repetitive_low_value"

