import json

from app.storage.sqlite_user_memory_repository import SQLiteUserMemoryRepository
from scripts.migrate_user_memories_to_sqlite import migrate_user_memories


def test_migrate_user_memories_to_sqlite_copies_json_memories(tmp_path) -> None:
    source_path = tmp_path / "user_memories.json"
    database_path = tmp_path / "memory.sqlite3"

    source_path.write_text(
        json.dumps(
            [
                {
                    "platform": "instagram",
                    "external_user_id": "user-1",
                    "user_profile": "Marcos",
                    "conversation_summary": "Le gustan las respuestas tranquilas.",
                    "stable_facts": ["se llama Marcos"],
                    "preferences": ["prefiere respuestas cortas"],
                    "relationship_notes": ["no le gusta que le sobreexpliquen"],
                    "updated_at": "2026-04-16T10:00:00",
                }
            ],
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    result = migrate_user_memories(
        source_path=source_path,
        database_path=database_path,
    )

    sqlite_repository = SQLiteUserMemoryRepository(str(database_path))
    memory = sqlite_repository.get_by_user("instagram", "user-1")

    assert result.source_count == 1
    assert result.migrated_count == 1
    assert result.target_count_after == 1

    assert memory is not None
    assert memory.user_profile == "Marcos"
    assert memory.stable_facts == ["se llama Marcos"]
    assert memory.preferences == ["prefiere respuestas cortas"]
    assert memory.relationship_notes == ["no le gusta que le sobreexpliquen"]


def test_migrate_user_memories_to_sqlite_dry_run_does_not_write(tmp_path) -> None:
    source_path = tmp_path / "user_memories.json"
    database_path = tmp_path / "memory.sqlite3"

    source_path.write_text(
        json.dumps(
            [
                {
                    "platform": "instagram",
                    "external_user_id": "user-1",
                    "user_profile": "Marcos",
                }
            ],
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    result = migrate_user_memories(
        source_path=source_path,
        database_path=database_path,
        dry_run=True,
    )

    assert result.source_count == 1
    assert result.migrated_count == 0
    assert result.target_count_after is None
    assert database_path.exists() is False
