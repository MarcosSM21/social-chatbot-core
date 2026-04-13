from app.channels.instagram_payload_parser import InstagramPayloadParser
from app.models.provider_payloads import InstagramWebhookPayload


def test_parser_captures_messaging_text_event() -> None:
    payload = InstagramWebhookPayload.from_dict(
        {
            "object": "instagram",
            "entry": [
                {
                    "id": "entry-1",
                    "messaging": [
                        {
                            "sender": {"id": "user-1"},
                            "recipient": {"id": "business-1"},
                            "timestamp": 123,
                            "message": {"mid": "mid-1", "text": "hola"},
                        }
                    ],
                }
            ],
        }
    )

    result = InstagramPayloadParser().parse(payload)

    assert result.status == "captured"
    assert result.events[0].provider_message_id == "mid-1"
    assert result.events[0].incoming_message_text == "hola"


def test_parser_captures_changes_text_event() -> None:
    payload = InstagramWebhookPayload.from_dict(
        {
            "object": "instagram",
            "entry": [
                {
                    "id": "entry-1",
                    "changes": [
                        {
                            "field": "messages",
                            "value": {
                                "sender": {"id": "user-1"},
                                "recipient": {"id": "business-1"},
                                "timestamp": "123",
                                "message": {"mid": "mid-2", "text": "hola changes"},
                            },
                        }
                    ],
                }
            ],
        }
    )

    result = InstagramPayloadParser().parse(payload)

    assert result.status == "captured"
    assert result.events[0].provider_message_id == "mid-2"
    assert result.events[0].incoming_message_text == "hola changes"
    assert result.events[0].timestamp == 123


def test_parser_ignores_non_text_message() -> None:
    payload = InstagramWebhookPayload.from_dict(
        {
            "object": "instagram",
            "entry": [
                {
                    "id": "entry-1",
                    "messaging": [
                        {
                            "sender": {"id": "user-1"},
                            "recipient": {"id": "business-1"},
                            "message": {"mid": "mid-3"},
                        }
                    ],
                }
            ],
        }
    )

    result = InstagramPayloadParser().parse(payload)

    assert result.status == "ignored"
    assert result.events[0].provider_message_id == "mid-3"


def test_parser_ignores_echo_message() -> None:
    payload = InstagramWebhookPayload.from_dict(
        {
            "object": "instagram",
            "entry": [
                {
                    "id": "entry-1",
                    "messaging": [
                        {
                            "sender": {"id": "business-1"},
                            "recipient": {"id": "user-1"},
                            "message": {
                                "mid": "mid-4",
                                "text": "echo",
                                "is_echo": True,
                            },
                        }
                    ],
                }
            ],
        }
    )

    result = InstagramPayloadParser().parse(payload)

    assert result.status == "ignored"
    assert result.events[0].detail == "Echo message ignored."


def test_parser_ignores_event_missing_sender_or_recipient() -> None:
    payload = InstagramWebhookPayload.from_dict(
        {
            "object": "instagram",
            "entry": [
                {
                    "id": "entry-1",
                    "changes": [
                        {
                            "field": "messages",
                            "value": {
                                "sender": None,
                                "recipient": {"id": "business-1"},
                                "message": {"mid": "mid-5", "text": "hola"},
                            },
                        }
                    ],
                }
            ],
        }
    )

    result = InstagramPayloadParser().parse(payload)

    assert result.status == "ignored"
    assert "missing sender or recipient" in result.events[0].detail
