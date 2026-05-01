import json
from pathlib import Path


class InstagramAdmissionRepository:
    def __init__(self, file_path: str = "data/instagram_admitted_users.json") -> None:
        self.file_path = Path(file_path)
        self._ensure_storage_exists()

    def _ensure_storage_exists(self) -> None:
        self.file_path.parent.mkdir(parents=True, exist_ok=True)

        if not self.file_path.exists():
            self.file_path.write_text("[]", encoding="utf-8")

    def load_user_ids(self) -> list[str]:
        raw_data = json.loads(self.file_path.read_text(encoding="utf-8"))
        return [str(item).strip() for item in raw_data if str(item).strip()]

    def save_user_ids(self, user_ids: list[str]) -> None:
        normalized = []
        for user_id in user_ids:
            cleaned = user_id.strip()
            if cleaned and cleaned not in normalized:
                normalized.append(cleaned)

        self.file_path.write_text(
            json.dumps(normalized, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def list_user_ids(self) -> list[str]:
        return self.load_user_ids()

    def contains(self, user_id: str) -> bool:
        return user_id in self.load_user_ids()

    def count(self) -> int:
        return len(self.load_user_ids())

    def add_user_id(self, user_id: str) -> bool:
        cleaned = user_id.strip()
        if not cleaned:
            return False

        user_ids = self.load_user_ids()
        if cleaned in user_ids:
            return False

        user_ids.append(cleaned)
        self.save_user_ids(user_ids)
        return True
    

    def remove_user_id(self, user_id: str) -> bool:
        user_ids = self.load_user_ids()
        if user_id not in user_ids:
            return False
        
        updated = [item for item in user_ids if item!= user_id]
        self.save_user_ids(updated)
        return True

