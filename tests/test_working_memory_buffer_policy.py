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


def test_working_memory_buffer_keeps_situational_context_not_structured_fact(tmp_path) -> None:
    service, memory_repository = build_service(tmp_path)

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
    assert memory.stable_facts == []
    assert memory.preferences == []
    assert len(memory.working_memory_buffer) == 1


def test_working_memory_buffer_does_not_store_identity_fact(tmp_path) -> None:
    service, memory_repository = build_service(tmp_path)

    service.process_message(
        message=ChatMessage(role="user", content="me llamo Marcos"),
        session_id="session-1",
        platform="instagram",
        external_user_id="user-1",
    )

    memory = memory_repository.get_by_user("instagram", "user-1")

    assert memory is not None
    assert memory.stable_facts == ["me llamo Marcos"]
    assert memory.working_memory_buffer == []


def test_working_memory_buffer_replaces_weaker_overlapping_fragment(tmp_path) -> None:
    service, _ = build_service(tmp_path)

    updated = service._update_working_memory_buffer(
        items=["The user is worried about the memory architecture."],
        candidate="The user is worried about the memory architecture and retrieval quality.",
        limit=5,
    )

    assert updated == [
        "The user is worried about the memory architecture and retrieval quality."
    ]


def test_working_memory_buffer_rejects_exact_duplicate(tmp_path) -> None:
    service, _ = build_service(tmp_path)

    items = [
        "The user wants concrete next steps.",
    ]

    updated = service._update_working_memory_buffer(
        items=items,
        candidate="The user wants concrete next steps.",
        limit=5,
    )

    assert updated == items


def test_working_memory_buffer_rejects_low_novelty_when_full(tmp_path) -> None:
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


def test_working_memory_buffer_rejects_multi_item_reformulation(tmp_path) -> None:
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


def test_working_memory_buffer_keeps_recent_novel_fragment_when_full(tmp_path) -> None:
    service, _ = build_service(tmp_path)

    updated = service._update_working_memory_buffer(
        items=[
            "The user is tired and wants to keep making progress.",
            "The user is worried about the architecture.",
            "The user wants concrete next steps.",
            "The user is exploring memory retrieval.",
            "The user is thinking about latency tradeoffs.",
        ],
        candidate="The user wants an easy visual way to inspect SQLite memory.",
        limit=5,
    )

    assert updated == [
        "The user is worried about the architecture.",
        "The user wants concrete next steps.",
        "The user is exploring memory retrieval.",
        "The user is thinking about latency tradeoffs.",
        "The user wants an easy visual way to inspect SQLite memory.",
    ]


def test_working_memory_buffer_never_exceeds_limit_in_real_flow(tmp_path) -> None:
    service, memory_repository = build_service(tmp_path)

    messages = [
        "hoy estoy algo cansado, pero quiero seguir avanzando con el proyecto",
        "también me preocupa bastante cómo organizar la memoria del sistema",
        "quiero el siguiente paso concreto del proyecto",
        "estoy pensando mucho en retrieval y compactación",
        "también me preocupa la latencia si metemos más LLMs",
        "además quiero una forma sencilla de inspeccionar sqlite",
        "sigo dándole vueltas a cómo ordenar toda esta arquitectura",
    ]

    for message in messages:
        service.process_message(
            message=ChatMessage(role="user", content=message),
            session_id="session-1",
            platform="instagram",
            external_user_id="user-1",
        )

    memory = memory_repository.get_by_user("instagram", "user-1")

    assert memory is not None
    assert len(memory.working_memory_buffer) <= 5
