from app.models.user_memory import UserMemory
from app.storage.sqlite_user_memory_repository import SQLiteUserMemoryRepository


def build_repository(tmp_path) -> SQLiteUserMemoryRepository:
    return SQLiteUserMemoryRepository(str(tmp_path / "test.sqlite3"))


def test_sqlite_get_or_create_creates_memory(tmp_path) -> None:
    repository = build_repository(tmp_path)

    memory = repository.get_or_create("instagram", "user-1")

    assert memory.platform == "instagram"
    assert memory.external_user_id == "user-1"
    assert repository.get_by_user("instagram", "user-1") is not None


def test_sqlite_save_updates_existing_memory(tmp_path) -> None:
    repository = build_repository(tmp_path)

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
            stable_facts=["me llamo Marcos"],
            preferences=["prefiero respuestas cortas"],
            relationship_notes=["no le gusta que le sobreexpliquen"],
        )
    )

    memory = repository.get_by_user("instagram", "user-1")

    assert memory is not None
    assert memory.user_profile == "new"
    assert memory.stable_facts == ["me llamo Marcos"]
    assert memory.preferences == ["prefiero respuestas cortas"]
    assert memory.relationship_notes == ["no le gusta que le sobreexpliquen"]


def test_sqlite_list_by_platform_returns_only_platform_memories(tmp_path) -> None:
    repository = build_repository(tmp_path)

    repository.save(UserMemory(platform="instagram", external_user_id="ig-1"))
    repository.save(UserMemory(platform="instagram", external_user_id="ig-2"))
    repository.save(UserMemory(platform="api", external_user_id="api-1"))

    memories = repository.list_by_platform("instagram")

    assert [memory.external_user_id for memory in memories] == ["ig-1", "ig-2"]


def test_sqlite_delete_by_user_removes_existing_memory(tmp_path) -> None:
    repository = build_repository(tmp_path)
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


def test_sqlite_delete_by_user_returns_false_when_missing(tmp_path) -> None:
    repository = build_repository(tmp_path)

    deleted = repository.delete_by_user("instagram", "missing-user")

    assert deleted is False


def test_sqlite_delete_empty_memories_removes_only_empty_records(tmp_path) -> None:
    repository = build_repository(tmp_path)

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
