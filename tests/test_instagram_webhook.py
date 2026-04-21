import hashlib
import hmac
import json

import pytest
from fastapi import HTTPException

from app.api import main as api_main
from app.channels.http_channel_result import HttpChannelResult
from app.models.chat import ChatMessage, ChatTurn
from app.models.outbound import OutboundChannelMessage
from app.outbound.result import OutboundSendResult
from app.providers.exceptions import GenerationProviderError


class FakeTraceRepository:
    duplicate = False
    records = []

    def has_processed_provider_message(self, provider_message_id):
        return self.duplicate

    def save_records(self, record):
        self.records.append(record)


class FakeRequest:
    def __init__(self, raw_body: bytes, headers: dict[str, str]) -> None:
        self._raw_body = raw_body
        self.headers = headers

    async def body(self) -> bytes:
        return self._raw_body


def sign_payload(raw_body: bytes, app_secret: str) -> str:
    digest = hmac.new(
        app_secret.encode("utf-8"),
        msg=raw_body,
        digestmod=hashlib.sha256,
    ).hexdigest()
    return f"sha256={digest}"


def build_payload(message_text: str = "hola", message_id: str = "mid-1") -> dict:
    return {
        "object": "instagram",
        "entry": [
            {
                "id": "entry-1",
                "messaging": [
                    {
                        "sender": {"id": "user-1"},
                        "recipient": {"id": "business-1"},
                        "timestamp": 123,
                        "message": {"mid": message_id, "text": message_text},
                    }
                ],
            }
        ],
    }


@pytest.fixture(autouse=True)
def reset_instagram_runtime_controls(monkeypatch) -> None:
    monkeypatch.setattr(api_main.settings, "bot_enabled", True)
    monkeypatch.setattr(api_main.settings, "instagram_allowed_user_ids", [])
    monkeypatch.setattr(api_main.settings, "instagram_reply_cooldown_seconds", 0)
    api_main._instagram_last_reply_by_user.clear()



def test_instagram_webhook_verification(monkeypatch) -> None:
    monkeypatch.setattr(api_main.settings, "webhook_verify_token", "verify-token")

    response = api_main.verify_instagram_webhook_messages(
        hub_mode="subscribe",
        hub_token="verify-token",
        hub_challenge="challenge-ok",
    )

    assert response.body == b"challenge-ok"


@pytest.mark.anyio
async def test_instagram_webhook_rejects_invalid_signature(monkeypatch) -> None:
    monkeypatch.setattr(api_main.settings, "instagram_app_secret", "secret")
    raw_body = json.dumps(build_payload()).encode("utf-8")
    request = FakeRequest(
        raw_body=raw_body,
        headers={"X-Hub-Signature-256": "sha256=invalid"},
    )

    with pytest.raises(HTTPException) as exc_info:
        await api_main.receive_instagram_webhook_message(request)

    assert exc_info.value.status_code == 403


@pytest.mark.anyio
async def test_instagram_webhook_accepts_valid_payload_without_network(monkeypatch) -> None:
    FakeTraceRepository.duplicate = False
    FakeTraceRepository.records = []
    monkeypatch.setattr(api_main.settings, "instagram_app_secret", "secret")
    monkeypatch.setattr(api_main, "_store_instagram_raw_payload", lambda raw_payload: None)
    monkeypatch.setattr(api_main, "ExternalTraceRepository", FakeTraceRepository)
    monkeypatch.setattr(api_main.settings, "instagram_reply_cooldown_seconds", 10)
    monkeypatch.setattr(api_main.time, "monotonic", lambda: 500.0)

    def fake_process_and_send(external_event):
        turn = ChatTurn(
            session_id="session-1",
            user_message=ChatMessage(role="user", content=external_event.message_text),
            assistant_message=ChatMessage(role="assistant", content="respuesta"),
            session_metadata={
                "memory_loaded": False,
                "memory_updated": True,
                "style_preset": "short_direct_calm",
                "safety_validation_status": "passed",
            },
        )
        outbound = OutboundChannelMessage(
            platform=external_event.platform,
            conversation_id=external_event.conversation_id,
            user_id=external_event.user_id,
            message_text="respuesta",
        )
        return (
            HttpChannelResult(turn=turn, outbound_message=outbound),
            OutboundSendResult(status="sent", detail="mock sent", external_message_id="out-1"),
        )

    monkeypatch.setattr(api_main, "_process_and_send_external_event", fake_process_and_send)
    


    raw_body = json.dumps(build_payload()).encode("utf-8")
    request = FakeRequest(
        raw_body=raw_body,
        headers={"X-Hub-Signature-256": sign_payload(raw_body, "secret")},
    )
    response = await api_main.receive_instagram_webhook_message(request)

    assert response.status == "accepted"
    assert len(FakeTraceRepository.records) == 1
    assert FakeTraceRepository.records[0].outbound_status == "sent"
    assert FakeTraceRepository.records[0].operational_status == "ok"
    assert FakeTraceRepository.records[0].operational_error_type is None
    assert api_main._instagram_last_reply_by_user["user-1"] == 500.0




