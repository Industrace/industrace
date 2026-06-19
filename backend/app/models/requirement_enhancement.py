# backend/app/models/requirement_enhancement.py
"""
IEC 62443-3-3 Requirement Enhancement (RE 1-4) per Security Requirement.
"""
import uuid
from sqlalchemy import Column, String, DateTime, Text, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class RequirementEnhancement(Base):
    __tablename__ = "requirement_enhancements"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    security_requirement_id = Column(
        UUID(as_uuid=True),
        ForeignKey("security_requirements.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    enhancement_level = Column(Integer, nullable=False)  # RE 1-4
    title = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    standard_version = Column(String(20), nullable=True, default="62443-3-3:2013")
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    security_requirement = relationship(
        "SecurityRequirement",
        back_populates="requirement_enhancements",
    )

    __table_args__ = (
        UniqueConstraint(
            "security_requirement_id",
            "enhancement_level",
            name="uq_sr_enhancement_level",
        ),
    )
