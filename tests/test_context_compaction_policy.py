from app.models.user_memory import UserMemory
from app.storage.sqlite_user_memory_repository import SQLiteUserMemoryRepository
from app.storage.user_memory_repository import UserMemoryRepository
from scripts.inspect_llm_prompt import build_prompt_preview


def test_compacted_prompt_uses_single_compacted_block_for_identity_memory(tmp_path) -> None:
    chat_history_file = tmp_path / "chat_history.json"
    user_memory_file = tmp_path / "user_memories.json"

    memory_repository = UserMemoryRepository(str(user_memory_file))
    memory_repository.save(
        UserMemory(
            platform="instagram",
            external_user_id="user-1",
            stable_facts=["me llamo Marcos"],
        )
    )

    preview = build_prompt_preview(
        message="te acuerdas de mi nombre?",
        platform="instagram",
        external_user_id="user-1",
        session_id="session-1",
        chat_history_file=str(chat_history_file),
        user_memory_file=str(user_memory_file),
        memory_storage_backend="json",
    )

    contents = "\n".join(message["content"] for message in preview["messages"])

    assert "Compacted turn context:" in contents
    assert "Identity context:" in contents
    assert "Stable fact: me llamo Marcos" in contents
    assert "Known stable facts about this user" not in contents
    assert "Relevant memory for this turn" not in contents


def test_compacted_prompt_can_use_working_memory_as_current_topic_context(tmp_path) -> None:
    chat_history_file = tmp_path / "chat_history.json"
    user_memory_file = tmp_path / "user_memories.json"

    memory_repository = UserMemoryRepository(str(user_memory_file))
    memory_repository.save(
        UserMemory(
            platform="instagram",
            external_user_id="user-1",
            working_memory_buffer=[
                "The user is working on a project and wants the next concrete step."
            ],
            conversation_summary="The user wants practical help with the project.",
        )
    )

    preview = build_prompt_preview(
        message="qué harías ahora con el proyecto?",
        platform="instagram",
        external_user_id="user-1",
        session_id="session-1",
        chat_history_file=str(chat_history_file),
        user_memory_file=str(user_memory_file),
        memory_storage_backend="json",
    )

    contents = "\n".join(message["content"] for message in preview["messages"])

    assert "Compacted turn context:" in contents
    assert "Current topic context:" in contents
    assert "Working memory: The user is working on a project and wants the next concrete step." in contents
    assert "Conversation summary:" not in contents


def test_compacted_prompt_includes_episode_continuity_field(tmp_path) -> None:
    chat_history_file = tmp_path / "chat_history.json"
    user_memory_file = tmp_path / "user_memories.json"

    preview = build_prompt_preview(
        message="hola",
        platform="instagram",
        external_user_id="user-1",
        session_id="session-1",
        chat_history_file=str(chat_history_file),
        user_memory_file=str(user_memory_file),
        memory_storage_backend="json",
    )

    contents = "\n".join(message["content"] for message in preview["messages"])

    assert "Compacted turn context:" in contents
    assert "Episode continuity:" in contents


def test_compacted_prompt_supports_sqlite_backend(tmp_path) -> None:
    chat_history_file = tmp_path / "chat_history.json"
    sqlite_database_path = tmp_path / "memory.sqlite3"

    memory_repository = SQLiteUserMemoryRepository(str(sqlite_database_path))
    memory_repository.save(
        UserMemory(
            platform="instagram",
            external_user_id="user-1",
            stable_facts=["me llamo Marcos"],
            preferences=["prefiero respuestas cortas"],
            working_memory_buffer=[
                "The user is tired but wants to keep making progress with the project."
            ],
        )
    )

    preview = build_prompt_preview(
        message="qué harías ahora con el proyecto?",
        platform="instagram",
        external_user_id="user-1",
        session_id="session-1",
        chat_history_file=str(chat_history_file),
        sqlite_database_path=str(sqlite_database_path),
        memory_storage_backend="sqlite",
    )

    contents = "\n".join(message["content"] for message in preview["messages"])

    assert "Compacted turn context:" in contents
    assert "Preference context:" in contents
    assert "Current state context:" in contents
