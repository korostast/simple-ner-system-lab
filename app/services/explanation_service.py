"""
Explanation Service using LLM Provider Interface
"""

from typing import Any

from app.core.config import settings
from app.core.constants import ENTITY_EXPLANATION_DOCUMENTS_RETURNED_COUNT
from app.core.llm_provider import APILLMProvider
from app.core.logger import logger
from app.repositories.entity_repository import EntityRepository


class ExplanationService:
    """Service for generating word/entity explanations using LLM"""

    def __init__(self):
        self.provider = None
        self._initialize_provider()

    def _initialize_provider(self):
        """Initialize LLM provider based on configuration"""
        try:
            self.provider = APILLMProvider()
            logger.info("LLM provider initialized")
        except Exception as e:
            logger.exception(f"Failed to initialize LLM provider: {e}")

    def get_provider_info(self) -> dict[str, Any]:
        """Get information about the current LLM provider"""
        model = settings.llm_model
        return {
            "available": self.provider.is_available() if self.provider else False,
            "model": model,
        }

    def explain_entity(self, entity_id: str) -> dict[str, Any]:
        """Generate explanation for an entity using related documents as context"""
        from app.repositories.text_repository import TextRepository

        entity = EntityRepository.get_by_id(entity_id)
        if not entity:
            raise ValueError(f"Entity with ID {entity_id} not found")

        entity_name = entity["e"]["name"]
        entity_description = entity["e"].get("description", "")
        category_name = entity.get("category_name", "")

        # Get related documents where this entity is mentioned
        related_texts = TextRepository.get_texts_by_entity(
            entity_id, limit=ENTITY_EXPLANATION_DOCUMENTS_RETURNED_COUNT
        )
        logger.info(f"Found {len(related_texts)} texts for to explain entity '{entity_name}'")

        user_prompt_parts = [f'Entity: "{entity_name}"']
        if category_name:
            user_prompt_parts.append(f'Category: "{category_name}"')

        if entity_description:
            user_prompt_parts.append(f'Description: "{entity_description}"')

        # Add related documents as context
        if related_texts:
            user_prompt_parts.append("Related documents, where entity is mentioned:")
            for i, text_data in enumerate(related_texts, 1):
                text_content = text_data["t"]["content"]
                user_prompt_parts.append(f"{i}. {text_content}")

        user_prompt = "\n".join(user_prompt_parts) if user_prompt_parts else None
        if not self.provider or not self.provider.is_available():
            logger.warning("LLM provider not available, returning generic explanation")
            explanation = (
                f"Explanation for '{entity_name}' is not available. LLM service is not configured."
            )
        else:
            explanation = self.provider.generate_entity_explanation(entity_name, user_prompt)

        return {
            "entity_id": entity_id,
            "name": entity_name,
            "category": category_name,
            "description": entity_description,
            "explanation": explanation,
            "related_documents_count": len(related_texts),
        }


explanation_service = ExplanationService()
