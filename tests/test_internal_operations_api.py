from app.api import main as api_main
from app.models.external_trace import ExternalTraceRecord


class FakeExternalTraceRepository:
    def list_recent_records(self, limit: int = 20, platform: str | None = None):
        records = [
            ExternalTraceRecord(
                platform="instagram",
                external_conversation_id="conversation-1",
                external_user_id="user-1",
                internal_session_id="session-1",
                incoming_message_text="hola",
                outgoing_message_text="ey",
                inbound_status="processed",
                outbound_status="sent",
                detail="ok",
                provider_message_id="mid-1",
                outbound_message_id="out-1",
                operational_status="ok",
                memory_loaded=True,
                memory_updated=False,
                style_preset="short_direct_calm",
                safety_validation_status="passed",
            )
        ]

        if platform is not None:
            records = [
                record
                for record in records
                if record.platform == platform
            ]

        return records[:limit]
    
    def summarize_records(self, platform: str | None = None):
        return {
            "platform": platform,
            "total": 3,
            "inbound_status_counts": {
                "processed": 1,
                "captured": 1,
                "ignored": 1,
            },
            "outbound_status_counts": {
                "sent": 1,
                "not_sent": 1,
                "none": 1,
            },
            "operational_status_counts": {
                "ok": 1,
                "bot_disabled": 1,
                "none": 1,
            },
            "operational_error_type_counts": {
                "none": 3,
            },
        }



def test_list_recent_operational_events(monkeypatch) -> None:
    monkeypatch.setattr(
        api_main,
        "ExternalTraceRepository",
        FakeExternalTraceRepository,
    )

    response = api_main.list_recent_operational_events(
        limit=10,
        platform="instagram",
        _=None,
    )

    assert response.count == 1

    event = response.events[0]

    assert event.platform == "instagram"
    assert event.external_user_id == "user-1"
    assert event.incoming_message_text == "hola"
    assert event.outgoing_message_text == "ey"
    assert event.inbound_status == "processed"
    assert event.outbound_status == "sent"
    assert event.operational_status == "ok"
    assert event.memory_loaded is True
    assert event.safety_validation_status == "passed"


def test_get_operational_summary(monkeypatch) -> None:
    monkeypatch.setattr(
        api_main,
        "ExternalTraceRepository",
        FakeExternalTraceRepository,
    )

    response = api_main.get_operational_summary(platform="instagram", _=None)

    assert response.platform == "instagram"
    assert response.total == 3
    assert response.inbound_status_counts == {
        "processed": 1,
        "captured": 1,
        "ignored": 1,
    }
    assert response.outbound_status_counts == {
        "sent": 1,
        "not_sent": 1,
        "none": 1,
    }
    assert response.operational_status_counts == {
        "ok": 1,
        "bot_disabled": 1,
        "none": 1,
    }
    assert response.operational_error_type_counts == {
        "none": 3,
    }

