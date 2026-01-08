# backend/models/manufacturer.py
from sqlalchemy import Column, String, Text, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
from app.database import Base


class Manufacturer(Base):
    __tablename__ = "manufacturers"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        unique=True,
        nullable=False,
    )
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    name = Column(String(255), nullable=False, unique=True)
    description = Column(Text)
    website = Column(String(255), nullable=True)
    email = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(
        DateTime, default=func.now(), onupdate=func.now(), nullable=False
    )
    deleted_at = Column(DateTime, nullable=True)
    assets = relationship(
        "Asset", back_populates="manufacturer", cascade="all, delete-orphan"
    )
