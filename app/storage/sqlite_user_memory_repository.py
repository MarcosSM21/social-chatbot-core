import json
import sqlite3

from app.models.user_memory import UserMemory
from app.storage.sqlite_connection import connect_sqlite
from app.storage.sqlite_schema import initialize_sqlite_schema



class SQLiteUserMemoryRepository:
    def __init__(self, database_path: str = "data/social_chatbot.sqlite3") -> None:
        self.database_path = database_path
        self.connection = connect_sqlite(database_path)
        initialize_sqlite_schema(self.connection)

    def _row_to_memory(self, row: sqlite3.Row) -> UserMemory:
        return UserMemory(
            platform=row["platform"],
            external_user_id=row["external_user_id"],
            last_known_username=row["last_known_username"],
            user_profile=row["user_profile"],
            conversation_summary=row["conversation_summary"],
            stable_facts=json.loads(row["stable_facts_json"]),
            preferences=json.loads(row["preferences_json"]),
            relationship_notes=json.loads(row["relationship_notes_json"]),
            updated_at=row["updated_at"],
            last_seen_at=row["last_seen_at"],
        )
    
    def load_memories(self) -> list[UserMemory]:
        rows = self.connection.execute(
            """
        SELECT
            platform,
            external_user_id,
            last_known_username,
            user_profile,
            conversation_summary,
            stable_facts_json,
            preferences_json,
            relationship_notes_json,
            updated_at,
            last_seen_at
        FROM user_memories
        ORDER BY platform, external_user_id
        """
        ).fetchall()

        return [self._row_to_memory(row) for row in rows]
    
    def save_memories(self, memories: list[UserMemory]) -> None:
        self.connection.execute("DELETE FROM user_memories")

        for memory in memories:
            self.save(memory)

        self.connection.commit()

    def get_by_user(self, platform: str, external_user_id: str) -> UserMemory | None:
        row = self.connection.execute(
            """
        SELECT
            platform,
            external_user_id,
            last_known_username,
            user_profile,
            conversation_summary,
            stable_facts_json,
            preferences_json,
            relationship_notes_json,
            updated_at,
            last_seen_at
        FROM user_memories
        WHERE platform = ? AND external_user_id = ? 
        """,
        (platform, external_user_id),
        ).fetchone()

        if row is None:
            return None
        
        return self._row_to_memory(row)
    
    def get_or_create(self, platform: str, external_user_id: str) -> UserMemory:
        memory = self.get_by_user(platform=platform, external_user_id=external_user_id)

        if memory is not None:
            return memory

        new_memory = UserMemory(
            platform=platform,
            external_user_id=external_user_id,
        )

        self.save(new_memory)
        return new_memory
    

    def save(self, memory: UserMemory) -> None:
        self.connection.execute(
            """
            INSERT INTO user_memories (
                platform,
                external_user_id,
                last_known_username,
                user_profile,
                conversation_summary,
                stable_facts_json,
                preferences_json,
                relationship_notes_json,
                updated_at,
                last_seen_at
            )
            VALUES (?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT(platform, external_user_id)
            DO UPDATE SET
                last_known_username = excluded.last_known_username,
                user_profile = excluded.user_profile,
                conversation_summary = excluded.conversation_summary,
                stable_facts_json = excluded.stable_facts_json,
                preferences_json = excluded.preferences_json,
                relationship_notes_json = excluded.relationship_notes_json,
                updated_at = excluded.updated_at,
                last_seen_at = excluded.last_seen_at
            """,
            (
                memory.platform,
                memory.external_user_id,
                memory.last_known_username,
                memory.user_profile,
                memory.conversation_summary,
                json.dumps(memory.stable_facts, ensure_ascii=False),
                json.dumps(memory.preferences, ensure_ascii=False),
                json.dumps(memory.relationship_notes, ensure_ascii=False),
                memory.updated_at,
                memory.last_seen_at,
            ),
        )
        self.connection.commit()
    

    def list_by_platform(self, platform: str) -> list[UserMemory]:
        rows = self.connection.execute(
            """
            SELECT
                platform,
                external_user_id,
                last_known_username,
                user_profile,
                conversation_summary,
                stable_facts_json,
                preferences_json,
                relationship_notes_json,
                updated_at,
                last_seen_at
            FROM user_memories
            WHERE platform = ?
            ORDER BY external_user_id
            """,
            (platform,),
        ).fetchall()

        return [self._row_to_memory(row) for row in rows]    
    

    def delete_by_user(self, platform: str, external_user_id: str) -> bool:
        cursor = self.connection.execute(
            """
            DELETE FROM user_memories
            WHERE  platform = ? AND external_user_id = ?
            """,
            (platform, external_user_id),
        )
        self.connection.commit()

        return cursor.rowcount > 0
    
    def has_meaningful_memory(self, memory: UserMemory) -> bool:
        return bool(
            memory.user_profile
            or memory.conversation_summary
            or memory.stable_facts
            or memory.preferences
            or memory.relationship_notes
        )
    
    def delete_empty_memories(self) -> int:
        memories = self.load_memories()
        empty_memories = [
            memory
            for memory in memories
            if not self.has_meaningful_memory(memory)
        ]

        for memory in empty_memories:
            self.delete_by_user(
                platform=memory.platform,
                external_user_id=memory.external_user_id,
            )

        return len(empty_memories)
