from app.models.user_memory import UserMemory
from app.storage.user_memory_repository import UserMemoryRepository


def test_get_or_create_creates_memory(tmp_path) -> None:
    repository = UserMemoryRepository(str(tmp_path / "user_memories.json"))

    memory = repository.get_or_create("instagram", "user-1")

    assert memory.platform == "instagram"
    assert memory.external_user_id == "user-1"
    assert repository.get_by_user("instagram", "user-1") is not None


def test_get_or_create_returns_existing_memory(tmp_path) -> None:
    repository = UserMemoryRepository(str(tmp_path / "user_memories.json"))
    memory = repository.get_or_create("instagram", "user-1")
    memory.user_profile = "me llamo Marcos"
    repository.save(memory)

    existing_memory = repository.get_or_create("instagram", "user-1")

    assert existing_memory.user_profile == "me llamo Marcos"


def test_save_updates_existing_memory(tmp_path) -> None:
    repository = UserMemoryRepository(str(tmp_path / "user_memories.json"))
    repository.save(
        UserMemory(
            platform="instagram",
            external_user_id="user-1",
            user_profile="old",
        )
    )

    repository.save(
        UserMemory(
            platform="instagram",
            external_user_id="user-1",
            user_profile="new",
        )
    )

    memories = repository.load_memories()
    assert len(memories) == 1
    assert memories[0].user_profile == "new"


def test_user_memory_from_old_shape_keeps_new_fields_empty() -> None:
    memory = UserMemory.from_dict(
        {
            "platform": "instagram",
            "external_user_id": "user-1",
            "user_profile": "me llamo Marcos",
            "conversation_summary": "old summary",
        }
    )

    assert memory.stable_facts == []
    assert memory.preferences == []
    assert memory.relationship_notes == []


def test_save_preserves_structured_memory_fields(tmp_path) -> None:
    repository = UserMemoryRepository(str(tmp_path / "user_memories.json"))

    repository.save(
        UserMemory(
            platform="instagram",
            external_user_id="user-1",
            stable_facts=["me llamo Marcos"],
            preferences=["prefiero respuestas cortas"],
            relationship_notes=["no le gusta que le sobreexpliquen"],
        )
    )

    memory = repository.get_or_create("instagram", "user-1")

    assert memory.stable_facts == ["me llamo Marcos"]
    assert memory.preferences == ["prefiero respuestas cortas"]
    assert memory.relationship_notes == ["no le gusta que le sobreexpliquen"]

