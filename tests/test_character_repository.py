import json

from app.models.conversation_character import ConversationCharacter
from app.storage.character_repository import CharacterRepository


def test_list_characters_returns_available_character_summaries() -> None:
    repository = CharacterRepository("characters")

    characters = repository.list_characters()
    character_ids = [character.character_id for character in characters]

    assert "leo_realistic_friend" in character_ids
    assert "laia_ambitious_model" in character_ids


def test_load_by_file_path_returns_character() -> None:
    repository = CharacterRepository("characters")

    character = repository.load_by_file_path("characters/laia_ambitious_model.json")

    assert character.character_id == "laia_ambitious_model"
    assert character.display_name == "Laia"


def test_load_by_id_returns_matching_character() -> None:
    repository = CharacterRepository("characters")

    character = repository.load_by_id("leo_realistic_friend")

    assert character.character_id == "leo_realistic_friend"
    assert character.display_name == "Leo"


def test_load_by_missing_file_returns_default_character() -> None:
    repository = CharacterRepository("characters")

    character = repository.load_by_file_path("characters/does_not_exist.json")

    assert character.character_id == ConversationCharacter.default().character_id
    assert character.display_name == ConversationCharacter.default().display_name


def test_load_by_unknown_id_returns_default_character() -> None:
    repository = CharacterRepository("characters")

    character = repository.load_by_id("unknown-character")

    assert character.character_id == ConversationCharacter.default().character_id


def test_invalid_character_json_is_ignored_when_listing(tmp_path) -> None:
    characters_dir = tmp_path / "characters"
    characters_dir.mkdir()

    invalid_character_file = characters_dir / "broken.json"
    invalid_character_file.write_text("{not valid json", encoding="utf-8")

    repository = CharacterRepository(str(characters_dir))

    assert repository.list_characters() == []


def test_valid_character_json_can_be_loaded_from_custom_directory(tmp_path) -> None:
    characters_dir = tmp_path / "characters"
    characters_dir.mkdir()

    character_file = characters_dir / "test_character.json"
    character_file.write_text(
        json.dumps(
            {
                "character_id": "test_character",
                "display_name": "Test Character",
                "core_identity": "A test character.",
                "backstory": "Created only for tests.",
            }
        ),
        encoding="utf-8",
    )

    repository = CharacterRepository(str(characters_dir))

    characters = repository.list_characters()

    assert len(characters) == 1
    assert characters[0].character_id == "test_character"
    assert characters[0].display_name == "Test Character"
    assert characters[0].file_path.endswith("test_character.json")

def test_load_by_file_path_with_status_reports_loaded_character() -> None:
    repository = CharacterRepository("characters")

    result = repository.load_by_file_path_with_status("characters/laia_ambitious_model.json")

    assert result.status == "loaded"
    assert result.detail is None
    assert result.character.character_id == "laia_ambitious_model"


def test_load_by_file_path_with_status_reports_missing_file() -> None:
    repository = CharacterRepository("characters")

    result = repository.load_by_file_path_with_status("characters/missing.json")

    assert result.status == "file_not_found"
    assert result.detail == "Character file was not found."
    assert result.character.character_id == "default"


def test_load_by_file_path_with_status_reports_invalid_json(tmp_path) -> None:
    character_file = tmp_path / "broken.json"
    character_file.write_text("{not valid json", encoding="utf-8")

    repository = CharacterRepository(str(tmp_path))

    result = repository.load_by_file_path_with_status(str(character_file))

    assert result.status == "invalid_json"
    assert result.detail == "Character file contains invalid JSON."
    assert result.character.character_id == "default"


def test_load_by_file_path_with_status_reports_missing_required_field(tmp_path) -> None:
    character_file = tmp_path / "missing_field.json"
    character_file.write_text(
        json.dumps(
            {
                "character_id": "broken_character",
                "display_name": "Broken Character",
            }
        ),
        encoding="utf-8",
    )

    repository = CharacterRepository(str(tmp_path))

    result = repository.load_by_file_path_with_status(str(character_file))

    assert result.status == "missing_required_field"
    assert "core_identity" in result.detail
    assert result.character.character_id == "default"
