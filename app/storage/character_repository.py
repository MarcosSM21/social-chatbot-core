import json
from dataclasses import dataclass
from pathlib import Path

from app.models.conversation_character import ConversationCharacter


@dataclass
class CharacterSummary:
    character_id: str
    display_name: str
    file_path: str

@dataclass
class CharacterLoadResult:
    character : ConversationCharacter
    file_path: str
    status: str
    detail: str | None = None


class CharacterRepository:
    def __init__(self, character_dir: str = "characters") -> None:
        self.character_dir = Path(character_dir)

    
    def list_characters(self) -> list[CharacterSummary]:
        characters: list[CharacterSummary] = []

        for file_path in sorted(self.character_dir.glob("*.json")):
            result = self.load_by_file_path_with_status(str(file_path))

            if result.status != "loaded":
                continue

            characters.append(
                CharacterSummary(
                    character_id=result.character.character_id,
                    display_name=result.character.display_name,
                    file_path=str(file_path)
                )
            )

        return characters

    

    def load_by_file_path(self, file_path: str) -> ConversationCharacter:
        return self.load_by_file_path_with_status(file_path).character
        

    def load_by_file_path_with_status(self, file_path: str) -> CharacterLoadResult:
        path = Path(file_path)

        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            character = ConversationCharacter.from_dict(data)

            return CharacterLoadResult(
                character=character,
                file_path=str(path),
                status="loaded",
                detail=None,
            )

        except FileNotFoundError:
            return CharacterLoadResult(
                character=ConversationCharacter.default(),
                file_path=str(path),
                status="file_not_found",
                detail="Character file was not found.",
            )

        except json.JSONDecodeError:
            return CharacterLoadResult(
                character=ConversationCharacter.default(),
                file_path=str(path),
                status="invalid_json",
                detail="Character file contains invalid JSON.",
            )

        except KeyError as exc:
            missing_field = str(exc.args[0])

            return CharacterLoadResult(
                character=ConversationCharacter.default(),
                file_path=str(path),
                status="missing_required_field",
                detail=f"Missing required character field: {missing_field}",
            )

        except TypeError:
            return CharacterLoadResult(
                character=ConversationCharacter.default(),
                file_path=str(path),
                status="invalid_character_data",
                detail="Character file contains invalid character data.",
            )
    
        
    def load_by_id(self, character_id: str) -> ConversationCharacter:
        for summary in self.list_characters():
            if summary.character_id == character_id:
                return self.load_by_file_path(summary.file_path)
            
        return ConversationCharacter.default()
    
