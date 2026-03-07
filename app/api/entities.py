"""
Entity API endpoints
"""

from fastapi import APIRouter, HTTPException, Query

from app.core.logger import logger
from app.models.common_schemas import MessageResponse
from app.models.entity_schemas import EntityCreate, EntityResponse
from app.models.graph_schemas import EntityGraphResponse
from app.repositories.entity_repository import EntityRepository
from app.services.entity_service import entity_service

router = APIRouter(prefix="/api/entities", tags=["entities"])


@router.post("", response_model=EntityResponse, status_code=201)
async def create_entity(entity: EntityCreate):
    """Add a new entity manually"""
    try:
        entity_id = entity_service.add_entity(
            name=entity.name,
            category_id=entity.category_id,
            description=entity.description,
        )

        created_entity = entity_service.get_entity(entity_id)
        if not created_entity:
            raise HTTPException(status_code=500, detail="Failed to retrieve created entity")

        return EntityResponse(
            id=created_entity["e"]["id"],
            name=created_entity["e"]["name"],
            description=created_entity["e"]["description"],
            category_name=created_entity.get("category_name"),
            category_id=created_entity.get("category_id"),
            created_at=created_entity["e"].get("created_at"),
            updated_at=created_entity["e"].get("updated_at"),
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception(f"Error creating entity: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{entity_id}", response_model=EntityResponse)
async def get_entity(entity_id: str):
    """Get entity details by ID"""
    entity = entity_service.get_entity(entity_id)
    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")

    return EntityResponse(
        id=entity["e"]["id"],
        name=entity["e"]["name"],
        description=entity["e"]["description"],
        category_name=entity.get("category_name"),
        category_id=entity.get("category_id"),
        created_at=entity["e"].get("created_at"),
        updated_at=entity["e"].get("updated_at"),
    )


@router.delete("/{entity_id}", response_model=MessageResponse)
async def delete_entity(entity_id: str):
    try:
        success = entity_service.delete_entity(entity_id)
        if not success:
            raise HTTPException(status_code=404, detail="Entity not found")

        return MessageResponse(message="Entity deleted successfully")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception(f"Error deleting entity: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("", response_model=list[EntityResponse])
async def list_entities(
    category_id: str | None = Query(None, description="Filter by category ID"),
    search: str | None = Query(None, description="Search entities by name"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of entities to return"),
):
    """List all entities, optionally filtered by category or search term"""
    try:
        entities = entity_service.list_entities(category_id, limit)

        # Filter by search term if provided
        if search:
            search_lower = search.lower()
            entities = [
                entity for entity in entities if search_lower in entity["e"]["name"].lower().strip()
            ]

        return [
            EntityResponse(
                id=entity["e"]["id"],
                name=entity["e"]["name"],
                description=entity["e"]["description"],
                category_name=entity.get("category_name"),
                category_id=entity.get("category_id"),
                created_at=entity["e"].get("created_at"),
                updated_at=entity["e"].get("updated_at"),
            )
            for entity in entities
        ]
    except Exception as e:
        logger.exception(f"Error listing entities: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{entity_id}/graph", response_model=EntityGraphResponse)
async def get_entity_graph(entity_id: str):
    """Get 2-hop graph data for an entity (entity -> texts -> other entities)"""
    try:
        graph_data = EntityRepository.get_entity_graph(entity_id)
        return EntityGraphResponse(nodes=graph_data["nodes"], edges=graph_data["edges"])
    except Exception as e:
        logger.exception(f"Error getting entity graph: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
