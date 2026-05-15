from pathlib import Path

from app.models.pending_outbound import PendingOutboundMessage
from app.storage.atomic_json_file import atomic_write_json_file, read_json_file
from app.storage.file_lock_registry import get_file_lock


class PendingOutboundRepository:
    def __init__(self, file_path: str = "data/instagram_pending_outbound.json") -> None:
        self.file_path = Path(file_path)
        self._file_lock = get_file_lock(self.file_path)
        self._ensure_storage_exists()

    def _ensure_storage_exists(self) -> None:
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.file_path.exists():
            atomic_write_json_file(self.file_path, [])

    def _load_records_unlocked(self) -> list[PendingOutboundMessage]:
        raw_data = read_json_file(self.file_path, [])
        return [PendingOutboundMessage.from_dict(item) for item in raw_data]

    def _write_records_unlocked(self, records: list[PendingOutboundMessage]) -> None:
        atomic_write_json_file(
            self.file_path,
            [record.to_dict() for record in records],
        )

    def list_records(self) -> list[PendingOutboundMessage]:
        with self._file_lock:
            return self._load_records_unlocked()

    def add_record(self, record: PendingOutboundMessage) -> None:
        with self._file_lock:
            records = self._load_records_unlocked()
            records = [item for item in records if item.pending_id != record.pending_id]
            records.append(record)
            self._write_records_unlocked(records)

    def remove_record(self, pending_id: str) -> bool:
        with self._file_lock:
            records = self._load_records_unlocked()
            remaining = [record for record in records if record.pending_id != pending_id]
            removed = len(remaining) != len(records)
            if removed:
                self._write_records_unlocked(remaining)
            return removed

    def list_due_records(self, now_ts: float) -> list[PendingOutboundMessage]:
        with self._file_lock:
            records = self._load_records_unlocked()
            return [
                record
                for record in records
                if record.status == "pending" and record.send_at_ts <= now_ts
            ]

    def list_pending_bundle_keys(self) -> list[str]:
        with self._file_lock:
            records = self._load_records_unlocked()
            bundle_keys: list[str] = []
            for record in records:
                if record.status != "pending":
                    continue
                if record.bundle_key not in bundle_keys:
                    bundle_keys.append(record.bundle_key)
            return bundle_keys
