import json
import uuid
from pathlib import Path

from app.models.conversation_mapping import ConversationMapping

class ConversationMappingRepository:
    def __init__(self, file_path: str = "data/conversation_mappings.json") -> None:
        self.file_path = Path(file_path)
        self._ensure_storage_exists()

    def _ensure_storage_exists(self) -> None:
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.file_path.exists():
            self.file_path.write_text("[]", encoding="utf-8")

    def load_mappings(self) -> list[ConversationMapping]:
        raw_data = json.loads(self.file_path.read_text(encoding="utf-8"))
        return [ConversationMapping.from_dict(item) for item in raw_data]
    
    def save_mapping(self, mappings: list[ConversationMapping]) -> None:
        serialized = [mapping.to_dict() for mapping in mappings]
        self.file_path.write_text(json.dumps(serialized, indent=2), encoding="utf-8")

    def get_or_create_session_id(self, platform: str, external_conversation_id: str, external_user_id: str) -> str:
        mappings = self.load_mappings()
        for mapping in mappings:
            if (mapping.platform == platform and 
                mapping.external_conversation_id == external_conversation_id and 
                mapping.external_user_id == external_user_id):
                return mapping.internal_session_id
        
        new_mapping = ConversationMapping(
            platform=platform,
            external_conversation_id=external_conversation_id,
            external_user_id=external_user_id,
            internal_session_id=str(uuid.uuid4())
        )
        mappings.append(new_mapping)
        self.save_mapping(mappings)
        return new_mapping.internal_session_id