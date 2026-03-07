"""
Text Processing API endpoints
"""

from fastapi import APIRouter, HTTPException, Query

from app.core.logger import logger
from app.models.text_schemas import (
    TextParseRequest,
    TextParseResponse,
    TextResponse,
)
from app.repositories.text_repository import TextRepository
from app.services.ner_service import ner_service

router = APIRouter(prefix="/api/texts", tags=["texts"])


@router.post("/parse", response_model=TextParseResponse, status_code=201)
async def parse_text(request: TextParseRequest):
    """Parse text and extract entities"""
    try:
        result = ner_service.parse_text(
            content=request.content,
            labels=request.labels,
            auto_create_entities=True,
        )

        return TextParseResponse(
            text_id=result["text_id"],
            content=result["content"],
            entities=[
                {
                    "text": e["text"],
                    "label": e["label"],
                    "start": 0,
                    "end": len(e["text"]),
                    "confidence": e["confidence"],
                }
                for e in result["entities"]
            ],
        )
    except Exception as e:
        logger.exception(f"Error parsing text: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{text_id}", response_model=TextResponse)
async def get_text(text_id: str):
    text = TextRepository.get_by_id(text_id)
    if not text:
        raise HTTPException(status_code=404, detail="Text not found")

    return TextResponse(
        id=text["t"]["id"],
        content=text["t"]["content"],
        created_at=text["t"].get("created_at"),
    )


@router.get("", response_model=list[TextResponse])
async def list_texts(limit: int = Query(100, ge=1, le=1000)):
    try:
        query = """
        MATCH (t:Text)
        RETURN t
        LIMIT $limit
        """
        from app.database.neo4j_client import neo4j_client

        results = neo4j_client.execute_query(query, {"limit": limit})

        return [
            TextResponse(
                id=r["t"]["id"],
                content=r["t"]["content"],
                created_at=r["t"].get("created_at"),
            )
            for r in results
        ]
    except Exception as e:
        logger.exception(f"Error listing texts: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
