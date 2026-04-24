import json

from app.core.settings import Settings
from app.models.chat import ChatMessage
from app.services.conversation_context_builder import ConversationContextBuilder
from app.storage.character_repository import CharacterRepository
from app.storage.user_memory_repository import UserMemoryRepository
from app.models.user_memory import UserMemory



def test_context_builder_loads_character_through_repository(tmp_path) -> None:
    characters_dir = tmp_path / "characters"
    characters_dir.mkdir()

    character_file = characters_dir / "test_character.json"
    character_file.write_text(
        json.dumps(
            {
                "character_id": "test_character",
                "display_name": "Test Character",
                "core_identity": "A test character.",
                "backstory": "Created only for this test.",
                "speaking_style": ["Speak in a very testable way."],
            }
        ),
        encoding="utf-8",
    )

    user_memory_file = tmp_path / "user_memories.json"

    settings = Settings.from_env()
    settings.character_file = str(character_file)

    user_memory_repository = UserMemoryRepository(str(user_memory_file))
    character_repository = CharacterRepository(str(characters_dir))

    builder = ConversationContextBuilder(
        settings=settings,
        user_memory_repository=user_memory_repository,
        character_repository=character_repository,
    )

    context = builder.build(
        platform="instagram",
        external_user_id="user-1",
        message=ChatMessage(role="user", content="hola"),
        recent_history=[],
    )

    assert context.character.character_id == "test_character"
    assert context.character.display_name == "Test Character"
    assert "Name: Test Character." in context.character_instructions


def test_context_builder_selects_name_memory_when_user_asks_about_name(tmp_path) -> None:
    user_memory_file = tmp_path / "user_memories.json"

    settings = Settings.from_env()
    user_memory_repository = UserMemoryRepository(str(user_memory_file))
    user_memory_repository.save(
        UserMemory(
            platform="instagram",
            external_user_id="user-1",
            stable_facts=["me llamo Marcos"],
            preferences=["prefiero respuestas cortas"],
        )
    )

    builder = ConversationContextBuilder(
        settings=settings,
        user_memory_repository=user_memory_repository,
    )

    context = builder.build(
        platform="instagram",
        external_user_id="user-1",
        message=ChatMessage(role="user", content="te acuerdas de mi nombre?"),
        recent_history=[],
    )

    assert context.retrieved_memory is not None
    assert "Stable fact: me llamo Marcos" in context.retrieved_memory
    assert context.retrieval_strategy == "rule_based_memory_selector_v1"


def test_context_builder_falls_back_to_summary_when_no_specific_memory_matches(tmp_path) -> None:
    user_memory_file = tmp_path / "user_memories.json"

    settings = Settings.from_env()
    user_memory_repository = UserMemoryRepository(str(user_memory_file))
    user_memory_repository.save(
        UserMemory(
            platform="instagram",
            external_user_id="user-1",
            conversation_summary="The user is tired but wants to keep making progress with the project.",
        )
    )

    builder = ConversationContextBuilder(
        settings=settings,
        user_memory_repository=user_memory_repository,
    )

    context = builder.build(
        platform="instagram",
        external_user_id="user-1",
        message=ChatMessage(role="user", content="qué harías tú ahora?"),
        recent_history=[],
    )

    assert context.retrieved_memory is not None
    assert context.retrieved_memory == [
        "Summary: The user is tired but wants to keep making progress with the project."
    ]
