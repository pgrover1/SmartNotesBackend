from pydantic import BaseModel, Field, validator

class SentimentResponse(BaseModel):
    """Response model for sentiment analysis"""
    sentiment: str = Field(..., description="The sentiment of the note (Positive, Neutral, or Negative)")
    
    @validator('sentiment')
    def validate_sentiment(cls, v):
        allowed_sentiments = ["Positive", "Neutral", "Negative"]
        if v not in allowed_sentiments:
            raise ValueError(f"Sentiment must be one of: {', '.join(allowed_sentiments)}")
        return v