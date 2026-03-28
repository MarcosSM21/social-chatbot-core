from dataclasses import asdict, dataclass
from typing import Any


@dataclass
class ProviderRawPayloadRecord:
    provider: str
    endpoint: str
    payload: dict[str, Any]

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "ProviderRawPayloadRecord":
        return cls(
            provider=data["provider"],
            endpoint=data["endpoint"],
            payload=data["payload"],
        )