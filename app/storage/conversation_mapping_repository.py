import uuid
from pathlib import Path

from app.models.conversation_mapping import ConversationMapping
from app.storage.atomic_json_file import atomic_write_json_file, read_json_file
from app.storage.file_lock_registry import get_file_lock


class ConversationMappingRepository:
    def __init__(self, file_path: str = "data/conversation_mappings.json") -> None:
        self.file_path = Path(file_path)
        self._file_lock = get_file_lock(self.file_path)
        self._ensure_storage_exists()

    def _ensure_storage_exists(self) -> None:
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.file_path.exists():
            atomic_write_json_file(self.file_path, [])

    def _load_mappings_unlocked(self) -> list[ConversationMapping]:
        raw_data = read_json_file(self.file_path, [])
        return [ConversationMapping.from_dict(item) for item in raw_data]

    def _write_mappings_unlocked(self, mappings: list[ConversationMapping]) -> None:
        serialized = [mapping.to_dict() for mapping in mappings]
        atomic_write_json_file(self.file_path, serialized)

    def load_mappings(self) -> list[ConversationMapping]:
        with self._file_lock:
            return self._load_mappings_unlocked()

    def save_mapping(self, mappings: list[ConversationMapping]) -> None:
        with self._file_lock:
            self._write_mappings_unlocked(mappings)

    def get_or_create_session_id(
        self,
        platform: str,
        external_conversation_id: str,
        external_user_id: str,
    ) -> str:
        with self._file_lock:
            mappings = self._load_mappings_unlocked()

            for mapping in mappings:
                if (
                    mapping.platform == platform
                    and mapping.external_conversation_id == external_conversation_id
                    and mapping.external_user_id == external_user_id
                ):
                    return mapping.internal_session_id

            new_mapping = ConversationMapping(
                platform=platform,
                external_conversation_id=external_conversation_id,
                external_user_id=external_user_id,
                internal_session_id=str(uuid.uuid4()),
            )
            mappings.append(new_mapping)
            self._write_mappings_unlocked(mappings)
            return new_mapping.internal_session_id

    def list_by_user(self, platform: str, external_user_id: str) -> list[ConversationMapping]:
        with self._file_lock:
            mappings = self._load_mappings_unlocked()
            return [
                mapping
                for mapping in mappings
                if mapping.platform == platform and mapping.external_user_id == external_user_id
            ]

    def delete_by_user(self, platform: str, external_user_id: str) -> int:
        with self._file_lock:
            mappings = self._load_mappings_unlocked()
            remaining = [
                mapping
                for mapping in mappings
                if not (mapping.platform == platform and mapping.external_user_id == external_user_id)
            ]

            deleted_count = len(mappings) - len(remaining)
            self._write_mappings_unlocked(remaining)
            return deleted_count
