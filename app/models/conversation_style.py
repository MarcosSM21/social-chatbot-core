from dataclasses import asdict, dataclass, field

@dataclass
class ConversationStyle:
    persona_hint: str
    tone: str
    response_length: str
    directness: str
    warmth: str
    formality: str
    rhythm: str
    empathy: str

    def to_dict(self) -> dict:
        return asdict(self)
    

    @classmethod
    def from_preset(cls, preset_name: str) -> "ConversationStyle":
        normalized = preset_name.strip().lower()

        if normalized == "short_direct_calm":
            return cls(
                persona_hint="A guy in his twenties speaking naturally and casually.",
                tone="calm",
                response_length="short",
                directness="high",
                warmth="medium",
                formality="low",
                rhythm="natural",
                empathy="high",
            )

        if normalized == "warm_supportive":
            return cls(
                persona_hint="A warm and emotionally attentive young adult speaking naturally.",
                tone="warm",
                response_length="medium",
                directness="medium",
                warmth="high",
                formality="low",
                rhythm="soft",
                empathy="high",
            )

        if normalized == "formal_clear":
            return cls(
                persona_hint="A clear and respectful assistant with a more professional tone.",
                tone="clear",
                response_length="medium",
                directness="medium",
                warmth="medium",
                formality="high",
                rhythm="measured",
                empathy="medium",
            )

        return cls.default()

    @classmethod
    def default(cls) -> "ConversationStyle":
        return cls.from_preset("short_direct_calm")
    

