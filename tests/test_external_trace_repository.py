from app.models.external_trace import ExternalTraceRecord
from app.storage.external_trace_repository import ExternalTraceRepository


def build_trace(
    platform: str,
    message_id: str,
    inbound_status: str = "processed",
    outbound_status: str | None = "sent",
    operational_status: str | None = "ok",
    operational_error_type: str | None = None,
) -> ExternalTraceRecord:
    return ExternalTraceRecord(
        platform=platform,
        external_conversation_id=f"conversation-{message_id}",
        external_user_id=f"user-{message_id}",
        internal_session_id=None,
        incoming_message_text=f"message {message_id}",
        outgoing_message_text=None,
        inbound_status=inbound_status,
        outbound_status=outbound_status,
        detail="test trace",
        provider_message_id=message_id,
        operational_status=operational_status,
        operational_error_type=operational_error_type,
    )



def test_list_recent_records_returns_newest_first(tmp_path) -> None:
    repository = ExternalTraceRepository(str(tmp_path / "external_traces.json"))

    repository.save_records(build_trace("instagram", "mid-1"))
    repository.save_records(build_trace("instagram", "mid-2"))
    repository.save_records(build_trace("instagram", "mid-3"))

    records = repository.list_recent_records(limit=2)

    assert [record.provider_message_id for record in records] == ["mid-3", "mid-2"]


def test_list_recent_records_can_filter_by_platform(tmp_path) -> None:
    repository = ExternalTraceRepository(str(tmp_path / "external_traces.json"))

    repository.save_records(build_trace("instagram", "ig-1"))
    repository.save_records(build_trace("api", "api-1"))
    repository.save_records(build_trace("instagram", "ig-2"))

    records = repository.list_recent_records(limit=10, platform="instagram")

    assert [record.provider_message_id for record in records] == ["ig-2", "ig-1"]

def test_summarize_records_counts_statuses(tmp_path) -> None:
    repository = ExternalTraceRepository(str(tmp_path / "external_traces.json"))

    repository.save_records(
        build_trace(
            platform="instagram",
            message_id="mid-1",
            inbound_status="processed",
            outbound_status="sent",
            operational_status="ok",
        )
    )
    repository.save_records(
        build_trace(
            platform="instagram",
            message_id="mid-2",
            inbound_status="captured",
            outbound_status="not_sent",
            operational_status="bot_disabled",
        )
    )
    repository.save_records(
        build_trace(
            platform="instagram",
            message_id="mid-3",
            inbound_status="processing_failed",
            outbound_status="not_sent",
            operational_status="processing_failed",
            operational_error_type="generation_provider_error",
        )
    )

    summary = repository.summarize_records(platform="instagram")

    assert summary["platform"] == "instagram"
    assert summary["total"] == 3
    assert summary["inbound_status_counts"] == {
        "processed": 1,
        "captured": 1,
        "processing_failed": 1,
    }
    assert summary["outbound_status_counts"] == {
        "sent": 1,
        "not_sent": 2,
    }
    assert summary["operational_status_counts"] == {
        "ok": 1,
        "bot_disabled": 1,
        "processing_failed": 1,
    }
    assert summary["operational_error_type_counts"] == {
        "none": 2,
        "generation_provider_error": 1,
    }


def test_summarize_records_can_filter_by_platform(tmp_path) -> None:
    repository = ExternalTraceRepository(str(tmp_path / "external_traces.json"))

    repository.save_records(build_trace("instagram", "ig-1"))
    repository.save_records(build_trace("api", "api-1"))
    repository.save_records(build_trace("instagram", "ig-2"))

    summary = repository.summarize_records(platform="instagram")

    assert summary["platform"] == "instagram"
    assert summary["total"] == 2
    assert summary["inbound_status_counts"] == {"processed": 2}
