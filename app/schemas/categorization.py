from typing import List, Optional
from pydantic import BaseModel, Field, validator, confloat

class CategorizationResponse(BaseModel):
    """Response model for category suggestion"""
    category: str = Field(..., description="The suggested category")
    confidence: confloat(ge=0.0, le=1.0) = Field(..., description="Confidence score for the suggestion")
    keywords: List[str] = Field(default_factory=list, description="Keywords extracted from the content")
    method: str = Field(..., description="Method used for categorization")