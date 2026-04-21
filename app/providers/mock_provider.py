from app.core.settings import Settings
from app.models.conversation_context import ConversationContext


class MockGenerationProvider:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def generate_reply(self, context: ConversationContext) -> str:
        
        cleaned_message = self._normalize_message(context.current_message.content)

        if not cleaned_message:
            return self._empty_message_response()

        prompt_context = self._build_context(context, cleaned_message)
        prompt = self._build_mock_prompt(prompt_context)

        return self._generate_from_prompt(prompt)
    

    def _normalize_message(self, content: str) -> str:
        return content.strip()
    
    def _build_context(self, context: ConversationContext, message: str) -> dict:
        return {
            "bot_name": self.settings.bot_name,
            "bot_tone": self.settings.bot_tone,
            "message": message,
            "has_history": len(context.recent_history) > 0,
            "history_size": len(context.recent_history),
            "recent_user_messages": [turn.user_message.content for turn in context.recent_history[-3:]],
        }
    
    def _build_mock_prompt(self, context: dict) -> dict:
        return {
            "instruction": "Generate a response based on the following context.",
            "context": context
        }
    
    def _generate_from_prompt(self, prompt: dict) -> str:
        context = prompt["context"]
        bot_name = context["bot_name"]
        bot_tone = context["bot_tone"]
        message_text = context["message"]
        has_history = context["has_history"]

        if bot_tone == "formal":
            if has_history:
                return (
                    f"{bot_name}: "
                    f"We are continuing our conversation. "
                    f"I have received your new message: '{message_text}'."
                )
            return (
                f"{bot_name}: "
                f"Hello. I have received your message: '{message_text}'."
            )

        if bot_tone == "direct":
            if has_history:
                return f"{bot_name}: Continuing. Received: {message_text}"
            return f"{bot_name}: Received: {message_text}"

        if has_history:
            return (
                f"{bot_name}: "
                f"We are continuing our conversation. You said: {message_text}"
            )

        return (
            f"{bot_name}: "
            f"Hello. Nice to talk to you. You said: {message_text}"
        )


    def _empty_message_response(self) -> str:
        if self.settings.bot_tone == "formal":
            return f"{self.settings.bot_name}: No message was received."

        if self.settings.bot_tone == "direct":
            return f"{self.settings.bot_name}: Empty message."

        return f"{self.settings.bot_name}: I did not receive any message."