import json
from pathlib import Path

from app.models.external_trace import ExternalTraceRecord

class ExternalTraceRepository:
    def __init__(self, file_path: str = "data/external_traces.json") -> None:
        self.file_path = Path(file_path)
        self._ensure_storage_exists()

    def _ensure_storage_exists(self) -> None:
        self.file_path.parent.mkdir(parents=True, exist_ok=True)

        if not self.file_path.exists():
            self.file_path.write_text("[]", encoding="utf-8")

    def load_records(self) -> list[ExternalTraceRecord]:
        raw_data = json.loads(self.file_path.read_text(encoding="utf-8"))
        return [ExternalTraceRecord.from_dict(item) for item in raw_data]
    
    def save_records(self, record: ExternalTraceRecord) -> None:
        records = self.load_records()
        records.append(record)

        serialized = [item.to_dict() for item in records]

        self.file_path.write_text(
            json.dumps(serialized, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def has_processed_provider_message(self, provider_message_id: str | None) -> bool:
        if not provider_message_id:
            return False

        records = self.load_records()
        return any(
            record.provider_message_id == provider_message_id
            and record.inbound_status == "processed"
            for record in records
        )
    
    def list_recent_records(self, limit: int = 20, platform: str | None = None):
        records = self.load_records()

        if platform is not None:
            records = [record for record in records if record.platform==platform]

        return list(reversed(records[-limit:]))
    

    def summarize_records(self, platform: str | None = None) -> dict:
        records = self.load_records()

        if platform is not None:
            records = [record for record in records if record.platform==platform]

        return {
            "platform": platform,
            "total": len(records),
            "inbound_status_counts": self._count_by_field(records, "inbound_status"),
            "outbound_status_counts": self._count_by_field(records, "outbound_status"),
            "operational_status_counts": self._count_by_field(records, "operational_status"),
            "operational_error_type_counts": self._count_by_field(records, "operational_error_type"),
        }
    

    def _count_by_field(self, records: list[ExternalTraceRecord], field_name: str) -> dict[str,int]:
        counts: dict[str, int] = {}
        
        for record in records:
            value = getattr(record, field_name)
            key = value if value is not None else "none"
            counts[key] = counts.get(key,0) + 1


        return counts 



