from sqlalchemy import Column, Integer, String, Text, ForeignKey, Table
from sqlalchemy.orm import relationship
from app.models.base import Base

# Many-to-many relationship table between notes and categories
note_category = Table(
    'note_category',
    Base.metadata,
    Column('note_id', Integer, ForeignKey('note.id'), primary_key=True),
    Column('category_id', Integer, ForeignKey('category.id'), primary_key=True)
)

class Note(Base):
    """SQLAlchemy model for notes"""
    title = Column(String(255), nullable=False, index=True)
    content = Column(Text, nullable=False)
    summary = Column(Text, nullable=True)
    sentiment = Column(String(50), nullable=True)
    
    # Relationships
    categories = relationship(
        "Category", 
        secondary=note_category,
        back_populates="notes"
    )