@pytest.mark.anyio
async def test_instagram_webhook_ignores_non_text_payload(monkeypatch) -> None:
    FakeTraceRepository.duplicate = False
    FakeTraceRepository.records = []
    monkeypatch.setattr(api_main.settings, "instagram_app_secret", "secret")
    monkeypatch.setattr(api_main, "_store_instagram_raw_payload", lambda raw_payload: None)
    monkeypatch.setattr(api_main, "ExternalTraceRepository", FakeTraceRepository)

    def fail_if_called(external_event):
        raise AssertionError("Non-text payload should not be processed")

    monkeypatch.setattr(api_main, "_process_and_send_external_event", fail_if_called)

    payload = build_payload(message_id="mid-non-text")
    payload["entry"][0]["messaging"][0]["message"].pop("text")
    raw_body = json.dumps(payload).encode("utf-8")
    request = FakeRequest(
        raw_body=raw_body,
        headers={"X-Hub-Signature-256": sign_payload(raw_body, "secret")},
    )
    response = await api_main.receive_instagram_webhook_message(request)

    assert response.status == "ignored"
    assert "No supported text-based DM events found" in response.detail
    assert FakeTraceRepository.records == []


@pytest.mark.anyio
async def test_instagram_webhook_traces_unexpected_sender_failure(monkeypatch) -> None:
    FakeTraceRepository.duplicate = False
    FakeTraceRepository.records = []
    monkeypatch.setattr(api_main.settings, "instagram_app_secret", "secret")
    monkeypatch.setattr(api_main, "_store_instagram_raw_payload", lambda raw_payload: None)
    monkeypatch.setattr(api_main, "ExternalTraceRepository", FakeTraceRepository)

    class FakeChannelAdapter:
        def process_event(self, external_event):
            turn = ChatTurn(
                session_id="session-1",
                user_message=ChatMessage(role="user", content=external_event.message_text),
                assistant_message=ChatMessage(role="assistant", content="respuesta"),
                session_metadata={
                    "memory_loaded": False,
                    "memory_updated": False,
                    "style_preset": "short_direct_calm",
                    "safety_validation_status": "passed",
                },
            )
            outbound = OutboundChannelMessage(
                platform=external_event.platform,
                conversation_id=external_event.conversation_id,
                user_id=external_event.user_id,
                message_text="respuesta",
            )
            return HttpChannelResult(turn=turn, outbound_message=outbound)

    class FailingInstagramSender:
        def __init__(self, settings):
            self.settings = settings

        def send(self, outbound_message):
            raise RuntimeError("sender exploded")

    monkeypatch.setattr(api_main, "build_http_channel_adapter", lambda settings: FakeChannelAdapter())
    monkeypatch.setattr(api_main, "InstagramOutboundSender", FailingInstagramSender)

    raw_body = json.dumps(build_payload()).encode("utf-8")
    request = FakeRequest(
        raw_body=raw_body,
        headers={"X-Hub-Signature-256": sign_payload(raw_body, "secret")},
    )

    response = await api_main.receive_instagram_webhook_message(request)

    assert response.status == "accepted"
    assert len(FakeTraceRepository.records) == 1

    record = FakeTraceRepository.records[0]
    assert record.inbound_status == "processed"
    assert record.outbound_status == "failed"
    assert "sender exploded" in record.detail
    assert record.outbound_message_id is None
    assert record.operational_status == "outbound_failed"
    assert record.operational_error_type == "instagram_outbound_failed"
    assert "sender exploded" in record.operational_detail


