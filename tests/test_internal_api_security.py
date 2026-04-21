import pytest
from fastapi import HTTPException

from app.api import main as api_main


def test_require_internal_api_key_accepts_valid_key(monkeypatch) -> None:
    monkeypatch.setattr(api_main.settings, "internal_api_key", "secret-key")

    result = api_main.require_internal_api_key(
        x_internal_api_key="secret-key",
    )

    assert result is None


def test_require_internal_api_key_rejects_missing_key(monkeypatch) -> None:
    monkeypatch.setattr(api_main.settings, "internal_api_key", "secret-key")

    with pytest.raises(HTTPException) as exc_info:
        api_main.require_internal_api_key(
            x_internal_api_key=None,
        )

    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == "Invalid internal API key"


def test_require_internal_api_key_rejects_wrong_key(monkeypatch) -> None:
    monkeypatch.setattr(api_main.settings, "internal_api_key", "secret-key")

    with pytest.raises(HTTPException) as exc_info:
        api_main.require_internal_api_key(
            x_internal_api_key="wrong-key",
        )

    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == "Invalid internal API key"
