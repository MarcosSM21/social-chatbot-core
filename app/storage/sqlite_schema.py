import sqlite3


def initialize_sqlite_schema(connection: sqlite3.Connection) -> None:
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS user_memories (
            platform TEXT NOT NULL,
            external_user_id TEXT NOT NULL,
            last_known_username TEXT,
            user_profile TEXT,
            conversation_summary TEXT,
            stable_facts_json TEXT NOT NULL DEFAULT '[]',
            preferences_json TEXT NOT NULL DEFAULT '[]',
            relationship_notes_json TEXT NOT NULL DEFAULT '[]',
            updated_at TEXT,
            last_seen_at TEXT,
            PRIMARY KEY (platform, external_user_id)
        )
        """
    )

    _ensure_column_exists(connection, "user_memories", "last_known_username", "TEXT")
    _ensure_column_exists(connection, "user_memories", "last_seen_at", "TEXT")

    connection.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_user_memories_platform
        ON user_memories (platform)
        """
    )

    connection.commit()


def _ensure_column_exists(
    connection: sqlite3.Connection,
    table_name: str,
    column_name: str,
    column_definition: str,
) -> None:
    rows = connection.execute(f"PRAGMA table_info({table_name})").fetchall()
    existing_columns = {row[1] for row in rows}

    if column_name in existing_columns:
        return

    connection.execute(
        f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_definition}"
    )

