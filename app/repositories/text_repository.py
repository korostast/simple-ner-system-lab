import uuid
from typing import Any

from app.core.logger import logger
from app.database.neo4j_client import neo4j_client


class TextRepository:
    """Repository for Text nodes"""

    @staticmethod
    def create(content: str) -> str:
        """Create a new text"""
        text_id = str(uuid.uuid4())

        query = """
        CREATE (t:Text {
            id: $id,
            content: $content,
            created_at: datetime()
        })
        RETURN t.id as id
        """

        _ = neo4j_client.execute_write(query, {"id": text_id, "content": content})

        logger.info(f"Created text with ID: {text_id}")
        return text_id

    @staticmethod
    def get_by_id(text_id: str) -> dict[str, Any] | None:
        """Get text by ID"""
        query = """
        MATCH (t:Text {id: $id})
        RETURN t
        """
        results = neo4j_client.execute_query(query, {"id": text_id})
        return results[0] if results else None

    @staticmethod
    def add_entity_mention(text_id: str, entity_id: str, role: str = "mentioned"):
        """Add entity mention relation to text"""
        query = """
        MATCH (t:Text {id: $text_id})
        MATCH (e:Entity {id: $entity_id})
        MERGE (t)-[r:MENTIONED_IN]->(e)
        SET r.role = $role
        RETURN t, e
        """
        neo4j_client.execute_write(
            query, {"text_id": text_id, "entity_id": entity_id, "role": role}
        )
        logger.info(f"Added entity mention: {entity_id} in text {text_id} as {role}")

    @staticmethod
    def get_texts_by_entity(entity_id: str, limit: int = 100) -> list[dict[str, Any]]:
        """Get texts where entity is mentioned, optionally filtered by role"""
        query = """
        MATCH (t:Text)-[r:MENTIONED_IN]->(e:Entity {id: $entity_id})
        RETURN t, r.role as role
        LIMIT $limit
        """
        params = {"entity_id": entity_id, "limit": limit}

        return neo4j_client.execute_query(query, params)
