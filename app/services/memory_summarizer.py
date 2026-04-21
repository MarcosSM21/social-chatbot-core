import re
from abc import ABC, abstractmethod


MAX_SUMMARY_CHARS = 900


class MemorySummarizer(ABC):
    @abstractmethod
    def summarize(
        self,
        current_summary: str | None,
        user_message: str,
        assistant_message: str,
    ) -> str:
        pass


class RuleBasedMemorySummarizer(MemorySummarizer):
    def summarize(
        self,
        current_summary: str | None,
        user_message: str,
        assistant_message: str,
    ) -> str:
        latest_exchange = self._summarize_latest_exchange(
            user_message=user_message,
            assistant_message=assistant_message,
        )

        if not current_summary:
            return latest_exchange[:MAX_SUMMARY_CHARS]

        combined = f"{current_summary}\n{latest_exchange}"
        return self._trim_summary(combined)

    def _summarize_latest_exchange(
        self,
        user_message: str,
        assistant_message: str,
    ) -> str:
        clean_user_message = user_message.strip()
        clean_assistant_message = assistant_message.strip()
        lowered_user_message = clean_user_message.lower()

        if not clean_user_message and not clean_assistant_message:
            return "There was an empty exchange."

        if self._contains_sensitive_marker(lowered_user_message):
            return "The user mentioned sensitive password or credential information that should not be stored."

        name = self._extract_name(clean_user_message)
        if name:
            return f"The user's name is {name}."

        if lowered_user_message.startswith("prefiero "):
            return f"The user prefers: {clean_user_message}."

        if lowered_user_message.startswith("me gusta "):
            return f"The user likes: {clean_user_message}."

        if lowered_user_message.startswith("no me gusta "):
            return f"The user dislikes: {clean_user_message}."

        if "cansado" in lowered_user_message and "proyecto" in lowered_user_message:
            return "The user is tired but still wants to keep making progress with the project."

        if "proyecto" in lowered_user_message:
            return "The user is thinking about the project and wants practical next steps."

        if "te acuerdas" in lowered_user_message or "recuerdas" in lowered_user_message:
            return "The user asked whether the assistant remembered something from earlier."

        if not clean_assistant_message:
            return f"Recent user context: {clean_user_message}"

        return f"Recent conversation context: {clean_user_message}"

    def _extract_name(self, text: str) -> str | None:
        me_llamo_match = re.search(r"\bme llamo\s+([^,.!?]+)", text, re.IGNORECASE)
        if me_llamo_match:
            return me_llamo_match.group(1).strip()

        mi_nombre_match = re.search(r"\bmi nombre es\s+([^,.!?]+)", text, re.IGNORECASE)
        if mi_nombre_match:
            return mi_nombre_match.group(1).strip()

        return None

    def _contains_sensitive_marker(self, lowered_text: str) -> bool:
        sensitive_markers = [
            "contraseña",
            "password",
            "token",
            "access_token",
            "secret",
            "api key",
            ".env",
            "dni",
            "tarjeta",
            "iban",
            "cuenta bancaria",
        ]

        return any(marker in lowered_text for marker in sensitive_markers)

    def _trim_summary(self, summary: str) -> str:
        if len(summary) <= MAX_SUMMARY_CHARS:
            return summary

        return summary[-MAX_SUMMARY_CHARS:].lstrip()
