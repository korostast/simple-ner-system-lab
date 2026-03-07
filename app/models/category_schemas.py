from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.core.utils import convert_neo4j_datetime


class CategoryCreate(BaseModel):
    """Schema for creating a category"""

    name: str = Field(..., description="Category name")
    description: str = Field(default="", description="Category description")
    parent_id: str | None = Field(None, description="Parent category ID")


class CategoryResponse(BaseModel):
    """Schema for category response"""

    id: str
    name: str
    description: str
    parent_name: str | None = None
    parent_id: str | None = None
    created_at: datetime | None = None

    @field_validator("created_at", mode="before")
    @classmethod
    def convert_neo4j_datetime_fields(cls, v):
        """Convert neo4j.time.DateTime to Python datetime"""
        return convert_neo4j_datetime(v)
