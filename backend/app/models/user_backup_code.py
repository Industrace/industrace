# backend/app/models/user_backup_code.py
import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.database import Base


class UserBackupCode(Base):
    """One-time MFA backup / recovery codes (hashed at rest)."""

    __tablename__ = "user_backup_codes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    code_hash = Column(String(255), nullable=False)
    used_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=func.now())

    user = relationship("User", back_populates="backup_codes")
