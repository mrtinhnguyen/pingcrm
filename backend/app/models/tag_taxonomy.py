import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class TagTaxonomy(Base):
    __tablename__ = "tag_taxonomies"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    categories: Mapped[dict] = mapped_column(JSON, default=dict)
    # Example: {"Role/Expertise": ["UX Designer", "Solidity Dev"],
    #           "Industry": ["Crypto", "AI/ML"],
    #           "Events": ["ETHdenver 2026"]}
    status: Mapped[str] = mapped_column(String, default="draft")  # draft | approved

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), onupdate=func.now(), nullable=True
    )
