"""
API endpoints for LLM provider management
"""

from typing import Any

from fastapi import APIRouter, HTTPException

from app.core.logger import logger
from app.services.explanation_service import explanation_service

router = APIRouter()


@router.get("/provider/info", response_model=dict[str, Any])
async def get_provider_info():
    """Get information about the current LLM provider"""
    try:
        if explanation_service is None:
            raise HTTPException(status_code=503, detail="Explanation service not initialized")

        info = explanation_service.get_provider_info()
        return info
    except Exception as e:
        logger.exception(f"Error getting provider info: {e}")
        raise HTTPException(status_code=500, detail=str(e))
