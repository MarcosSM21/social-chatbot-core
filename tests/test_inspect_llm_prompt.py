from app.models.user_memory import UserMemory
from app.storage.user_memory_repository import UserMemoryRepository
from scripts.inspect_llm_prompt import build_prompt_preview
from app.storage.sqlite_user_memory_repository import SQLiteUserMemoryRepository



def test_build_prompt_preview_contains_final_user_message(tmp_path) -> None:
    chat_history_file = tmp_path / "chat_history.json"
    user_memory_file = tmp_path / "user_memories.json"

    preview = build_prompt_preview(
        message="hola, qué tal?",
        platform="instagram",
        external_user_id="user-1",
        session_id="session-1",
        chat_history_file=str(chat_history_file),
        user_memory_file=str(user_memory_file),
        memory_storage_backend="json",
    )

    assert preview["messages"][-1] == {
        "role": "user",
        "content": "hola, qué tal?",
    }


def test_build_prompt_preview_includes_character_context(tmp_path) -> None:
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

    system_messages = [
        message["content"]
        for message in preview["messages"]
        if message["role"] == "system"
    ]

    assert any("Active character brief." in message for message in system_messages)
    assert any("Name:" in message for message in system_messages)
    assert preview["character"]["display_name"]



def test_build_prompt_preview_includes_user_memory(tmp_path) -> None:
    chat_history_file = tmp_path / "chat_history.json"
    user_memory_file = tmp_path / "user_memories.json"

    memory_repository = UserMemoryRepository(str(user_memory_file))
    memory_repository.save(
        UserMemory(
            platform="instagram",
            external_user_id="user-1",
            stable_facts=["me llamo Marcos"],
            preferences=["prefiero respuestas cortas"],
            relationship_notes=["no le gusta que le sobreexpliquen"],
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
    assert "Preference context:" in contents
    assert "Preference: prefiero respuestas cortas" in contents


def test_prompt_system_instructions_do_not_use_bot_name_as_identity(tmp_path, monkeypatch) -> None:
    chat_history_file = tmp_path / "chat_history.json"
    user_memory_file = tmp_path / "user_memories.json"

    monkeypatch.setenv("BOT_NAME", "Willy")

    preview = build_prompt_preview(
        message="hola",
        platform="instagram",
        external_user_id="user-1",
        session_id="session-1",
        chat_history_file=str(chat_history_file),
        user_memory_file=str(user_memory_file),
        memory_storage_backend="json",
    )

    first_message = preview["messages"][0]

    assert first_message["role"] == "system"
    assert "You are Willy" not in first_message["content"]
    assert "active character instructions" in first_message["content"]


def test_prompt_character_is_declared_as_only_conversational_identity(tmp_path) -> None:
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

    assert "Your conversational identity, voice, and boundaries come from the active character instructions. " in contents

def test_prompt_does_not_include_global_style_constraints(tmp_path) -> None:
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

    assert "Global style constraints" not in contents
    assert "short_direct_calm" not in contents



def test_prompt_uses_compact_character_brief(tmp_path, monkeypatch) -> None:
    chat_history_file = tmp_path / "chat_history.json"
    user_memory_file = tmp_path / "user_memories.json"

    monkeypatch.setenv("CHARACTER_FILE", "characters/laia_ambitious_model.json")

    preview = build_prompt_preview(
        message="holaa",
        platform="instagram",
        external_user_id="user-1",
        session_id="session-1",
        chat_history_file=str(chat_history_file),
        user_memory_file=str(user_memory_file),
        memory_storage_backend="json",
    )

    contents = "\n".join(message["content"] for message in preview["messages"])

    assert "Active character brief." in contents
    assert "Name: Laia." in contents
    assert "Inner world:" in contents
    assert "Motivations:" in contents
    assert "Relationship dynamic:" in contents
    assert "Conversation habits:" in contents
    assert "Do not mention the character profile." in contents


def test_prompt_does_not_include_good_response_examples_as_templates(tmp_path, monkeypatch) -> None:
    chat_history_file = tmp_path / "chat_history.json"
    user_memory_file = tmp_path / "user_memories.json"

    monkeypatch.setenv("CHARACTER_FILE", "characters/laia_ambitious_model.json")

    preview = build_prompt_preview(
        message="holaa",
        platform="instagram",
        external_user_id="user-1",
        session_id="session-1",
        chat_history_file=str(chat_history_file),
        user_memory_file=str(user_memory_file),
        memory_storage_backend="json",
    )

    contents = "\n".join(message["content"] for message in preview["messages"])

    assert "good_response_examples" not in contents
    assert "bad_response_examples" not in contents
    assert "holiii, todo bien por aquí" not in contents


def test_build_prompt_preview_includes_retrieved_memory_block(tmp_path) -> None:
    chat_history_file = tmp_path / "chat_history.json"
    user_memory_file = tmp_path / "user_memories.json"

    memory_repository = UserMemoryRepository(str(user_memory_file))
    memory_repository.save(
        UserMemory(
            platform="instagram",
            external_user_id="user-1",
            stable_facts=["me llamo Marcos"],
            preferences=["prefiero respuestas cortas"],
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

def test_build_prompt_preview_can_use_working_memory_in_retrieved_memory_block(tmp_path) -> None:
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
            conversation_summary="The user wants practical help.",
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
    assert preview["memory"]["retrieved_memory_reasons"] is not None


def test_build_prompt_preview_uses_configured_sqlite_backend(tmp_path) -> None:
    chat_history_file = tmp_path / "chat_history.json"
    sqlite_database_path = tmp_path / "memory.sqlite3"

    memory_repository = SQLiteUserMemoryRepository(str(sqlite_database_path))
    memory_repository.save(
        UserMemory(
            platform="instagram",
            external_user_id="user-1",
            stable_facts=["me llamo Marcos"],
            working_memory_buffer=[
                "The user is working on a project and wants the next concrete step."
            ],
        )
    )

    preview = build_prompt_preview(
        message="te acuerdas de mi nombre?",
        platform="instagram",
        external_user_id="user-1",
        session_id="session-1",
        chat_history_file=str(chat_history_file),
        sqlite_database_path=str(sqlite_database_path),
        memory_storage_backend="sqlite",
    )

    contents = "\n".join(message["content"] for message in preview["messages"])

    assert "Compacted turn context:" in contents
    assert "Identity context:" in contents
    assert "Stable fact: me llamo Marcos" in contents


def test_build_prompt_preview_includes_compacted_turn_context_block(tmp_path) -> None:
    chat_history_file = tmp_path / "chat_history.json"
    user_memory_file = tmp_path / "user_memories.json"

    memory_repository = UserMemoryRepository(str(user_memory_file))
    memory_repository.save(
        UserMemory(
            platform="instagram",
            external_user_id="user-1",
            stable_facts=["me llamo Marcos"],
            preferences=["prefiero respuestas cortas"],
            working_memory_buffer=[
                "The user is tired but wants to keep making progress with the project."
            ],
            conversation_summary="The user wants practical progress on the project.",
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

