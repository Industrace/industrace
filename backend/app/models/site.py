# backend/models/site.py
import uuid
from sqlalchemy import Column, String, DateTime, Text, ForeignKey, Table, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

site_contacts = Table(
    "site_contacts",
    Base.metadata,
    Column(
        "site_id",
        UUID(as_uuid=True),
        ForeignKey("sites.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "contact_id",
        UUID(as_uuid=True),
        ForeignKey("contacts.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


class Site(Base):
    __tablename__ = "sites"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    name = Column(String(255), nullable=False)
    code = Column(String(50), nullable=False)
    address = Column(Text)
    description = Column(Text)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    deleted_at = Column(DateTime, nullable=True)
    review_interval_months = Column(Integer, nullable=True)  # Intervallo review specifico per site (override tenant)
    assets = relationship("Asset", back_populates="site")
    areas = relationship("Area", back_populates="site")
    parent_id = Column(UUID(as_uuid=True), ForeignKey("sites.id"), nullable=True)
    parent = relationship("Site", remote_side=[id], backref="children")
    contacts = relationship("Contact", secondary=site_contacts, backref="sites")
