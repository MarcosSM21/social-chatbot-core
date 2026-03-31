import json
from pathlib import Path

from app.models.user_memory import UserMemory


class UserMemoryRepository:
    def __init__(self, file_path: str = "data/user_memories.json") -> None:
        self.file_path = Path(file_path)
        self._ensure_storage_exists()

    def _ensure_storage_exists(self) -> None:
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.file_path.exists():
            self.file_path.write_text("[]", encoding="utf-8")

    def load_memories(self) -> list[UserMemory]:
        raw_data = json.loads(self.file_path.read_text(encoding="utf-8"))
        return [UserMemory.from_dict(item) for item in raw_data]
    
    def save_memories(self, memories: list[UserMemory]) -> None:
        serialized_memories = [memory.to_dict() for memory in memories]
        self.file_path.write_text(
            json.dumps(serialized_memories, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def get_by_user(self, platform: str, external_user_id: str) -> UserMemory | None:
        memories = self.load_memories()

        for memory in memories:
            if (
                memory.platform == platform
                and memory.external_user_id == external_user_id
            ):
                return memory
            
        return None
    
    def get_or_create(self, platform: str, external_user_id: str) -> UserMemory:
        memory = self.get_by_user(platform=platform, external_user_id=external_user_id)

        if memory is not None:
            return memory
        
        new_memory = UserMemory(
            platform=platform,
            external_user_id=external_user_id,
        )

        memories = self.load_memories()
        memories.append(new_memory)
        self.save_memories(memories)

        return new_memory
    
    def save(self, memory: UserMemory) -> None:
        memories = self.load_memories()

        for index, stored_memory in enumerate(memories):
            if (
                stored_memory.platform == memory.platform
                and stored_memory.external_user_id == memory.external_user_id
            ):
                memories[index] = memory
                self.save_memories(memories)
                return
        
        memories.append(memory)
        self.save_memories(memories)
