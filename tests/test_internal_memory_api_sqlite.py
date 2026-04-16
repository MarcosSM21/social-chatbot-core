from app.api import main as api_main
from app.models.user_memory import UserMemory
from app.storage.sqlite_user_memory_repository import SQLiteUserMemoryRepository


def configure_sqlite_memory_backend(monkeypatch, tmp_path) -> SQLiteUserMemoryRepository:
    database_path = tmp_path / "memory.sqlite3"

    monkeypatch.setattr(api_main.settings, "memory_storage_backend", "sqlite")
    monkeypatch.setattr(api_main.settings, "sqlite_database_path", str(database_path))

    return SQLiteUserMemoryRepository(str(database_path))


def test_internal_memory_list_uses_sqlite_backend(monkeypatch, tmp_path) -> None:
    repository = configure_sqlite_memory_backend(monkeypatch, tmp_path)

    repository.save(
        UserMemory(
            platform="instagram",
            external_user_id="user-1",
            stable_facts=["se llama Marcos"],
            preferences=["prefiere respuestas cortas"],
        )
    )
    repository.save(
        UserMemory(
            platform="api",
            external_user_id="api-user-1",
            stable_facts=["usuario interno"],
        )
    )

    response = api_main.list_internal_memory_by_platform("instagram")

    assert response.platform == "instagram"
    assert response.count == 1
    assert response.memories[0].external_user_id == "user-1"
    assert response.memories[0].stable_facts == ["se llama Marcos"]
    assert response.memories[0].preferences == ["prefiere respuestas cortas"]


def test_internal_memory_detail_uses_sqlite_backend(monkeypatch, tmp_path) -> None:
    repository = configure_sqlite_memory_backend(monkeypatch, tmp_path)

    repository.save(
        UserMemory(
            platform="instagram",
            external_user_id="user-1",
            user_profile="Marcos",
            relationship_notes=["le gusta un tono natural"],
        )
    )

    response = api_main.get_internal_memory_by_user("instagram", "user-1")

    assert response.platform == "instagram"
    assert response.external_user_id == "user-1"
    assert response.user_profile == "Marcos"
    assert response.relationship_notes == ["le gusta un tono natural"]


def test_internal_memory_delete_uses_sqlite_backend(monkeypatch, tmp_path) -> None:
    repository = configure_sqlite_memory_backend(monkeypatch, tmp_path)

    repository.save(
        UserMemory(
            platform="instagram",
            external_user_id="user-1",
            stable_facts=["se llama Marcos"],
        )
    )

    response = api_main.delete_internal_memory_by_user("instagram", "user-1")

    assert response.deleted is True

    assert repository.get_by_user("instagram", "user-1") is None


def test_internal_memory_delete_empty_uses_sqlite_backend(monkeypatch, tmp_path) -> None:
    repository = configure_sqlite_memory_backend(monkeypatch, tmp_path)

    repository.save(UserMemory(platform="instagram", external_user_id="empty-user"))
    repository.save(
        UserMemory(
            platform="instagram",
            external_user_id="memory-user",
            stable_facts=["se llama Marcos"],
        )
    )

    response = api_main.delete_empty_internal_memories()

    assert response.deleted_count == 1

    assert repository.get_by_user("instagram", "empty-user") is None
    assert repository.get_by_user("instagram", "memory-user") is not None