@pytest.mark.anyio
async def test_instagram_webhook_ignores_duplicate_provider_message(monkeypatch) -> None:
    FakeTraceRepository.duplicate = True
    FakeTraceRepository.records = []
    monkeypatch.setattr(api_main.settings, "instagram_app_secret", "secret")
    monkeypatch.setattr(api_main, "_store_instagram_raw_payload", lambda raw_payload: None)
    monkeypatch.setattr(api_main, "ExternalTraceRepository", FakeTraceRepository)

    def fail_if_called(external_event):
        raise AssertionError("Duplicate message should not be processed")

    monkeypatch.setattr(api_main, "_process_and_send_external_event", fail_if_called)

    raw_body = json.dumps(build_payload()).encode("utf-8")
    request = FakeRequest(
        raw_body=raw_body,
        headers={"X-Hub-Signature-256": sign_payload(raw_body, "secret")},
    )
    response = await api_main.receive_instagram_webhook_message(request)

    assert response.status == "ignored"
    assert response.detail == "Duplicate provider message ignored."
    assert FakeTraceRepository.records == []


@pytest.mark.anyio
async def test_instagram_webhook_traces_generation_failure_without_retrying(monkeypatch) -> None:
    FakeTraceRepository.duplicate = False
    FakeTraceRepository.records = []
    monkeypatch.setattr(api_main.settings, "instagram_app_secret", "secret")
    monkeypatch.setattr(api_main, "_store_instagram_raw_payload", lambda raw_payload: None)
    monkeypatch.setattr(api_main, "ExternalTraceRepository", FakeTraceRepository)

    def fail_process_and_send(external_event):
        raise GenerationProviderError("provider down")

    monkeypatch.setattr(api_main, "_process_and_send_external_event", fail_process_and_send)

    raw_body = json.dumps(build_payload()).encode("utf-8")
    request = FakeRequest(
        raw_body=raw_body,
        headers={"X-Hub-Signature-256": sign_payload(raw_body, "secret")},
    )

    response = await api_main.receive_instagram_webhook_message(request)

    assert response.status == "accepted"
    assert "processing failed" in response.detail
    assert len(FakeTraceRepository.records) == 1

    record = FakeTraceRepository.records[0]
    assert record.inbound_status == "processing_failed"
    assert record.outbound_status == "not_sent"
    assert record.provider_message_id == "mid-1"
    assert record.outgoing_message_text is None
    assert record.operational_status == "processing_failed"
    assert record.operational_error_type == "generation_provider_error"
    assert "provider down" in record.operational_detail




@pytest.mark.anyio
async def test_instagram_webhook_captures_message_without_reply_when_bot_disabled(monkeypatch) -> None:
    FakeTraceRepository.duplicate = False
    FakeTraceRepository.records = []

    monkeypatch.setattr(api_main.settings, "instagram_app_secret", "secret")
    monkeypatch.setattr(api_main.settings, "bot_enabled", False)
    monkeypatch.setattr(api_main, "_store_instagram_raw_payload", lambda raw_payload: None)
    monkeypatch.setattr(api_main, "ExternalTraceRepository", FakeTraceRepository)

    def fail_if_called(external_event):
        raise AssertionError("Bot disabled mode should not process or send responses")

    monkeypatch.setattr(api_main, "_process_and_send_external_event", fail_if_called)

    raw_body = json.dumps(build_payload(message_text="hola en modo escucha")).encode("utf-8")
    request = FakeRequest(
        raw_body=raw_body,
        headers={"X-Hub-Signature-256": sign_payload(raw_body, "secret")},
    )

    response = await api_main.receive_instagram_webhook_message(request)

    assert response.status == "accepted"
    assert "bot is disabled" in response.detail

    assert len(FakeTraceRepository.records) == 1

    record = FakeTraceRepository.records[0]

    assert record.inbound_status == "captured"
    assert record.outbound_status == "not_sent"
    assert record.incoming_message_text == "hola en modo escucha"
    assert record.outgoing_message_text is None
    assert record.operational_status == "bot_disabled"
    assert record.operational_error_type is None

    monkeypatch.setattr(api_main.settings, "bot_enabled", True)



