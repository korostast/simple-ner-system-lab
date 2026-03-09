import uuid
from typing import Any

from app.core.logger import logger
from app.database.neo4j_client import neo4j_client


class EntityRepository:
    """Repository for Entity nodes"""

    @staticmethod
    def create(name: str, category_id: str, description: str = "") -> str:
        """Create a new entity"""
        entity_id = str(uuid.uuid4())

        query = """
        CREATE (e:Entity {
            id: $id,
            name: $name,
            description: $description,
            created_at: datetime(),
            updated_at: datetime()
        })
        WITH e
        MATCH (c:Category {id: $category_id})
        CREATE (e)-[:BELONGS_TO]->(c)
        RETURN e.id as id
        """

        _ = neo4j_client.execute_write(
            query,
            {
                "id": entity_id,
                "name": name,
                "description": description,
                "category_id": category_id,
            },
        )

        logger.info(f"Created entity: {name} with ID: {entity_id}")
        return entity_id

    @staticmethod
    def get_by_id(entity_id: str) -> dict[str, Any] | None:
        """Get entity by ID"""
        query = """
        MATCH (e:Entity {id: $id})
        OPTIONAL MATCH (e)-[:BELONGS_TO]->(c:Category)
        RETURN e, c.name as category_name, c.id as category_id
        """
        results = neo4j_client.execute_query(query, {"id": entity_id})
        return results[0] if results else None

    @staticmethod
    def get_by_name(name: str) -> dict[str, Any] | None:
        """Get entity by name"""
        query = """
        MATCH (e:Entity {name: $name})
        OPTIONAL MATCH (e)-[:BELONGS_TO]->(c:Category)
        RETURN e, c.name as category_name, c.id as category_id
        """
        results = neo4j_client.execute_query(query, {"name": name})
        return results[0] if results else None

    @staticmethod
    def list_all(category_id: str | None = None, limit: int = 100) -> list[dict[str, Any]]:
        """List all entities, optionally filtered by category"""
        if category_id:
            query = """
            MATCH (e:Entity)-[:BELONGS_TO]->(c:Category {id: $category_id})
            RETURN e, c.name as category_name, c.id as category_id
            LIMIT $limit
            """
            params = {"category_id": category_id, "limit": limit}
        else:
            query = """
            MATCH (e:Entity)
            OPTIONAL MATCH (e)-[:BELONGS_TO]->(c:Category)
            RETURN e, c.name as category_name, c.id as category_id
            LIMIT $limit
            """
            params = {"limit": limit}

        return neo4j_client.execute_query(query, params)

    @staticmethod
    def delete(entity_id: str) -> bool:
        """Delete an entity"""
        query = """
        MATCH (e:Entity {id: $id})
        DETACH DELETE e
        RETURN count(e) as deleted
        """
        result = neo4j_client.execute_write(query, {"id": entity_id})
        deleted = result["deleted"] if result else 0
        logger.info(f"Deleted entity: {entity_id}")
        return deleted > 0

    @staticmethod
    def _create_node_id(node_type: str, node_id: str) -> str:
        """Create a unique node ID for the graph"""
        return f"{node_type}-{node_id}"

    @staticmethod
    def _create_entity_node(
        entity: dict[str, Any], category: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Create an entity node for the graph"""
        return {
            "data": {
                "id": EntityRepository._create_node_id("entity", entity["id"]),
                "label": entity["name"],
                "type": "entity",
                "description": entity.get("description", ""),
                "category": category["name"] if category else None,
            }
        }

    @staticmethod
    def _create_category_node(category: dict[str, Any]) -> dict[str, Any]:
        """Create a category node for the graph"""
        return {
            "data": {
                "id": EntityRepository._create_node_id("category", category["id"]),
                "label": category["name"],
                "type": "category",
                "description": category.get("description", ""),
            }
        }

    @staticmethod
    def _create_text_node(text: dict[str, Any]) -> dict[str, Any]:
        """Create a text node for the graph"""
        label = f"{text['content'][:50]}..." if len(text["content"]) > 50 else text["content"]
        return {
            "data": {
                "id": EntityRepository._create_node_id("text", text["id"]),
                "label": label,
                "type": "text",
                "content": text["content"],
            }
        }

    @staticmethod
    def _create_edge(source_id: str, target_id: str, label: str) -> dict[str, Any]:
        """Create an edge for the graph"""
        return {"data": {"source": source_id, "target": target_id, "label": label}}

    @staticmethod
    def get_entity_graph(entity_id: str) -> dict[str, Any]:
        """Get 2-hop graph data for an entity (entity -> texts -> other entities)"""

        # Return all the 2-hop graph data in a single query
        query = """
        MATCH (e:Entity {id: $id})
        OPTIONAL MATCH (e)-[:BELONGS_TO]->(c:Category)
        WITH e, collect(DISTINCT c) AS categories

        OPTIONAL MATCH (t:Text)-[:MENTIONED_IN]->(e)
        WITH e, categories, t

        OPTIONAL MATCH (t)-[:MENTIONED_IN]->(e2:Entity)
        WHERE e2.id <> $id
        WITH e, categories, t, e2

        OPTIONAL MATCH (e2)-[:BELONGS_TO]->(c2:Category)
        WITH e, categories, t, e2, collect(DISTINCT c2) AS oe_categories

        WITH e, categories, 
            collect(DISTINCT t) AS texts,
            collect(DISTINCT CASE 
                WHEN e2 IS NOT NULL 
                THEN {entity: e2, categories: oe_categories} 
            END) AS other_entities_with_cats

        RETURN e, categories, texts, other_entities_with_cats
        """
        results = neo4j_client.execute_query(query, {"id": entity_id})

        if not results:
            return {"nodes": [], "edges": []}

        result = results[0]
        entity = result["e"]
        categories = result["categories"]
        texts = result["texts"]
        secondary_entities = [
            secondary_entity
            for secondary_entity in result["other_entities_with_cats"]
            if secondary_entity["entity"] is not None
        ]

        nodes = []
        edges = []
        node_ids = set()

        def __add_node(node: dict[str, Any]) -> None:
            """Add a node if it doesn't already exist"""
            node_id = node["data"]["id"]
            if node_id not in node_ids:
                nodes.append(node)
                node_ids.add(node_id)

        def __add_edge(source_id: str, target_id: str, label: str) -> None:
            """Add an edge to the graph"""
            edges.append(EntityRepository._create_edge(source_id, target_id, label))

        # 1. Entity node
        main_entity_node = EntityRepository._create_entity_node(
            entity, categories[0] if categories else None
        )
        __add_node(main_entity_node)

        # 2. Category nodes - add all categories the entity belongs to
        for category in categories:
            category_node = EntityRepository._create_category_node(category)
            __add_node(category_node)
            __add_edge(main_entity_node["data"]["id"], category_node["data"]["id"], "BELONGS_TO")

        # 3. Text nodes
        for text in texts:
            text_node = EntityRepository._create_text_node(text)
            __add_node(text_node)
            __add_edge(main_entity_node["data"]["id"], text_node["data"]["id"], "MENTIONED_IN")

        # 4. Second level of entities (all the entities related to all the texts)
        for secondary_entity in secondary_entities:
            other_entity = secondary_entity["entity"]
            other_categories = secondary_entity.get("categories", [])

            entity_node = EntityRepository._create_entity_node(
                other_entity, other_categories[0] if other_categories else None
            )
            __add_node(entity_node)

            # 4.1. Categories - add all categories the secondary entity belongs to
            for other_category in other_categories:
                category_node = EntityRepository._create_category_node(other_category)
                __add_node(category_node)
                __add_edge(entity_node["data"]["id"], category_node["data"]["id"], "BELONGS_TO")

            # 4.2. Link texts and entities
            for text in texts:
                text_node_id = EntityRepository._create_node_id("text", text["id"])
                __add_edge(text_node_id, entity_node["data"]["id"], "MENTIONED_IN")

        logger.info(
            f"Generated graph for entity {entity_id}: {len(nodes)} nodes, {len(edges)} edges"
        )
        return {"nodes": nodes, "edges": edges}
