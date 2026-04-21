import json

from app.core.settings import Settings
from app.models.chat import ChatMessage
from app.services.conversation_context_builder import ConversationContextBuilder
from app.storage.character_repository import CharacterRepository
from app.storage.user_memory_repository import UserMemoryRepository


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
