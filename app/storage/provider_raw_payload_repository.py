from pathlib import Path

from app.models.provider_raw_payload import ProviderRawPayloadRecord
from app.storage.atomic_json_file import atomic_write_json_file, read_json_file
from app.storage.file_lock_registry import get_file_lock


class ProviderRawPayloadRepository:
    def __init__(self, file_path: str = "data/provider_raw_payloads.json") -> None:
        self.file_path = Path(file_path)
        self._file_lock = get_file_lock(self.file_path)
        self._ensure_storage_exists()

    def _ensure_storage_exists(self) -> None:
        self.file_path.parent.mkdir(parents=True, exist_ok=True)

        if not self.file_path.exists():
            atomic_write_json_file(self.file_path, [])

    def _load_records_unlocked(self) -> list[ProviderRawPayloadRecord]:
        raw_data = read_json_file(self.file_path, [])
        return [ProviderRawPayloadRecord.from_dict(item) for item in raw_data]

    def _write_records_unlocked(self, records: list[ProviderRawPayloadRecord]) -> None:
        serialized = [item.to_dict() for item in records]
        atomic_write_json_file(self.file_path, serialized)

    def load_records(self) -> list[ProviderRawPayloadRecord]:
        with self._file_lock:
            return self._load_records_unlocked()

    def save_record(self, record: ProviderRawPayloadRecord) -> None:
        with self._file_lock:
            records = self._load_records_unlocked()
            records.append(record)
            self._write_records_unlocked(records)
