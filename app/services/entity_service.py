"""
Entity Management Service
"""

from typing import Any

from app.core.logger import logger
from app.repositories.category_repository import CategoryRepository
from app.repositories.entity_repository import EntityRepository


class EntityService:
    """Service for entity management operations"""

    @staticmethod
    def add_entity(
        name: str,
        category_id: str,
        description: str = "",
    ) -> str:
        """Add a new entity manually"""
        category = CategoryRepository.get_by_id(category_id)
        if not category:
            raise ValueError(f"Category with ID {category_id} not found")

        existing = EntityRepository.get_by_name(name)
        if existing:
            raise ValueError(f"Entity with name '{name}' already exists")

        entity_id = EntityRepository.create(name, category_id, description)
        logger.info(f"Added entity: {name} to category {category_id}")
        return entity_id

    @staticmethod
    def delete_entity(entity_id: str) -> bool:
        entity = EntityRepository.get_by_id(entity_id)
        if not entity:
            raise ValueError(f"Entity with ID {entity_id} not found")

        success = EntityRepository.delete(entity_id)
        logger.info(f"Deleted entity: {entity_id}")
        return success

    @staticmethod
    def get_entity(entity_id: str) -> dict[str, Any] | None:
        return EntityRepository.get_by_id(entity_id)

    @staticmethod
    def list_entities(category_id: str | None = None, limit: int = 100) -> list[dict[str, Any]]:
        """List entities, optionally filtered by category"""
        return EntityRepository.list_all(category_id, limit)


entity_service = EntityService()
