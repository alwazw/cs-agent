import os
from openai import OpenAI

class LLMService:
    def __init__(self, api_key: str | None = None, model: str = "gpt-4o-mini"):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY", "mock-key")
        self.client = OpenAI(api_key=self.api_key)
        self.model = model

    def generate_response(
        self,
        user_message: str,
        persona_instructions: str,
        knowledge_context: str
    ) -> str:
        """
        Generates an SMS response combining persona instructions,
        aggregated markdown knowledge context, and user input.
        """
        system_prompt = (
            f"{persona_instructions}\n\n"
            "=== Knowledge Base Context ===\n"
            f"{knowledge_context if knowledge_context else 'No specific documentation available.'}\n\n"
            "=== Constraints ===\n"
            "Keep your responses suitable for SMS (concise, clear, and relevant)."
        )

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            max_tokens=250,
        )

        return response.choices[0].message.content or ""
