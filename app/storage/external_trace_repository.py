from pathlib import Path

from app.models.external_trace import ExternalTraceRecord
from app.storage.atomic_json_file import atomic_write_json_file, read_json_file
from app.storage.file_lock_registry import get_file_lock


class ExternalTraceRepository:
    def __init__(self, file_path: str = "data/external_traces.json") -> None:
        self.file_path = Path(file_path)
        self._file_lock = get_file_lock(self.file_path)
        self._ensure_storage_exists()

    def _ensure_storage_exists(self) -> None:
        self.file_path.parent.mkdir(parents=True, exist_ok=True)

        if not self.file_path.exists():
            atomic_write_json_file(self.file_path, [])

    def _load_records_unlocked(self) -> list[ExternalTraceRecord]:
        raw_data = read_json_file(self.file_path, [])
        return [ExternalTraceRecord.from_dict(item) for item in raw_data]

    def _write_records_unlocked(self, records: list[ExternalTraceRecord]) -> None:
        serialized = [item.to_dict() for item in records]
        atomic_write_json_file(self.file_path, serialized)

    def load_records(self) -> list[ExternalTraceRecord]:
        with self._file_lock:
            return self._load_records_unlocked()

    def save_records(self, record: ExternalTraceRecord) -> None:
        with self._file_lock:
            records = self._load_records_unlocked()
            records.append(record)
            self._write_records_unlocked(records)

    def has_processed_provider_message(self, provider_message_id: str | None) -> bool:
        if not provider_message_id:
            return False

        with self._file_lock:
            records = self._load_records_unlocked()
            return any(
                record.provider_message_id == provider_message_id
                and record.inbound_status == "processed"
                for record in records
            )

    def list_recent_records(self, limit: int = 20, platform: str | None = None):
        with self._file_lock:
            records = self._load_records_unlocked()

        if platform is not None:
            records = [record for record in records if record.platform == platform]

        return list(reversed(records[-limit:]))

    def summarize_records(self, platform: str | None = None) -> dict:
        with self._file_lock:
            records = self._load_records_unlocked()

        if platform is not None:
            records = [record for record in records if record.platform == platform]

        return {
            "platform": platform,
            "total": len(records),
            "inbound_status_counts": self._count_by_field(records, "inbound_status"),
            "outbound_status_counts": self._count_by_field(records, "outbound_status"),
            "operational_status_counts": self._count_by_field(records, "operational_status"),
            "operational_error_type_counts": self._count_by_field(records, "operational_error_type"),
        }

    def _count_by_field(self, records: list[ExternalTraceRecord], field_name: str) -> dict[str, int]:
        counts: dict[str, int] = {}

        for record in records:
            value = getattr(record, field_name)
            key = value if value is not None else "none"
            counts[key] = counts.get(key, 0) + 1

        return counts
