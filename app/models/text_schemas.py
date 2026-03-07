from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.core.utils import convert_neo4j_datetime
from app.models.entity_schemas import EntityMention


class TextCreate(BaseModel):
    """Schema for creating a text"""

    content: str = Field(..., description="Text content")


class TextResponse(BaseModel):
    """Schema for text response"""

    id: str
    content: str
    created_at: datetime | None = None

    @field_validator("created_at", mode="before")
    @classmethod
    def convert_neo4j_datetime_fields(cls, v):
        """Convert neo4j.time.DateTime to Python datetime"""
        return convert_neo4j_datetime(v)


class TextParseRequest(BaseModel):
    """Schema for text parsing request"""

    content: str = Field(..., description="Text content to parse")
    labels: list[str] | None = Field(None, description="NER labels to use")


class TextParseResponse(BaseModel):
    """Schema for text parsing response"""

    text_id: str
    content: str
    entities: list[EntityMention]
