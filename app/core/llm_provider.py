"""
LLM Provider Interface and Implementations
"""

from openai import OpenAI

from app.core.config import settings
from app.core.logger import logger
from app.core.prompts import EXPLAIN_ENTITY_SYSTEM_PROMPT


class APILLMProvider:
    """OpenAI-compatible API provider (supports llama.cpp server)"""

    def __init__(self):
        self.client = None
        self._initialize_client()

    def _initialize_client(self):
        """Initialize OpenAI client"""
        try:
            # Support empty API key for local llama.cpp server
            api_key = settings.llm_api_key or "dummy-key"

            self.client = OpenAI(api_key=api_key, base_url=settings.llm_api_url)
            logger.info(f"API LLM provider initialized: {settings.llm_api_url}")
        except Exception as e:
            logger.exception(f"Failed to initialize API LLM provider: {e}")

    def generate_entity_explanation(self, word: str, user_prompt: str | None = None) -> str:
        """Generate explanation using API"""
        if not self.client:
            raise RuntimeError("API LLM client not available")

        try:
            response = self.client.chat.completions.create(
                model=settings.llm_model,
                messages=[
                    {"role": "system", "content": EXPLAIN_ENTITY_SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                max_tokens=settings.llm_max_tokens,
                temperature=settings.llm_temperature,
                top_p=settings.llm_top_p,
            )

            explanation = response.choices[0].message.content.strip()
            logger.info(f"Generated API explanation for '{word}': '{explanation}'")
            return explanation

        except Exception as e:
            logger.exception(f"Failed to generate API explanation for {word}: {e}")
            raise

    def is_available(self) -> bool:
        """Check if API provider is initialized"""
        return self.client is not None
