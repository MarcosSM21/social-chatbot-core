from app.storage.sqlite_connection import connect_sqlite
from app.storage.sqlite_schema import initialize_sqlite_schema


def test_initialize_sqlite_schema_creates_user_memories_table(tmp_path) -> None:
    database_path = tmp_path / "test.sqlite3"
    connection = connect_sqlite(str(database_path))

    initialize_sqlite_schema(connection)

    tables = connection.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table'"
    ).fetchall()

    table_names = [row["name"] for row in tables]

    assert "user_memories" in table_names


def test_initialize_sqlite_schema_is_idempotent(tmp_path) -> None:
    database_path = tmp_path / "test.sqlite3"
    connection = connect_sqlite(str(database_path))

    initialize_sqlite_schema(connection)
    initialize_sqlite_schema(connection)

    rows = connection.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'user_memories'"
    ).fetchall()

    assert len(rows) == 1
