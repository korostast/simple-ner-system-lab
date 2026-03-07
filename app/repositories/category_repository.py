import uuid
from typing import Any

from app.core.constants import DEFAULT_NER_CATEGORIES
from app.core.logger import logger
from app.database.neo4j_client import neo4j_client


class CategoryRepository:
    """Repository for Category nodes"""

    @staticmethod
    def create(name: str, description: str = "", parent_id: str | None = None) -> str:
        """Create a new category"""
        category_id = str(uuid.uuid4())

        if parent_id:
            query = """
            CREATE (c:Category {
                id: $id,
                name: $name,
                description: $description,
                created_at: datetime()
            })
            WITH c
            MATCH (p:Category {id: $parent_id})
            CREATE (p)-[:PARENT_OF]->(c)
            RETURN c.id as id
            """
            params = {
                "id": category_id,
                "name": name,
                "description": description,
                "parent_id": parent_id,
            }
        else:
            query = """
            CREATE (c:Category {
                id: $id,
                name: $name,
                description: $description,
                created_at: datetime()
            })
            RETURN c.id as id
            """
            params = {"id": category_id, "name": name, "description": description}

        _ = neo4j_client.execute_write(query, params)
        logger.info(f"Created category: {name} with ID: {category_id}")
        return category_id

    @staticmethod
    def get_by_id(category_id: str) -> dict[str, Any] | None:
        """Get category by ID"""
        query = """
        MATCH (c:Category {id: $id})
        OPTIONAL MATCH (c)<-[:PARENT_OF]-(p:Category)
        RETURN c, p.name as parent_name, p.id as parent_id
        """
        results = neo4j_client.execute_query(query, {"id": category_id})
        return results[0] if results else None

    @staticmethod
    def get_by_name(name: str) -> dict[str, Any] | None:
        """Get category by name"""
        query = """
        MATCH (c:Category {name: $name})
        OPTIONAL MATCH (c)<-[:PARENT_OF]-(p:Category)
        RETURN c, p.name as parent_name, p.id as parent_id
        """
        results = neo4j_client.execute_query(query, {"name": name})
        return results[0] if results else None

    @staticmethod
    def list_all() -> list[dict[str, Any]]:
        """List all categories"""
        query = """
        MATCH (c:Category)
        OPTIONAL MATCH (c)<-[:PARENT_OF]-(p:Category)
        RETURN c, p.name as parent_name, p.id as parent_id
        ORDER BY c.name
        """
        return neo4j_client.execute_query(query)

    @staticmethod
    def delete(category_id: str) -> bool:
        """Delete a category"""
        query = """
        MATCH (c:Category {id: $id})
        DETACH DELETE c
        RETURN count(c) as deleted
        """
        result = neo4j_client.execute_write(query, {"id": category_id})
        deleted = result["deleted"] if result else 0
        logger.info(f"Deleted category: {category_id}")
        return deleted > 0

    @staticmethod
    def assign_entity_to_category(entity_id: str, category_id: str) -> bool:
        """Assign entity to category"""
        query = """
        MATCH (e:Entity {id: $entity_id})
        MATCH (c:Category {id: $category_id})
        MERGE (e)-[:BELONGS_TO]->(c)
        RETURN e, c
        """
        neo4j_client.execute_write(query, {"entity_id": entity_id, "category_id": category_id})
        logger.info(f"Assigned entity {entity_id} to category {category_id}")
        return True

    @staticmethod
    def initialize_default_categories() -> None:
        """Initialize default NER categories if they don't exist"""
        for category_name in DEFAULT_NER_CATEGORIES:
            existing = CategoryRepository.get_by_name(category_name)
            if existing:
                logger.info(f"Category already exists: '{category_name}'")
            else:
                CategoryRepository.create(category_name, "Default NER category")
                logger.info(f"Created default category: '{category_name}'")
