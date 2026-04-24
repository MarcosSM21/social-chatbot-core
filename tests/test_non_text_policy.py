from app.models.user_memory import UserMemory
from app.storage.user_memory_repository import UserMemoryRepository


def test_empty_memory_cleanup_still_removes_placeholder_records(tmp_path) -> None:
    repository = UserMemoryRepository(str(tmp_path / "user_memories.json"))

    repository.save(
        UserMemory(
            platform="instagram",
            external_user_id="user-1",
        )
    )

    deleted_count = repository.delete_empty_memories()

    assert deleted_count == 1
    assert repository.get_by_user("instagram", "user-1") is None
