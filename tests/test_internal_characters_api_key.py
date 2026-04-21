from app.api import main as api_main
from app.models.conversation_character import ConversationCharacter
from app.storage.character_repository import CharacterLoadResult, CharacterSummary



class FakeCharacterRepository:
    def list_characters(self):
        return [
            CharacterSummary(
                character_id="leo_realistic_friend",
                display_name="Leo",
                file_path="characters/leo_realistic_friend.json",
            ),
            CharacterSummary(
                character_id="laia_ambitious_model",
                display_name="Laia",
                file_path="characters/laia_ambitious_model.json",
            ),
        ]

    def load_by_file_path(self, file_path: str):
        class FakeCharacter:
            character_id = "leo_realistic_friend"
            display_name = "Leo"

        return FakeCharacter()
    
    def load_by_file_path_with_status(self, file_path: str):
        return CharacterLoadResult(
            character=self.load_by_file_path(file_path),
            file_path=file_path,
            status="loaded",
            detail=None,
        )



class FakeDefaultCharacterRepository:
    def load_by_file_path_with_status(self, file_path: str):
        return CharacterLoadResult(
            character=ConversationCharacter.default(),
            file_path=file_path,
            status="file_not_found",
            detail="Character file was not found.",
        )



def test_list_internal_characters(monkeypatch) -> None:
    monkeypatch.setattr(
        api_main,
        "CharacterRepository",
        FakeCharacterRepository,
    )

    response = api_main.list_internal_characters(_=None)

    assert response.count == 2
    assert response.characters[0].character_id == "leo_realistic_friend"
    assert response.characters[0].display_name == "Leo"
    assert response.characters[1].character_id == "laia_ambitious_model"


def test_get_active_internal_character(monkeypatch) -> None:
    monkeypatch.setattr(
        api_main,
        "CharacterRepository",
        FakeCharacterRepository,
    )
    monkeypatch.setattr(
        api_main.settings,
        "character_file",
        "characters/leo_realistic_friend.json",
    )

    response = api_main.get_active_internal_character(_=None)

    assert response.character_id == "leo_realistic_friend"
    assert response.display_name == "Leo"
    assert response.file_path == "characters/leo_realistic_friend.json"
    assert response.is_default is False
    assert response.load_status == "loaded"
    assert response.load_detail is None



def test_get_active_internal_character_marks_default_fallback(monkeypatch) -> None:
    monkeypatch.setattr(
        api_main,
        "CharacterRepository",
        FakeDefaultCharacterRepository,
    )
    monkeypatch.setattr(
        api_main.settings,
        "character_file",
        "characters/missing.json",
    )

    response = api_main.get_active_internal_character(_=None)

    assert response.character_id == "default"
    assert response.display_name == "SocialBot"
    assert response.file_path is None
    assert response.is_default is True
    assert response.load_status == "file_not_found"
    assert response.load_detail == "Character file was not found."

