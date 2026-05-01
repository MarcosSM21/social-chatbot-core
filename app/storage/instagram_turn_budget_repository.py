import json
from pathlib import Path


class InstagramTurnBudgetRepository:
    def __init__(self, file_path: str = "data/instagram_blocked_users.json") -> None:
        self.file_path = Path(file_path)
        self._ensure_storage_exists()

    def _ensure_storage_exists(self) -> None:
        self.file_path.parent.mkdir(parents=True, exist_ok=True)

        if not self.file_path.exists():
            self.file_path.write_text("{}", encoding="utf-8")

    def _load_data(self) -> dict[str, dict]:
        raw_data = json.loads(self.file_path.read_text(encoding="utf-8"))
        if not isinstance(raw_data, dict):
            return {}
        return raw_data

    def _save_data(self, data: dict[str, dict]) -> None:
        self.file_path.write_text(
            json.dumps(data, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def is_blocked(self, user_id: str) -> bool:
        data = self._load_data()
        record = data.get(user_id, {})
        return bool(record.get("blocked", False))

    def get_turn_count(self, user_id: str) -> int:
        data = self._load_data()
        record = data.get(user_id, {})
        return int(record.get("turn_count", 0))

    def increment_turn(self, user_id: str, limit: int) -> dict[str, int | bool]:
        data = self._load_data()
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
        self._save_data(data)

        is_blocked = bool(record.get("blocked", False))
        blocked_now = (not was_blocked) and is_blocked

        return {
            "turn_count": new_turn_count,
            "blocked": is_blocked,
            "blocked_now": blocked_now,
        }


    def list_records(self) -> dict[str, dict]:
        return self._load_data()
    
    def reset_user(self, user_id: str) -> bool:
        data = self._load_data()
        if user_id not in data:
            return False
        
        data[user_id] = {
            "turn_count": 0,
            "blocked": False,
        }
        self._save_data(data)
        return True
    
    

