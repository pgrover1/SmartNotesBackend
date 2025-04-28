from sqlalchemy import Column, String
from sqlalchemy.orm import relationship
from app.models.base import Base
from app.models.note import note_category

class Category(Base):
    """SQLAlchemy model for note categories"""
    name = Column(String(100), nullable=False, unique=True, index=True)
    description = Column(String(255), nullable=True)
    
    # Relationships
    notes = relationship(
        "Note", 
        secondary=note_category,
        back_populates="categories"
    )
