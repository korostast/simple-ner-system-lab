"""
Neo4j database client for NER System
"""

from typing import Any

from neo4j import GraphDatabase

from app.core.config import settings
from app.core.logger import logger


class Neo4jClient:
    """Neo4j database client"""

    def __init__(self):
        self.driver: GraphDatabase.driver | None = None
        self._connect()

    def _connect(self):
        """Establish connection to Neo4j"""
        try:
            self.driver = GraphDatabase.driver(
                settings.neo4j_uri, auth=(settings.neo4j_user, settings.neo4j_password)
            )
            # Test connection
            self.driver.verify_connectivity()
            logger.info(f"Connected to Neo4j at {settings.neo4j_uri}")
        except Exception as e:
            logger.exception(f"Failed to connect to Neo4j: {e}")
            raise

    def close(self):
        """Close database connection"""
        if self.driver:
            self.driver.close()
            logger.info("Neo4j connection closed")

    def execute_query(
        self, query: str, parameters: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        """Execute a Cypher query and return results"""
        try:
            with self.driver.session() as session:
                result = session.run(query, parameters or {})
                return [record.data() for record in result]
        except Exception as e:
            logger.exception(f"Query execution failed: {e}")
            raise

    def execute_write(self, query: str, parameters: dict[str, Any] | None = None) -> Any:
        """Execute a write operation"""
        try:
            with self.driver.session() as session:
                result = session.run(query, parameters or {})
                return result.single()
        except Exception as e:
            logger.exception(f"Write operation failed: {e}")
            raise

    def initialize_schema(self) -> None:
        """Initialize database schema with constraints and indexes"""
        constraints = [
            "CREATE CONSTRAINT entity_id_unique IF NOT EXISTS FOR (e:Entity) REQUIRE e.id IS UNIQUE",
            "CREATE CONSTRAINT category_id_unique IF NOT EXISTS FOR (c:Category) REQUIRE c.id IS UNIQUE",
            "CREATE CONSTRAINT text_id_unique IF NOT EXISTS FOR (t:Text) REQUIRE t.id IS UNIQUE",
            "CREATE CONSTRAINT word_id_unique IF NOT EXISTS FOR (w:Word) REQUIRE w.id IS UNIQUE",
        ]

        indexes = [
            "CREATE INDEX entity_name_index IF NOT EXISTS FOR (e:Entity) ON (e.name)",
            "CREATE INDEX category_name_index IF NOT EXISTS FOR (c:Category) ON (c.name)",
            "CREATE INDEX text_content_index IF NOT EXISTS FOR (t:Text) ON (t.content)",
            "CREATE INDEX word_text_index IF NOT EXISTS FOR (w:Word) ON (w.text)",
        ]

        for constraint in constraints:
            try:
                self.execute_write(constraint)
                logger.info(f"Created constraint: {constraint}")
            except Exception as e:
                logger.warning(f"Constraint may already exist: {e}")

        for index in indexes:
            try:
                self.execute_write(index)
                logger.info(f"Created index: {index}")
            except Exception as e:
                logger.warning(f"Index may already exist: {e}")

        logger.info("Database schema initialized")


neo4j_client = Neo4jClient()
