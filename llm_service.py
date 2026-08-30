import os
from openai import AsyncOpenAI
from typing import List, Dict

class LLMService:
    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None
    ):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY", "mock-key")
        self.base_url = base_url or os.getenv("LOCAL_LLM_URL", None)
        self.model = model or os.getenv("LLM_MODEL", "gpt-4o-mini")

        kwargs = {"api_key": self.api_key}
        if self.base_url:
            kwargs["base_url"] = self.base_url

        self.client = AsyncOpenAI(**kwargs)

    async def generate_response(
        self,
        user_message: str,
        persona_instructions: str,
        knowledge_context: str,
        chat_history: List[Dict[str, str]] | None = None
    ) -> str:
        """
        Generates an SMS response using AsyncOpenAI combining:
        - System prompt (persona instructions + knowledge base context + constraints)
        - Windowed chat history (up to last 5 back-and-forth turns)
        - User message
        - Flexible support for OpenAI, LM Studio, Ollama, or local inference servers.
        """
        system_prompt = (
            f"{persona_instructions}\n\n"
            "=== Knowledge Base Context ===\n"
            f"{knowledge_context if knowledge_context else 'No specific documentation available.'}\n\n"
            "=== Constraints ===\n"
            "Keep your responses suitable for SMS (concise, under 320 characters, clear, and relevant)."
        )

        messages = [{"role": "system", "content": system_prompt}]

        if chat_history:
            messages.extend(chat_history)

        messages.append({"role": "user", "content": user_message})

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=150,
        )

        return (response.choices[0].message.content or "").strip()
