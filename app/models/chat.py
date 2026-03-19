from dataclasses import asdict, dataclass

@dataclass
class ChatMessage:
    role: str
    content: str

    def to_dict(self) -> dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) ->"ChatMessage":
        return cls(
            role=data['role'], 
            content=data['content']
            )

@dataclass
class ChatTurn:
    user_message: ChatMessage
    assistant_message: ChatMessage

    def to_dict(self) -> dict:
        return {
            "user_message": self.user_message.to_dict(),
            "assistant_message": self.assistant_message.to_dict()
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "ChatTurn":
        return cls(
            user_message=ChatMessage.from_dict(data['user_message']),
            assistant_message=ChatMessage.from_dict(data['assistant_message'])
        )
