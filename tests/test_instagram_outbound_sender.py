import requests

from app.core.settings import Settings
from app.models.outbound import OutboundChannelMessage
from app.outbound.instagram_sender import InstagramOutboundSender


class FakeSuccessfulResponse:
    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict:
        return {"message_id": "outbound-mid-1"}


class FakeInvalidJsonResponse:
    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict:
        raise ValueError("invalid json")


def build_settings() -> Settings:
    settings = Settings.from_env()
    settings.instagram_api_version = "v25.0"
    settings.instagram_ig_user_id = "ig-user-1"
    settings.instagram_access_token = "test-token"
    return settings


def build_message() -> OutboundChannelMessage:
    return OutboundChannelMessage(
        platform="instagram",
        conversation_id="conversation-1",
        user_id="recipient-1",
        message_text="hola",
    )


def test_instagram_sender_fails_without_ig_user_id() -> None:
    settings = build_settings()
    settings.instagram_ig_user_id = ""

    result = InstagramOutboundSender(settings).send(build_message())

    assert result.status == "failed"
    assert result.external_message_id is None
    assert "INSTAGRAM_IG_USER_ID" in result.detail


def test_instagram_sender_fails_without_access_token() -> None:
    settings = build_settings()
    settings.instagram_access_token = ""

    result = InstagramOutboundSender(settings).send(build_message())

    assert result.status == "failed"
    assert result.external_message_id is None
    assert "INSTAGRAM_ACCESS_TOKEN" in result.detail


def test_instagram_sender_fails_without_recipient_user_id() -> None:
    message = build_message()
    message.user_id = ""

    result = InstagramOutboundSender(build_settings()).send(message)

    assert result.status == "failed"
    assert result.external_message_id is None
    assert "recipient user_id" in result.detail


def test_instagram_sender_fails_with_empty_message_text() -> None:
    message = build_message()
    message.message_text = "   "

    result = InstagramOutboundSender(build_settings()).send(message)

    assert result.status == "failed"
    assert result.external_message_id is None
    assert "empty" in result.detail


def test_instagram_sender_returns_failed_when_request_fails(monkeypatch) -> None:
    def fake_post(*args, **kwargs):
        raise requests.RequestException("network down")

    monkeypatch.setattr("app.outbound.instagram_sender.requests.post", fake_post)

    result = InstagramOutboundSender(build_settings()).send(build_message())

    assert result.status == "failed"
    assert result.external_message_id is None
    assert "network down" in result.detail


def test_instagram_sender_returns_sent_with_message_id(monkeypatch) -> None:
    def fake_post(*args, **kwargs):
        return FakeSuccessfulResponse()

    monkeypatch.setattr("app.outbound.instagram_sender.requests.post", fake_post)

    result = InstagramOutboundSender(build_settings()).send(build_message())

    assert result.status == "sent"
    assert result.external_message_id == "outbound-mid-1"


def test_instagram_sender_handles_invalid_success_response_json(monkeypatch) -> None:
    def fake_post(*args, **kwargs):
        return FakeInvalidJsonResponse()

    monkeypatch.setattr("app.outbound.instagram_sender.requests.post", fake_post)

    result = InstagramOutboundSender(build_settings()).send(build_message())

    assert result.status == "sent"
    assert result.external_message_id is None
    assert "response JSON could not be parsed" in result.detail
