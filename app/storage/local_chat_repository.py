import json
from pathlib import Path

from app.models.chat import ChatTurn

class LocalChatRepository:
    def __init__(self, file_path:str = "data/chat_history.json") -> None:
        self.file_path = Path(file_path)
        self.__ensure_storage_exissts()

    def __ensure_storage_exissts(self) -> None:
        self.file_path.parent.mkdir(parents=True, exist_ok=True)

        if not self.file_path.exists():
            self.file_path.write_text("[]", encoding="utf-8")

    def load_turns(self)-> list[ChatTurn]:
        raw_data = json.loads(self.file_path.read_text(encoding="utf-8"))
        return [ChatTurn.from_dict(item) for item in raw_data]
    
    def get_recent_turns(self, limit:int = 3) -> list[ChatTurn]:
        turns = self.load_turns()
        return turns[-limit:] # Devuelve los últimos '3' turnos de conversación
    
    def save_turn(self, turn:ChatTurn) -> None:
        turns = self.load_turns()
        turns.append(turn)

        serialized_turns = [stored_turn.to_dict() for stored_turn in turns]

        self.file_path.write_text(
            json.dumps(serialized_turns, indent=2, ensure_ascii=False),
            encoding="utf-8"    
        )


    