from app.models.conversation_character import ConversationCharacter


def test_loads_leo_realistic_friend_extended_fields() -> None:
    character = ConversationCharacter.from_json_file("characters/leo_realistic_friend.json")

    assert character.character_id == "leo_realistic_friend"
    assert character.display_name == "Leo"
    assert character.inner_world
    assert character.motivations
    assert character.aspirations
    assert character.contradictions
    assert character.worldview
    assert character.relationship_dynamic
    assert character.conversation_habits
    assert character.do_not_perform


def test_loads_laia_ambitious_model_extended_fields() -> None:
    character = ConversationCharacter.from_json_file("characters/laia_ambitious_model.json")

    assert character.character_id == "laia_ambitious_model"
    assert character.display_name == "Laia"
    assert character.inner_world
    assert character.motivations
    assert character.aspirations
    assert character.contradictions
    assert character.worldview
    assert character.relationship_dynamic
    assert character.conversation_habits
    assert character.do_not_perform
