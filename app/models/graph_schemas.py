from typing import Any

from pydantic import BaseModel


class GraphNode(BaseModel):
    """Schema for a graph node"""

    data: dict[str, Any]


class GraphEdge(BaseModel):
    """Schema for a graph edge"""

    data: dict[str, Any]


class EntityGraphResponse(BaseModel):
    """Schema for entity graph response"""

    nodes: list[GraphNode]
    edges: list[GraphEdge]
