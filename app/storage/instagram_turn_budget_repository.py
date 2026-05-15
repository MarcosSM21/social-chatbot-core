from pathlib import Path

from app.storage.atomic_json_file import atomic_write_json_file, read_json_file
from app.storage.file_lock_registry import get_file_lock


class InstagramTurnBudgetRepository:
    def __init__(self, file_path: str = "data/instagram_blocked_users.json") -> None:
        self.file_path = Path(file_path)
        self._file_lock = get_file_lock(self.file_path)
        self._ensure_storage_exists()

    def _ensure_storage_exists(self) -> None:
        self.file_path.parent.mkdir(parents=True, exist_ok=True)

        if not self.file_path.exists():
            atomic_write_json_file(self.file_path, {})

    def _load_data_unlocked(self) -> dict[str, dict]:
        raw_data = read_json_file(self.file_path, {})
        if not isinstance(raw_data, dict):
            return {}
        return raw_data

    def _save_data_unlocked(self, data: dict[str, dict]) -> None:
        atomic_write_json_file(self.file_path, data)

    def is_blocked(self, user_id: str) -> bool:
        with self._file_lock:
            data = self._load_data_unlocked()
            record = data.get(user_id, {})
            return bool(record.get("blocked", False))

    def get_turn_count(self, user_id: str) -> int:
        with self._file_lock:
            data = self._load_data_unlocked()
            record = data.get(user_id, {})
            return int(record.get("turn_count", 0))

    def increment_turn(self, user_id: str, limit: int) -> dict[str, int | bool]:
        with self._file_lock:
            data = self._load_data_unlocked()
            record = data.get(
                user_id,
                {
                    "turn_count": 0,
                    "blocked": False,
                },
            )

            was_blocked = bool(record.get("blocked", False))
            previous_turn_count = int(record.get("turn_count", 0))

            new_turn_count = previous_turn_count + 1
            record["turn_count"] = new_turn_count

            if limit > 0 and new_turn_count >= limit:
                record["blocked"] = True

            data[user_id] = record
            self._save_data_unlocked(data)

            is_blocked = bool(record.get("blocked", False))
            blocked_now = (not was_blocked) and is_blocked

            return {
                "turn_count": new_turn_count,
                "blocked": is_blocked,
                "blocked_now": blocked_now,
            }

    def list_records(self) -> dict[str, dict]:
        with self._file_lock:
            return self._load_data_unlocked()

    def reset_user(self, user_id: str) -> bool:
        with self._file_lock:
            data = self._load_data_unlocked()
            if user_id not in data:
                return False

            data[user_id] = {
                "turn_count": 0,
                "blocked": False,
            }
            self._save_data_unlocked(data)
            return True
