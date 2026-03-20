from dataclasses import asdict, dataclass

@dataclass
class ConversationMapping:
    platform: str
    external_conversation_id: str
    external_user_id: str
    internal_session_id: str

    def to_dict(self) -> dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> "ConversationMapping":
        return cls(
            platform=data["platform"],
            external_conversation_id=data["external_conversation_id"],
            external_user_id=data["external_user_id"],
            internal_session_id=data["internal_session_id"]
        )
    
    # Este modelo representa esto:
    #   (instagram, ig-thread-001, ig-user-999) -> 7d2b...-uuid-interno