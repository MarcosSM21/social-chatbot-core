from dataclasses import dataclass

@dataclass
class ChatMessage:
    role: str
    content: str

@dataclass
class ChatTurn:
    user_message: ChatMessage
    assistant_message: ChatMessage

