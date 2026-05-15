from pathlib import Path
from threading import Lock


_FILE_LOCKS: dict[Path, Lock] = {}
_REGISTRY_LOCK = Lock()


def get_file_lock(file_path: Path) -> Lock:
    normalized_path = file_path.resolve()

    with _REGISTRY_LOCK:
        lock = _FILE_LOCKS.get(normalized_path)
        if lock is None:
            lock = Lock()
            _FILE_LOCKS[normalized_path] = lock
        return lock
