from app.core.settings import Settings


def test_settings_no_longer_exposes_global_style_fields(monkeypatch) -> None:
    monkeypatch.setenv("STYLE_PRESET", "short_direct_calm")
    monkeypatch.setenv("STYLE_TONE", "calm")
    monkeypatch.setenv("STYLE_RESPONSE_LENGTH", "short")

    settings = Settings.from_env()

    assert not hasattr(settings, "style_preset")
    assert not hasattr(settings, "style_persona_hint")
    assert not hasattr(settings, "style_tone")
    assert not hasattr(settings, "style_response_length")
    assert not hasattr(settings, "style_directness")
    assert not hasattr(settings, "style_warmth")
    assert not hasattr(settings, "style_formality")
    assert not hasattr(settings, "style_rhythm")
    assert not hasattr(settings, "style_empathy")
