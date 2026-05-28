"""
UserModel for SQLAlchemy ORM, representing the 'user' table in the database.
"""

from datetime import UTC, datetime
import uuid

from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Uuid, DateTime, String

from backend.models.base_model import Base

class User(Base):
    __tablename__ = 'user'
    
    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        default=uuid.uuid4,
        primary_key=True
    )
    
    username: Mapped[str] = mapped_column(
        String,
        unique=True,
        index=True,
        nullable=False
    )

    display_name: Mapped[str] = mapped_column(
        String,
        nullable=False
    )

    # For auditing purposes only, not exposed in API responses

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.now(UTC),
        nullable=False
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.now(UTC),
        onupdate=datetime.now(UTC),
        nullable=False
    )
    # password: Mapped[str] = mapped_column(String, nullable=False)
