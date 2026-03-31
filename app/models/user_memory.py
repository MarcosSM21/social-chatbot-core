from dataclasses import dataclass, asdict

@dataclass
class UserMemory:
    platform: str
    external_user_id: str
    user_profile: str | None = None
    conversation_summary: str | None = None
    updated_at: str | None = None

    def to_dict(self):
        return asdict(self) 
    
    @classmethod
    def from_dict(cls, data: dict) -> "UserMemory":
        return cls(
            platform=data.get("platform"),
            external_user_id=data.get("external_user_id"),
            user_profile=data.get("user_profile"),
            conversation_summary=data.get("conversation_summary"),
            updated_at=data.get("updated_at")
        )