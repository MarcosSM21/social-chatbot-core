from app.models.user_memory import UserMemory
from app.storage.sqlite_user_memory_repository import SQLiteUserMemoryRepository
from app.storage.user_memory_repository import UserMemoryRepository
from scripts.inspect_user_memory import build_memory_preview


def test_build_memory_preview_reads_json_backend_user_memory(tmp_path) -> None:
    user_memory_file = tmp_path / "user_memories.json"

    repository = UserMemoryRepository(str(user_memory_file))
    repository.save(
        UserMemory(
            platform="instagram",
            external_user_id="user-1",
            stable_facts=["me llamo Marcos"],
            preferences=["prefiero respuestas cortas"],
            conversation_summary="The user wants practical help.",
            working_memory_buffer=[
                "The user is working on a project and wants the next concrete step."
            ],
        )
    )

    preview = build_memory_preview(
        platform="instagram",
        external_user_id="user-1",
        memory_storage_backend="json",
        user_memory_file=str(user_memory_file),
    )

    assert preview["found"] is True
    assert preview["memory"]["stable_facts"] == ["me llamo Marcos"]
    assert preview["memory"]["preferences"] == ["prefiero respuestas cortas"]
    assert preview["memory"]["working_memory_buffer"] == [
        "The user is working on a project and wants the next concrete step."
    ]


def test_build_memory_preview_reads_sqlite_backend_user_memory(tmp_path) -> None:
    sqlite_database_path = tmp_path / "memory.sqlite3"

    repository = SQLiteUserMemoryRepository(str(sqlite_database_path))
    repository.save(
        UserMemory(
            platform="instagram",
            external_user_id="user-1",
            stable_facts=["me llamo Marcos"],
            working_memory_buffer=[
                "The user is working on a project and wants the next concrete step."
            ],
        )
    )

    preview = build_memory_preview(
        platform="instagram",
        external_user_id="user-1",
        memory_storage_backend="sqlite",
        sqlite_database_path=str(sqlite_database_path),
    )

    assert preview["found"] is True
    assert preview["memory"]["stable_facts"] == ["me llamo Marcos"]
    assert preview["memory"]["working_memory_buffer"] == [
        "The user is working on a project and wants the next concrete step."
    ]


def test_build_memory_preview_can_list_platform_memories(tmp_path) -> None:
    user_memory_file = tmp_path / "user_memories.json"

    repository = UserMemoryRepository(str(user_memory_file))
    repository.save(
        UserMemory(
            platform="instagram",
            external_user_id="user-1",
            stable_facts=["me llamo Marcos"],
        )
    )
    repository.save(
        UserMemory(
            platform="instagram",
            external_user_id="user-2",
            preferences=["prefiero respuestas cortas"],
        )
    )

    preview = build_memory_preview(
        platform="instagram",
        memory_storage_backend="json",
        user_memory_file=str(user_memory_file),
        list_only=True,
    )

    assert preview["platform"] == "instagram"
    assert preview["count"] == 2
    assert len(preview["memories"]) == 2
