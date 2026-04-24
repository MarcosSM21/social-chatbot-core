import pytest

from app.core.container import build_user_memory_repository
from app.core.settings import Settings
from app.storage.sqlite_user_memory_repository import SQLiteUserMemoryRepository
from app.storage.user_memory_repository import UserMemoryRepository



def test_build_user_memory_repository_can_use_sqlite(tmp_path) -> None:
    settings = Settings.from_env()
    settings.memory_storage_backend = "sqlite"
    settings.sqlite_database_path = str(tmp_path / "memory.sqlite3")

    repository = build_user_memory_repository(settings)

    assert isinstance(repository, SQLiteUserMemoryRepository)

    memory = repository.get_or_create("instagram", "user-1")

    assert memory.platform == "instagram"
    assert memory.external_user_id == "user-1"


def test_build_user_memory_repository_rejects_unknown_backend() -> None:
    settings = Settings.from_env()
    settings.memory_storage_backend = "unknown"

    with pytest.raises(ValueError, match="Unsupported memory storage backend"):
        build_user_memory_repository(settings)


def test_build_user_memory_repository_uses_sqlite_by_default(monkeypatch, tmp_path) -> None:
    monkeypatch.delenv("MEMORY_STORAGE_BACKEND", raising=False)
    monkeypatch.setenv("SQLITE_DATABASE_PATH", str(tmp_path / "memory.sqlite3"))

    settings = Settings.from_env()
    repository = build_user_memory_repository(settings)

    assert isinstance(repository, SQLiteUserMemoryRepository)


def test_build_user_memory_repository_can_use_json_with_explicit_path(tmp_path) -> None:
    settings = Settings.from_env()
    settings.memory_storage_backend = "json"
    settings.json_user_memory_path = str(tmp_path / "user_memories.json")

    repository = build_user_memory_repository(settings)

    assert isinstance(repository, UserMemoryRepository)

    memory = repository.get_or_create("instagram", "user-1")

    assert memory.platform == "instagram"
    assert memory.external_user_id == "user-1"


