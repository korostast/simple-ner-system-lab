from pydantic import BaseModel


class MessageResponse(BaseModel):
    """Schema for generic message response"""

    message: str
    success: bool = True


class ErrorResponse(BaseModel):
    """Schema for error response"""

    error: str
    detail: str | None = None
