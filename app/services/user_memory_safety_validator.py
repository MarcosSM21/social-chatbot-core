from dataclasses import dataclass


@dataclass
class UserMemorySafetyResult:
    status: str
    detail: str
    matched_rule: str | None = None


class UserMemorySafetyValidator:
    sensitive_markers = {
        "password_es": "contraseña",
        "password_en": "password",
        "token": "token",
        "access_token": "access_token",
        "secret": "secret",
        "api_key": "api key",
        "env_file": ".env",
        "dni": "dni",
        "credit_card_es": "tarjeta",
        "iban": "iban",
        "bank_account": "cuenta bancaria",
    }

    def validate_candidate_memory(self, candidate_text: str | None) -> UserMemorySafetyResult:
        if not candidate_text:
            return UserMemorySafetyResult(
                status="passed",
                detail="No candidate memory to validate.",
                matched_rule=None,
            )

        normalized_text = candidate_text.lower()

        for rule_name, marker in self.sensitive_markers.items():
            if marker.lower() in normalized_text:
                return UserMemorySafetyResult(
                    status="blocked",
                    detail="Candidate memory contained a sensitive marker.",
                    matched_rule=rule_name,
                )

        return UserMemorySafetyResult(
            status="passed",
            detail="Candidate memory passed safety validation.",
            matched_rule=None,
        )
