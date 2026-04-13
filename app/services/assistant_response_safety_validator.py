from dataclasses import dataclass


@dataclass
class AssistantResponseSafetyResult:
    status: str
    detail: str
    safe_text: str
    matched_rule: str | None = None


class AssistantResponseSafetyValidator:
    max_response_length = 1000

    safe_fallback_text = (
        "Prefiero no compartir detalles internos o sensibles. "
        "Pero puedo ayudarte con otra cosa."
    )

    empty_fallback_text = (
        "Te leo, pero no he podido generar una respuesta clara. "
        "¿Me lo repites?"
    )

    sensitive_markers = {
        "env_file": ".env",
        "instagram_access_token": "INSTAGRAM_ACCESS_TOKEN",
        "instagram_app_secret": "INSTAGRAM_APP_SECRET",
        "webhook_verify_token": "WEBHOOK_VERIFY_TOKEN",
        "instagram_token_prefix": "IGAA",
        "openai_token_prefix": "sk-",
        "system_prompt": "system prompt",
        "hidden_instructions": "hidden instructions",
        "internal_instructions": "internal instructions",
        "developer_message": "developer message",
    }

    def validate(self, response_text: str) -> AssistantResponseSafetyResult:
        cleaned_text = response_text.strip()

        if not cleaned_text:
            return AssistantResponseSafetyResult(
                status="blocked",
                detail="Assistant response was empty.",
                safe_text=self.empty_fallback_text,
                matched_rule="empty_response",
            )
        
        matched_rule = self._find_sensitive_marker(cleaned_text)
        if matched_rule is not None:
            return AssistantResponseSafetyResult(
                status="blocked",
                detail="Assistant response contained a sensitive internal marker.",
                safe_text=self.safe_fallback_text,
                matched_rule=matched_rule,
            )
        
        if len(cleaned_text) > self.max_response_length:
            return AssistantResponseSafetyResult(
                status="adjusted",
                detail="Assistant response was longer than the configured safety limit.",
                safe_text=cleaned_text[: self.max_response_length].rstrip() + "...",
                matched_rule="max_response_length",
            )
        
        return AssistantResponseSafetyResult(
            status="passed",
            detail="Assistant response passed safety validation.",
            safe_text=cleaned_text,
            matched_rule=None,
        )

    def _find_sensitive_marker(self, response_text: str) -> str | None:
        normalized_text = response_text.lower()

        for rule_name, marker in self.sensitive_markers.items():
            if marker.lower() in normalized_text:
                return rule_name

        return None
