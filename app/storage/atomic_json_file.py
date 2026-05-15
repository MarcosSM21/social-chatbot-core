import json
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any


def read_json_file(file_path: Path, default: Any) -> Any:
    try:
        if not file_path.exists():
            return default

        raw_text = file_path.read_text(encoding="utf-8").strip()
        if not raw_text:
            return default

        return json.loads(raw_text)
    except (json.JSONDecodeError, OSError):
        return default


def atomic_write_json_file(file_path: Path, data: Any) -> None:
    file_path.parent.mkdir(parents=True, exist_ok=True)

    with NamedTemporaryFile(
        "w",
        encoding="utf-8",
        dir=file_path.parent,
        delete=False,
    ) as temp_file:
        json.dump(data, temp_file, ensure_ascii=False, indent=2)
        temp_file.write("\n")
        temp_path = Path(temp_file.name)

    temp_path.replace(file_path)