@pytest.mark.anyio
async def test_instagram_webhook_replies_when_user_is_allowed(monkeypatch) -> None:
    FakeTraceRepository.duplicate = False
    FakeTraceRepository.records = []

    monkeypatch.setattr(api_main.settings, "instagram_app_secret", "secret")
    monkeypatch.setattr(api_main.settings, "instagram_allowed_user_ids", ["user-1"])
    monkeypatch.setattr(api_main, "_store_instagram_raw_payload", lambda raw_payload: None)
    monkeypatch.setattr(api_main, "ExternalTraceRepository", FakeTraceRepository)

    def fake_process_and_send(external_event):
        turn = ChatTurn(
            session_id="session-1",
            user_message=ChatMessage(role="user", content=external_event.message_text),
            assistant_message=ChatMessage(role="assistant", content="respuesta"),
            session_metadata={
                "memory_loaded": False,
                "memory_updated": False,
                "style_preset": "short_direct_calm",
                "safety_validation_status": "passed",
            },
        )
        outbound = OutboundChannelMessage(
            platform=external_event.platform,
            conversation_id=external_event.conversation_id,
            user_id=external_event.user_id,
            message_text="respuesta",
        )
        return (
            HttpChannelResult(turn=turn, outbound_message=outbound),
            OutboundSendResult(status="sent", detail="mock sent", external_message_id="out-1"),
        )

    monkeypatch.setattr(api_main, "_process_and_send_external_event", fake_process_and_send)

    raw_body = json.dumps(build_payload(message_text="hola", message_id="mid-allowed")).encode("utf-8")
    request = FakeRequest(
        raw_body=raw_body,
        headers={"X-Hub-Signature-256": sign_payload(raw_body, "secret")},
    )

    response = await api_main.receive_instagram_webhook_message(request)

    assert response.status == "accepted"
    assert len(FakeTraceRepository.records) == 1
    assert FakeTraceRepository.records[0].outbound_status == "sent"
    assert FakeTraceRepository.records[0].operational_status == "ok"


@pytest.mark.anyio
async def test_instagram_webhook_captures_without_reply_when_user_is_not_allowed(monkeypatch) -> None:
    FakeTraceRepository.duplicate = False
    FakeTraceRepository.records = []

    monkeypatch.setattr(api_main.settings, "instagram_app_secret", "secret")
    monkeypatch.setattr(api_main.settings, "instagram_allowed_user_ids", ["another-user"])
    monkeypatch.setattr(api_main, "_store_instagram_raw_payload", lambda raw_payload: None)
    monkeypatch.setattr(api_main, "ExternalTraceRepository", FakeTraceRepository)

    def fail_if_called(external_event):
        raise AssertionError("Non-allowed users should not be processed or replied to")

    monkeypatch.setattr(api_main, "_process_and_send_external_event", fail_if_called)

    raw_body = json.dumps(build_payload(message_text="hola", message_id="mid-not-allowed")).encode("utf-8")
    request = FakeRequest(
        raw_body=raw_body,
        headers={"X-Hub-Signature-256": sign_payload(raw_body, "secret")},
    )

    response = await api_main.receive_instagram_webhook_message(request)

    assert response.status == "accepted"
    assert "user is not allowed" in response.detail

    assert len(FakeTraceRepository.records) == 1

    record = FakeTraceRepository.records[0]

    assert record.inbound_status == "captured"
    assert record.outbound_status == "not_sent"
    assert record.incoming_message_text == "hola"
    assert record.outgoing_message_text is None
    assert record.operational_status == "user_not_allowed"
    assert record.operational_error_type is None


def test_is_instagram_user_allowed_when_allowlist_is_empty(monkeypatch) -> None:
    monkeypatch.setattr(api_main.settings, "instagram_allowed_user_ids", [])

    assert api_main._is_instagram_user_allowed("user-1") is True


