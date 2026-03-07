"""
Explanation API endpoints
"""

from fastapi import APIRouter, HTTPException

from app.core.logger import logger
from app.models.entity_schemas import EntityExplanationResponse
from app.services.explanation_service import explanation_service

router = APIRouter(prefix="/api", tags=["explanations"])


@router.post("/entities/{entity_id}/explain", response_model=EntityExplanationResponse)
async def explain_entity(entity_id: str):
    """Get explanation for an entity via LLM"""
    try:
        result = explanation_service.explain_entity(entity_id)
        return EntityExplanationResponse(
            entity=result["name"],
            explanation=result["explanation"],
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.exception(f"Error explaining entity: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
