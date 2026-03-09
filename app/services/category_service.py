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
        """Auto-assign entities to a category by re-parsing all texts in the knowledge base"""
        from app.repositories.text_repository import TextRepository
        from app.services.ner_service import ner_service

        category = CategoryRepository.get_by_id(category_id)
        if not category:
            raise ValueError(f"Category with ID {category_id} not found")

        category_name = category["c"]["name"]

        all_texts = TextRepository.list_all(limit=1000)

        assigned_count = 0
        texts_processed = 0
        entities_created = 0

        for text_data in all_texts:
            text = text_data["t"]
            text_id = text["id"]
            text_content = text["content"]

            texts_processed += 1

            # Use GLiNER to predict entities in this text for the specific category
            try:
                predictions = ner_service.predict_entities(text_content, labels=[category_name])

                for prediction in predictions:
                    entity_name = prediction["text"]
                    entity = EntityRepository.get_by_name(entity_name)
                    if not entity:
                        entity_id = EntityRepository.create(entity_name, category_id)
                        entities_created += 1
                        logger.info(f"Created entity {entity_name} in category {category_name}")
                    else:
                        entity_id = entity["e"]["id"]
                        CategoryRepository.assign_entity_to_category(entity_id, category_id)
                        assigned_count += 1
                        logger.info(f"Assigned entity {entity_name} to category {category_name}")

                    TextRepository.add_entity_mention(text_id, entity_id, role="mentioned")

            except Exception as e:
                logger.warning(f"Failed to process text {text_id}: {e}")

        logger.info(
            f"Auto-assign completed: processed {texts_processed} texts, "
            f"created {entities_created} new entities, "
            f"assigned {assigned_count} existing entities to category {category_name}"
        )

        return {
            "category_id": category_id,
            "category_name": category_name,
            "texts_processed": texts_processed,
            "entities_created": entities_created,
            "entities_assigned": assigned_count,
        }


category_service = CategoryService()
