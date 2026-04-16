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


def test_list_by_platform_returns_only_platform_memories(tmp_path) -> None:
    repository = UserMemoryRepository(str(tmp_path / "user_memories.json"))

    repository.save(UserMemory(platform="instagram", external_user_id="ig-1"))
    repository.save(UserMemory(platform="instagram", external_user_id="ig-2"))
    repository.save(UserMemory(platform="api", external_user_id="api-1"))

    memories = repository.list_by_platform("instagram")

    assert [memory.external_user_id for memory in memories] == ["ig-1", "ig-2"]


def test_delete_by_user_removes_existing_memory(tmp_path) -> None:
    repository = UserMemoryRepository(str(tmp_path / "user_memories.json"))

    repository.save(
        UserMemory(
            platform="instagram",
            external_user_id="user-1",
            stable_facts=["me llamo Marcos"],
        )
    )

    deleted = repository.delete_by_user("instagram", "user-1")

    assert deleted is True
    assert repository.get_by_user("instagram", "user-1") is None


def test_delete_by_user_returns_false_when_missing(tmp_path) -> None:
    repository = UserMemoryRepository(str(tmp_path / "user_memories.json"))

    deleted = repository.delete_by_user("instagram", "missing-user")

    assert deleted is False


def test_delete_empty_memories_removes_only_empty_records(tmp_path) -> None:
    repository = UserMemoryRepository(str(tmp_path / "user_memories.json"))

    repository.save(UserMemory(platform="instagram", external_user_id="empty-user"))
    repository.save(
        UserMemory(
            platform="instagram",
            external_user_id="memory-user",
            preferences=["prefiero respuestas cortas"],
        )
    )

    deleted_count = repository.delete_empty_memories()
    remaining_memories = repository.load_memories()

    assert deleted_count == 1
    assert len(remaining_memories) == 1
    assert remaining_memories[0].external_user_id == "memory-user"

