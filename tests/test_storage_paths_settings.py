from app.core.settings import Settings


def test_storage_paths_settings_have_expected_defaults(monkeypatch) -> None:
    monkeypatch.delenv("JSON_USER_MEMORY_PATH", raising=False)
    monkeypatch.delenv("CHAT_HISTORY_PATH", raising=False)
    monkeypatch.delenv("EXTERNAL_TRACES_PATH", raising=False)
    monkeypatch.delenv("PROVIDER_RAW_PAYLOADS_PATH", raising=False)

    settings = Settings.from_env()

    assert settings.json_user_memory_path == "data/user_memories.json"
    assert settings.chat_history_path == "data/chat_history.json"
    assert settings.external_traces_path == "data/external_traces.json"
    assert settings.provider_raw_payloads_path == "data/provider_raw_payloads.json"


def test_storage_paths_settings_can_be_loaded_from_env(monkeypatch) -> None:
    monkeypatch.setenv("JSON_USER_MEMORY_PATH", "runtime/memory.json")
    monkeypatch.setenv("CHAT_HISTORY_PATH", "runtime/chat_history.json")
    monkeypatch.setenv("EXTERNAL_TRACES_PATH", "runtime/external_traces.json")
    monkeypatch.setenv("PROVIDER_RAW_PAYLOADS_PATH", "runtime/provider_raw_payloads.json")

    settings = Settings.from_env()

    assert settings.json_user_memory_path == "runtime/memory.json"
    assert settings.chat_history_path == "runtime/chat_history.json"
    assert settings.external_traces_path == "runtime/external_traces.json"
    assert settings.provider_raw_payloads_path == "runtime/provider_raw_payloads.json"
