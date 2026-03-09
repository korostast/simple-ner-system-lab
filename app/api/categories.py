"""
Category Management API endpoints
"""

from fastapi import APIRouter, HTTPException

from app.core.logger import logger
from app.models.category_schemas import CategoryCreate, CategoryResponse
from app.models.common_schemas import (
    MessageResponse,
)
from app.services.category_service import category_service

router = APIRouter(prefix="/api/categories", tags=["categories"])


@router.post("", response_model=CategoryResponse, status_code=201)
async def create_category(category: CategoryCreate):
    """Add a new NER category"""
    try:
        category_id = category_service.add_category(
            name=category.name,
            description=category.description,
            parent_id=category.parent_id,
            auto_assign=True,
        )

        # Return created category
        created_category = category_service.get_category(category_id)
        if not created_category:
            raise HTTPException(status_code=500, detail="Failed to retrieve created category")

        return CategoryResponse(
            id=created_category["c"]["id"],
            name=created_category["c"]["name"],
            description=created_category["c"]["description"],
            parent_name=created_category.get("parent_name"),
            parent_id=created_category.get("parent_id"),
            created_at=created_category["c"].get("created_at"),
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception(f"Error creating category: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("", response_model=list[CategoryResponse])
async def list_categories():
    try:
        categories = category_service.list_categories()

        return [
            CategoryResponse(
                id=cat["c"]["id"],
                name=cat["c"]["name"],
                description=cat["c"]["description"],
                parent_name=cat.get("parent_name"),
                parent_id=cat.get("parent_id"),
                created_at=cat["c"].get("created_at"),
            )
            for cat in categories
        ]
    except Exception as e:
        logger.exception(f"Error listing categories: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{category_id}", response_model=CategoryResponse)
async def get_category(category_id: str):
    """Get category details by ID"""
    category = category_service.get_category(category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    return CategoryResponse(
        id=category["c"]["id"],
        name=category["c"]["name"],
        description=category["c"]["description"],
        parent_name=category.get("parent_name"),
        parent_id=category.get("parent_id"),
        created_at=category["c"].get("created_at"),
    )


@router.delete("/{category_id}", response_model=MessageResponse)
async def delete_category(category_id: str):
    try:
        success = category_service.delete_category(category_id)
        if not success:
            raise HTTPException(status_code=404, detail="Category not found")

        return MessageResponse(message="Category deleted successfully")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception(f"Error deleting category: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/{category_id}/assign", response_model=MessageResponse)
async def auto_assign_entities(category_id: str):
    """Auto-assign entities to a category by re-parsing all texts in the knowledge base"""
    try:
        result = category_service.auto_assign_entities(category_id)
        return MessageResponse(
            message=f"Processed {result['texts_processed']} texts, "
            f"created {result['entities_created']} new entities, "
            f"assigned {result['entities_assigned']} existing entities to category {result['category_name']}"
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception(f"Error auto-assigning entities: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
