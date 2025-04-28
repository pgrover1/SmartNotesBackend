from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, validator

class SummarizeParams(BaseModel):
    """Parameters for summarizing a note"""
    max_length: int = Field(150, description="Maximum length of summary in characters", ge=50, le=1000)
    model: str = Field("gpt-4o", description="OpenAI model to use for summarization")
    
    @validator('model')
    def validate_model(cls, v):
        allowed_models = ["gpt-4o", "gpt-3.5-turbo"]
        if v not in allowed_models:
            raise ValueError(f"Model must be one of: {', '.join(allowed_models)}")
        return v

class SummarizeResponse(BaseModel):
    """Response model for summarization"""
    summary: Optional[str] = None
    success: bool = Field(..., description="Whether the summarization was successful")
    error: Optional[str] = None
    model_used: str = Field(..., description="The model used for summarization")