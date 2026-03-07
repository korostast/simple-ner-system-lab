from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.core.utils import convert_neo4j_datetime


class EntityCreate(BaseModel):
    """Schema for creating an entity"""

    name: str = Field(..., description="Entity name")
    category_id: str = Field(..., description="Category ID")
    description: str = Field(default="", description="Entity description")


class EntityUpdate(BaseModel):
    """Schema for updating an entity"""

    name: str | None = Field(None, description="Entity name")
    description: str | None = Field(None, description="Entity description")


class EntityResponse(BaseModel):
    """Schema for entity response"""

    id: str
    name: str
    description: str
    category_name: str | None = None
    category_id: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @field_validator("created_at", "updated_at", mode="before")
    @classmethod
    def convert_neo4j_datetime_fields(cls, v):
        """Convert neo4j.time.DateTime to Python datetime"""
        return convert_neo4j_datetime(v)


class EntityMention(BaseModel):
    """Schema for entity mention"""

    text: str
    label: str
    start: int
    end: int
    confidence: float


class EntityExplanationResponse(BaseModel):
    """Schema for explanation response"""

    entity: str
    explanation: str
