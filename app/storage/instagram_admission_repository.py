from pathlib import Path

from app.storage.atomic_json_file import atomic_write_json_file, read_json_file
from app.storage.file_lock_registry import get_file_lock


class InstagramAdmissionRepository:
    def __init__(self, file_path: str = "data/instagram_admitted_users.json") -> None:
        self.file_path = Path(file_path)
        self._file_lock = get_file_lock(self.file_path)
        self._ensure_storage_exists()

    def _ensure_storage_exists(self) -> None:
        self.file_path.parent.mkdir(parents=True, exist_ok=True)

        if not self.file_path.exists():
            atomic_write_json_file(self.file_path, [])

    def _load_user_ids_unlocked(self) -> list[str]:
        raw_data = read_json_file(self.file_path, [])
        return [str(item).strip() for item in raw_data if str(item).strip()]

    def _write_user_ids_unlocked(self, user_ids: list[str]) -> None:
        normalized: list[str] = []

        for user_id in user_ids:
            cleaned = user_id.strip()
            if cleaned and cleaned not in normalized:
                normalized.append(cleaned)

        atomic_write_json_file(self.file_path, normalized)

    def load_user_ids(self) -> list[str]:
        with self._file_lock:
            return self._load_user_ids_unlocked()

    def save_user_ids(self, user_ids: list[str]) -> None:
        with self._file_lock:
            self._write_user_ids_unlocked(user_ids)

    def list_user_ids(self) -> list[str]:
        with self._file_lock:
            return self._load_user_ids_unlocked()

    def contains(self, user_id: str) -> bool:
        with self._file_lock:
            return user_id in self._load_user_ids_unlocked()

    def count(self) -> int:
        with self._file_lock:
            return len(self._load_user_ids_unlocked())

    def add_user_id(self, user_id: str) -> bool:
        cleaned = user_id.strip()
        if not cleaned:
            return False

        with self._file_lock:
            user_ids = self._load_user_ids_unlocked()
            if cleaned in user_ids:
                return False

            user_ids.append(cleaned)
            self._write_user_ids_unlocked(user_ids)
            return True

    def remove_user_id(self, user_id: str) -> bool:
        with self._file_lock:
            user_ids = self._load_user_ids_unlocked()
            if user_id not in user_ids:
                return False

            updated = [item for item in user_ids if item != user_id]
            self._write_user_ids_unlocked(updated)
            return True