def test_is_instagram_user_allowed_when_user_is_in_allowlist(monkeypatch) -> None:
    monkeypatch.setattr(api_main.settings, "instagram_allowed_user_ids", ["user-1", "user-2"])

    assert api_main._is_instagram_user_allowed("user-1") is True


def test_is_instagram_user_allowed_when_user_is_not_in_allowlist(monkeypatch) -> None:
    monkeypatch.setattr(api_main.settings, "instagram_allowed_user_ids", ["user-2"])

    assert api_main._is_instagram_user_allowed("user-1") is False


def test_is_instagram_user_rate_limited_when_cooldown_is_disabled(monkeypatch) -> None:
    monkeypatch.setattr(api_main.settings, "instagram_reply_cooldown_seconds", 0)
    api_main._instagram_last_reply_by_user["user-1"] = 123.0

    assert api_main._is_instagram_user_rate_limited("user-1") is False


def test_is_instagram_user_rate_limited_when_no_previous_reply(monkeypatch) -> None:
    monkeypatch.setattr(api_main.settings, "instagram_reply_cooldown_seconds", 10)

    assert api_main._is_instagram_user_rate_limited("user-1") is False


def test_is_instagram_user_rate_limited_when_recent_reply_exists(monkeypatch) -> None:
    monkeypatch.setattr(api_main.settings, "instagram_reply_cooldown_seconds", 10)
    monkeypatch.setattr(api_main.time, "monotonic", lambda: 100.0)

    api_main._instagram_last_reply_by_user["user-1"] = 95.0

    assert api_main._is_instagram_user_rate_limited("user-1") is True


def test_is_instagram_user_not_rate_limited_when_cooldown_has_passed(monkeypatch) -> None:
    monkeypatch.setattr(api_main.settings, "instagram_reply_cooldown_seconds", 10)
    monkeypatch.setattr(api_main.time, "monotonic", lambda: 120.0)

    api_main._instagram_last_reply_by_user["user-1"] = 100.0

    assert api_main._is_instagram_user_rate_limited("user-1") is False


def test_remember_instagram_reply_stores_current_time(monkeypatch) -> None:
    monkeypatch.setattr(api_main.settings, "instagram_reply_cooldown_seconds", 10)
    monkeypatch.setattr(api_main.time, "monotonic", lambda: 250.0)

    api_main._remember_instagram_reply("user-1")

    assert api_main._instagram_last_reply_by_user["user-1"] == 250.0


@pytest.mark.anyio
async def test_instagram_webhook_captures_without_reply_when_user_is_rate_limited(monkeypatch) -> None:
    FakeTraceRepository.duplicate = False
    FakeTraceRepository.records = []

    monkeypatch.setattr(api_main.settings, "instagram_app_secret", "secret")
    monkeypatch.setattr(api_main.settings, "instagram_reply_cooldown_seconds", 10)
    monkeypatch.setattr(api_main.time, "monotonic", lambda: 100.0)
    monkeypatch.setattr(api_main, "_store_instagram_raw_payload", lambda raw_payload: None)
    monkeypatch.setattr(api_main, "ExternalTraceRepository", FakeTraceRepository)

    api_main._instagram_last_reply_by_user["user-1"] = 95.0

    def fail_if_called(external_event):
        raise AssertionError("Rate limited users should not be processed or replied to")

    monkeypatch.setattr(api_main, "_process_and_send_external_event", fail_if_called)

    raw_body = json.dumps(build_payload(message_text="otra vez hola", message_id="mid-rate-limited")).encode("utf-8")
    request = FakeRequest(
        raw_body=raw_body,
        headers={"X-Hub-Signature-256": sign_payload(raw_body, "secret")},
    )

    response = await api_main.receive_instagram_webhook_message(request)

    assert response.status == "accepted"
    assert "rate limited" in response.detail

    assert len(FakeTraceRepository.records) == 1

    record = FakeTraceRepository.records[0]

    assert record.inbound_status == "captured"
    assert record.outbound_status == "not_sent"
    assert record.incoming_message_text == "otra vez hola"
    assert record.outgoing_message_text is None
    assert record.operational_status == "rate_limited"
    assert record.operational_error_type is None



