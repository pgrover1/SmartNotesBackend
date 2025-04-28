from sqlalchemy import Column, Integer, DateTime
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

class CustomBase:
    """Base class for all SQLAlchemy models"""
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @declared_attr
    def __tablename__(cls):
        """Generate __tablename__ automatically from class name"""
        return cls.__name__.lower()

Base = declarative_base(cls=CustomBase)
