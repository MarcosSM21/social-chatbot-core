import argparse
import sys
from dataclasses import dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from app.storage.sqlite_user_memory_repository import SQLiteUserMemoryRepository
from app.storage.user_memory_repository import UserMemoryRepository

@dataclass
class UserMemoryMigrationResult:
    source_path: str
    database_path: str
    source_count: int
    migrated_count: int
    target_count_after: int | None
    dry_run: bool


def migrate_user_memories(
        source_path : str | Path = "data/user_memories.json",
        database_path: str | Path = "data/social_chatbot.sqlite3",
        dry_run: bool = False,
) -> UserMemoryMigrationResult:
    source_repository = UserMemoryRepository(str(source_path))
    source_memories = source_repository.load_memories()

    if dry_run:
        return UserMemoryMigrationResult(
            source_path=str(source_path),
            database_path=str(database_path),
            source_count=len(source_memories),
            migrated_count=0,
            target_count_after=None,
            dry_run=True,
        )
    
    sqlite_repository = SQLiteUserMemoryRepository(str(database_path))

    for memory in source_memories:
        sqlite_repository.save(memory)

    target_count_after = len(sqlite_repository.load_memories())

    return UserMemoryMigrationResult(
        source_path=str(source_path),
        database_path=str(database_path),
        source_count=len(source_memories),
        migrated_count=len(source_memories),
        target_count_after=target_count_after,
        dry_run=False
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Migrate user memories from JSON storage to SQLite storage."
    )
    parser.add_argument(
        "--source",
        default="data/user_memories.json",
        help="Path to the source JSON user memories file.",
    )
    parser.add_argument(
        "--database",
        default="data/social_chatbot.sqlite3",
        help="Path to the target SQLite database.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be migrated without writing to SQLite.",
    )

    args = parser.parse_args()

    result = migrate_user_memories(
        source_path=args.source,
        database_path=args.database,
        dry_run=args.dry_run,
    )

    print("User memory migration result")
    print(f"- Source: {result.source_path}")
    print(f"- SQLite database: {result.database_path}")
    print(f"- Source memories: {result.source_count}")
    print(f"- Migrated memories: {result.migrated_count}")
    print(f"- Target memories after migration: {result.target_count_after}")
    print(f"- Dry run: {result.dry_run}")


if __name__ == "__main__":
    main()