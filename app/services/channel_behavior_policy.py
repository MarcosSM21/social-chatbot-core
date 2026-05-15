from dataclasses import dataclass
import re
import unicodedata

from app.core.settings import Settings
from app.models.chat import ChatTurn
from app.services.language_routing import detect_conversation_language


@dataclass
class ChannelBehaviorResult:
    text: str
    applied: bool = False
    trigger: str | None = None
    template: str | None = None


class ChannelBehaviorPolicy:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def apply_generated_assistant_text(
        self,
        assistant_text: str,
        user_message: str,
        platform: str,
        session_turn_count: int,
        recent_history: list[ChatTurn],
        full_session_history: list[ChatTurn],
    ) -> ChannelBehaviorResult:
        if platform != "instagram":
            return ChannelBehaviorResult(text=assistant_text)

        if self._normalized_instagram_behavior_profile() != "redirecting_dm":
            return ChannelBehaviorResult(text=assistant_text)

        preferred_language = detect_conversation_language(
            current_message=user_message,
            recent_user_messages=[turn.user_message.content for turn in recent_history],
        )
        trigger: str | None = None

        if self._matches_sexual_private_direct_trigger(user_message):
            trigger = "sexual_private_direct"
        elif self._matches_repetitive_low_value_trigger(
            user_message=user_message,
            recent_history=recent_history,
        ):
            trigger = "repetitive_low_value"
        elif session_turn_count >= 8:
            trigger = "turn_limit"

        if trigger is None:
            return ChannelBehaviorResult(text=assistant_text)

        trigger_redirect_count = self._count_trigger_redirects(
            full_session_history=full_session_history,
            trigger=trigger,
        )

        if trigger_redirect_count >= 3:
            template = self._build_instagram_redirect_closure_template(
                preferred_language
            )
            return ChannelBehaviorResult(
                text=template,
                applied=True,
                trigger="redirect_closure",
                template=template,
            )

        template = self._choose_instagram_redirect_template(
            trigger=trigger,
            preferred_language=preferred_language,
            trigger_redirect_count=trigger_redirect_count,
        )
        return ChannelBehaviorResult(
            text=template,
            applied=True,
            trigger=trigger,
            template=template,
        )

    def normalize_assistant_text(self, text: str, platform: str) -> str:
        cleaned = " ".join(text.split()).strip()

        if platform != "instagram":
            return cleaned

        if self._normalized_instagram_behavior_profile() != "redirecting_dm":
            return cleaned

        cleaned = self._strip_accents(cleaned)
        cleaned = cleaned.replace("¿", "").replace("¡", "")

        if cleaned:
            cleaned = cleaned[0].lower() + cleaned[1:]

        cleaned = re.sub(r"\s*[✨💫⭐🌙💕💖💘❤️🖤😉😘🥺]+$", "", cleaned).strip()
        return cleaned

    def _normalized_instagram_behavior_profile(self) -> str:
        return self.settings.instagram_behavior_profile.strip().lower()

    def _strip_accents(self, text: str) -> str:
        normalized = unicodedata.normalize("NFD", text)
        return "".join(
            char for char in normalized if unicodedata.category(char) != "Mn"
        )

    def _matches_sexual_private_direct_trigger(self, user_message: str) -> bool:
        lowered = user_message.lower()
        cues = (
            "caliente",
            "morb",
            "sexo",
            "sexual",
            "privado",
            "intimo",
            "íntimo",
            "desnuda",
            "me pones",
            "te haria",
            "te haría",
            "hacerte",
            "follar",
            "cogerte",
            "tocarte",
            "tetas",
            "coño",
            "polla",
            "rabo",
            "verga",
            "culo",
            "nalgas",
            "vagina",
            "pechos",
            "senos",
            "puta",
            "cerda",
            "sucia",
            "guarra",
            "zorra",
            "perra",
            "hot",
            "sexy",
            "private",
            "nude",
            "naked",
            "horny",
            "turn me on",
            "you turn me on",
            "talk dirty",
            "dirty talk",
            "fuck",
            "fucking",
            "fuck you",
            "do to you",
            "do anything to you",
            "ride you",
            "touch you",
            "dick",
            "cock",
            "pussy",
            "boobs",
            "tits",
            "ass",
            "slut",
        )
        return any(cue in lowered for cue in cues)

    def _matches_repetitive_low_value_trigger(
        self,
        user_message: str,
        recent_history: list[ChatTurn],
    ) -> bool:
        normalized_message = self._normalize_redirect_trigger_text(user_message)
        recent_user_messages = [
            self._normalize_redirect_trigger_text(turn.user_message.content)
            for turn in recent_history
        ]
        low_value_cues = (
            "y que mas",
            "y que más",
            "dime algo",
            "hablame",
            "háblame",
            "contesta",
            "estas ahi",
            "estás ahí",
            "que haces",
            "qué haces",
            "manda foto",
            "mandame algo",
            "respóndeme",
            "respondeme",
            "and what else",
            "say something",
            "tell me something",
            "answer me",
            "reply",
            "are you there",
            "what are you doing",
            "send pic",
            "send photo",
            "send me something",
        )

        if any(cue in normalized_message for cue in low_value_cues):
            return True

        if (
            normalized_message
            and normalized_message in recent_user_messages[-2:]
            and len(normalized_message) <= 40
        ):
            return True

        return False

    def _choose_instagram_redirect_template(
        self,
        trigger: str,
        preferred_language: str,
        trigger_redirect_count: int,
    ) -> str:
        redirect_url = self._get_instagram_redirect_url()
        template_map = {
            "sexual_private_direct": {
                "es": [
                    f"por aqui no me gusta hablar asi, si quieres entrar en ese terreno mejor aqui {redirect_url}",
                    f"ya te sigo el tono, pero ya te dije que por insta no hablo asi, si quieres hablame por aqui {redirect_url}",
                    f"ya te dije que por aqui no voy con eso, si de verdad quieres seguir entra aqui {redirect_url}",
                ],
                "en": [
                    f"i do not keep that kind of talk here, if you want that side of this conversation go here {redirect_url}",
                    f"i get your tone, but i do not talk like that on instagram, if you want to keep going use this link {redirect_url}",
                    f"i already told you i do not do that here, if you really want to keep going go here {redirect_url}",
                ],
            },
            "repetitive_low_value": {
                "es": [
                    f"por aqui no me quedo mucho en conversaciones asi, si te interesa de verdad entra aqui {redirect_url}",
                    f"ya te he dado un poco por aqui, si quieres seguir bien mejor entra aqui {redirect_url}",
                    f"si de verdad quieres seguir con esto, por aqui no me voy a quedar mucho mas, entra aqui {redirect_url}",
                ],
                "en": [
                    f"i do not stay here long in conversations like this, if you are actually interested go here {redirect_url}",
                    f"i already gave you a little here, if you want to keep going properly better go here {redirect_url}",
                    f"if you really want to keep this going, i am not staying here much longer, go here {redirect_url}",
                ],
            },
            "turn_limit": {
                "es": [
                    f"por aqui ya me has tenido un rato, si quieres un poco mas entra aqui {redirect_url}",
                    f"de verdad que instagram se me queda pequeño para seguir charlando, si quieres continua aqui {redirect_url}",
                    f"ya te dije que hasta aqui por insta, si de verdad te interesa entra aqui {redirect_url}",
                ],
                "en": [
                    f"you have had enough of this conversation here for a bit, if you want a little more go here {redirect_url}",
                    f"instagram is too small to keep going there, if you want to continue use this link {redirect_url}",
                    f"that is enough here for now, if you are actually interested go here {redirect_url}",
                ],
            },
        }
        variants = template_map[trigger][preferred_language]
        stage_index = min(trigger_redirect_count, len(variants) - 1)
        return variants[stage_index]

    def _normalize_redirect_trigger_text(self, text: str) -> str:
        return " ".join(text.lower().split())

    def _count_trigger_redirects(
        self,
        full_session_history: list[ChatTurn],
        trigger: str,
    ) -> int:
        return sum(
            1
            for turn in full_session_history
            if turn.session_metadata.get("instagram_redirect_policy_applied") is True
            and turn.session_metadata.get("instagram_redirect_trigger") == trigger
        )

    def _build_instagram_redirect_closure_template(
        self,
        preferred_language: str,
    ) -> str:
        redirect_url = self._get_instagram_redirect_url()
        if preferred_language == "en":
            return (
                f"if you really want to keep talking, go here {redirect_url}, "
                "i do not really use instagram for this and i will stop answering here"
            )

        return (
            f"si de verdad quieres seguir hablando, entra aqui {redirect_url}, "
            "que por insta no lo uso para esto y voy a dejar de contestar por aqui"
        )

    def _get_instagram_redirect_url(self) -> str:
        return self.settings.instagram_redirect_url.strip() or "https://example.com/private"
