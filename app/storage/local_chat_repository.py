from pathlib import Path

from app.models.chat import ChatTurn
from app.storage.atomic_json_file import atomic_write_json_file, read_json_file
from app.storage.file_lock_registry import get_file_lock


class LocalChatRepository:
    def __init__(self, file_path: str = "data/chat_history.json") -> None:
        self.file_path = Path(file_path)
        self._file_lock = get_file_lock(self.file_path)
        self.__ensure_storage_exists()

    def __ensure_storage_exists(self) -> None:
        self.file_path.parent.mkdir(parents=True, exist_ok=True)

        if not self.file_path.exists():
            atomic_write_json_file(self.file_path, [])

    def _load_turns_unlocked(self) -> list[ChatTurn]:
        raw_data = read_json_file(self.file_path, [])
        return [ChatTurn.from_dict(item) for item in raw_data]

    def _write_turns_unlocked(self, turns: list[ChatTurn]) -> None:
        serialized_turns = [stored_turn.to_dict() for stored_turn in turns]
        atomic_write_json_file(self.file_path, serialized_turns)

    def load_turns(self) -> list[ChatTurn]:
        with self._file_lock:
            return self._load_turns_unlocked()

    def get_recent_turns(self, session_id: str, limit: int = 3) -> list[ChatTurn]:
        with self._file_lock:
            turns = self._load_turns_unlocked()
            session_turns = [turn for turn in turns if turn.session_id == session_id]
            return session_turns[-limit:]

    def save_turn(self, turn: ChatTurn) -> None:
        with self._file_lock:
            turns = self._load_turns_unlocked()
            turns.append(turn)
            self._write_turns_unlocked(turns)

    def delete_turns_by_session_ids(self, session_ids: list[str]) -> int:
        if not session_ids:
            return 0

        with self._file_lock:
            turns = self._load_turns_unlocked()
            remaining_turns = [
                turn
                for turn in turns
                if turn.session_id not in session_ids
            ]

            deleted_count = len(turns) - len(remaining_turns)
            self._write_turns_unlocked(remaining_turns)

            return deleted_count
