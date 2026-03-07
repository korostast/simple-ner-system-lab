"""
Category Management Service
"""

from typing import Any

from app.core.logger import logger
from app.repositories.category_repository import CategoryRepository
from app.repositories.entity_repository import EntityRepository


class CategoryService:
    """Service for category management operations"""

    @staticmethod
    def add_category(
        name: str, description: str = "", parent_id: str | None = None, auto_assign: bool = True
    ) -> str:
        """Add a new NER category"""
        existing = CategoryRepository.get_by_name(name)
        if existing:
            raise ValueError(f"Category with name '{name}' already exists")

        category_id = CategoryRepository.create(name, description, parent_id)
        logger.info(f"Added category: {name} with ID: {category_id}")

        if auto_assign:
            CategoryService.auto_assign_entities(category_id)

        return category_id

    @staticmethod
    def delete_category(category_id: str) -> bool:
        category = CategoryRepository.get_by_id(category_id)
        if not category:
            raise ValueError(f"Category with ID {category_id} not found")

        success = CategoryRepository.delete(category_id)
        logger.info(f"Deleted category: {category_id}")
        return success

    @staticmethod
    def get_category(category_id: str) -> dict[str, Any] | None:
        return CategoryRepository.get_by_id(category_id)

    @staticmethod
    def list_categories() -> list[dict[str, Any]]:
        return CategoryRepository.list_all()

    @staticmethod
    def auto_assign_entities(category_id: str) -> dict[str, Any]:
        """Auto-assign entities to a category based on NER predictions"""
        from app.services.ner_service import ner_service

        category = CategoryRepository.get_by_id(category_id)
        if not category:
            raise ValueError(f"Category with ID {category_id} not found")

        category_name = category["c"]["name"]

        all_entities = EntityRepository.list_all(limit=1000)

        assigned_count = 0
        for entity_data in all_entities:
            entity = entity_data["e"]
            entity_id = entity["id"]
            entity_name = entity["name"]

            # Use GLiNER to predict if entity belongs to this category
            try:
                # Predict entity's category
                predictions = ner_service.predict_entities(
                    entity_name, labels=[category_name], threshold=0.3
                )

                # If prediction matches, assign entity to category
                if predictions and predictions[0]["label"] == category_name:
                    CategoryRepository.assign_entity_to_category(entity_id, category_id)
                    assigned_count += 1
                    logger.info(f"Assigned entity {entity_name} to category {category_name}")

            except Exception as e:
                logger.warning(f"Failed to auto-assign entity {entity_name}: {e}")

        logger.info(f"Auto-assigned {assigned_count} entities to category {category_name}")

        return {
            "category_id": category_id,
            "category_name": category_name,
            "assigned_count": assigned_count,
        }


category_service = CategoryService()
