from app.services.assistant_response_safety_validator import (
    AssistantResponseSafetyValidator,
)
from app.services.user_memory_safety_validator import UserMemorySafetyValidator


def test_assistant_response_safety_allows_normal_text() -> None:
    result = AssistantResponseSafetyValidator().validate("hola, todo bien")

    assert result.status == "passed"
    assert result.safe_text == "hola, todo bien"
    assert result.matched_rule is None


def test_assistant_response_safety_blocks_empty_text() -> None:
    result = AssistantResponseSafetyValidator().validate("   ")

    assert result.status == "blocked"
    assert result.matched_rule == "empty_response"
    assert result.safe_text


def test_assistant_response_safety_blocks_sensitive_marker() -> None:
    result = AssistantResponseSafetyValidator().validate("INSTAGRAM_ACCESS_TOKEN=secret")

    assert result.status == "blocked"
    assert result.matched_rule == "instagram_access_token"


def test_assistant_response_safety_adjusts_long_text() -> None:
    result = AssistantResponseSafetyValidator().validate("a" * 1100)

    assert result.status == "adjusted"
    assert result.matched_rule == "max_response_length"
    assert len(result.safe_text) <= AssistantResponseSafetyValidator.max_response_length + 3


def test_user_memory_safety_allows_normal_memory() -> None:
    result = UserMemorySafetyValidator().validate_candidate_memory("me llamo Marcos")

    assert result.status == "passed"
    assert result.matched_rule is None


def test_user_memory_safety_blocks_sensitive_memory() -> None:
    validator = UserMemorySafetyValidator()

    assert validator.validate_candidate_memory("mi contraseña es 1234").status == "blocked"
    assert validator.validate_candidate_memory("guarda mi .env").status == "blocked"
    assert validator.validate_candidate_memory("mi token es abc").status == "blocked"
    assert validator.validate_candidate_memory("mi dni es 12345678A").status == "blocked"
    assert validator.validate_candidate_memory("mi api key es abc").status == "blocked"
