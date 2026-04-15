from dataclasses import dataclass, asdict, field


@dataclass
class UserMemory:
    platform: str
    external_user_id: str
    user_profile: str | None = None
    conversation_summary: str | None = None
    stable_facts: list[str] = field(default_factory=list)
    preferences: list[str] = field(default_factory=list)
    relationship_notes: list[str] = field(default_factory=list)
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
            stable_facts=data.get("stable_facts", []),
            preferences=data.get("preferences", []),
            relationship_notes=data.get("relationship_notes", []),
            updated_at=data.get("updated_at"),
        )
