import json
from pathlib import Path

from app.models.provider_raw_payload import ProviderRawPayloadRecord


class ProviderRawPayloadRepository:
    def __init__(self, file_path: str = "data/provider_raw_payloads.json") -> None:
        self.file_path = Path(file_path)
        self._ensure_storage_exists()

    def _ensure_storage_exists(self) -> None:
        self.file_path.parent.mkdir(parents=True, exist_ok=True)

        if not self.file_path.exists():
            self.file_path.write_text("[]", encoding="utf-8")

    def load_records(self) -> list[ProviderRawPayloadRecord]:
        raw_data = json.loads(self.file_path.read_text(encoding="utf-8"))
        return [ProviderRawPayloadRecord.from_dict(item) for item in raw_data]

    def save_record(self, record: ProviderRawPayloadRecord) -> None:
        records = self.load_records()
        records.append(record)

        serialized = [item.to_dict() for item in records]
        self.file_path.write_text(
            json.dumps(serialized, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )