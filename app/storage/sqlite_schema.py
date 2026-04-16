import sqlite3


def initialize_sqlite_schema(connection: sqlite3.Connection) -> None:
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS user_memories (
            platform TEXT NOT NULL,
            external_user_id TEXT NOT NULL,
            user_profile TEXT,
            conversation_summary TEXT,
            stable_facts_json TEXT NOT NULL DEFAULT '[]',
            preferences_json TEXT NOT NULL DEFAULT '[]',
            relationship_notes_json TEXT NOT NULL DEFAULT '[]',
            updated_at TEXT,
            PRIMARY KEY (platform, external_user_id)
        )
        """
    )

    connection.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_user_memories_platform
        ON user_memories (platform)
        """
    )

    connection.commit()
