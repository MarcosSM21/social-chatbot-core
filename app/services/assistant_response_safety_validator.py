from dataclasses import dataclass
import re


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

        original_text = cleaned_text
        cleaned_text = self._strip_stage_direction_artifacts(cleaned_text)

        if not cleaned_text:
            return AssistantResponseSafetyResult(
                status="blocked",
                detail="Assistant response became empty after removing stage-direction artifacts.",
                safe_text=self.empty_fallback_text,
                matched_rule="stage_direction_cleanup_empty",
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

        if cleaned_text != original_text:
            return AssistantResponseSafetyResult(
                status="adjusted",
                detail="Assistant response contained stage-direction artifacts that were removed.",
                safe_text=cleaned_text,
                matched_rule="stage_direction_artifact",
            )

        return AssistantResponseSafetyResult(
            status="passed",
            detail="Assistant response passed safety validation.",
            safe_text=cleaned_text,
            matched_rule=None,
        )
    
    def _strip_stage_direction_artifacts(self, response_text: str) -> str:
        cleaned = response_text.strip()

        leading_patterns = (
            r"^\((?:[^)]{1,120})\)\s*",
            r"^(?:pausa|pause|sonrisa leve|suspiro|suspira|smiles?|smile|pauses?|se rie|se ríe|sonrie|sonríe)\b[\s:.,-]*",
        )

        previous = None
        while cleaned != previous:
            previous = cleaned
            for pattern in leading_patterns:
                cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE).strip()

        cleaned = re.sub(r"\s{2,}", " ", cleaned).strip()

        return cleaned



    def _find_sensitive_marker(self, response_text: str) -> str | None:
        normalized_text = response_text.lower()

        for rule_name, marker in self.sensitive_markers.items():
            if marker.lower() in normalized_text:
                return rule_name

        return None
