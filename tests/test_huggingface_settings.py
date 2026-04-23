from app.core.settings import Settings


def test_huggingface_settings_have_safe_defaults(monkeypatch) -> None:
    monkeypatch.delenv("HUGGINGFACE_MODEL_ID", raising=False)
    monkeypatch.delenv("HUGGINGFACE_DEVICE", raising=False)
    monkeypatch.delenv("HUGGINGFACE_MAX_NEW_TOKENS", raising=False)
    monkeypatch.delenv("HUGGINGFACE_TEMPERATURE", raising=False)

    settings = Settings.from_env()

    assert settings.huggingface_model_id == ""
    assert settings.huggingface_device == "cpu"
    assert settings.huggingface_max_new_tokens == 150
    assert settings.huggingface_temperature == 0.7


def test_huggingface_settings_can_be_loaded_from_env(monkeypatch) -> None:
    monkeypatch.setenv("HUGGINGFACE_MODEL_ID", "TinyLlama/TinyLlama-1.1B-Chat-v1.0")
    monkeypatch.setenv("HUGGINGFACE_DEVICE", "cpu")
    monkeypatch.setenv("HUGGINGFACE_MAX_NEW_TOKENS", "96")
    monkeypatch.setenv("HUGGINGFACE_TEMPERATURE", "0.3")

    settings = Settings.from_env()

    assert settings.huggingface_model_id == "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
    assert settings.huggingface_device == "cpu"
    assert settings.huggingface_max_new_tokens == 96
    assert settings.huggingface_temperature == 0.3
