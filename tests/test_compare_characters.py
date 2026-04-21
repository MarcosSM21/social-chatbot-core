from scripts.compare_characters import run_character_case, reset_runtime_storage


def test_compare_characters_uses_requested_character_file() -> None:
    reset_runtime_storage()

    result = run_character_case(
        character_file="characters/laia_ambitious_model.json",
        message="holaa",
        provider="mock",
        session_id="test-session",
        external_user_id="test-user",
    )

    assert result["character_id"] == "laia_ambitious_model"
    assert result["character_name"] == "Laia"
    assert result["user_message"] == "holaa"
    assert result["assistant_message"]


def test_compare_characters_can_switch_between_characters() -> None:
    reset_runtime_storage()

    leo_result = run_character_case(
        character_file="characters/leo_realistic_friend.json",
        message="holaa",
        provider="mock",
        session_id="test-session-leo",
        external_user_id="test-user-leo",
    )
    laia_result = run_character_case(
        character_file="characters/laia_ambitious_model.json",
        message="holaa",
        provider="mock",
        session_id="test-session-laia",
        external_user_id="test-user-laia",
    )

    assert leo_result["character_id"] == "leo_realistic_friend"
    assert laia_result["character_id"] == "laia_ambitious_model"
    assert leo_result["character_name"] == "Leo"
    assert laia_result["character_name"] == "Laia"
