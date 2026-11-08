import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()


class OpenRouterClient:
    def __init__(
        self,
        api_key: str | None = None,
        model_name: str = "openrouter/free",
    ):
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        self.model_name = model_name

        if self.api_key:
            self.client = OpenAI(
                base_url="https://openrouter.ai/api/v1", api_key=self.api_key
            )
        else:
            self.client = None

    def generate(self, prompt: str) -> str:
        """
        Sends the prompt to the model and returns its text response.
        Matches the interface expected by Generator.
        """
        if not self.api_key or self.client is None:
            raise ValueError(
                "OPENROUTER_API_KEY not found in environment or .env file."
            )

        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
        )

        return response.choices[0].message.content or ""
