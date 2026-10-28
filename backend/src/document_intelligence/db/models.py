from datetime import datetime, timezone
import uuid

from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey


class Base(DeclarativeBase):
    pass


class DocumentRecord(Base):
    __tablename__ = "document_records"
    id: Mapped[str] = mapped_column(primary_key=True, default=lambda: uuid.uuid4().hex)
    session_id: Mapped[str] = mapped_column(
        ForeignKey("workspace_sessions.id", ondelete="CASCADE"), index=True
    )
    file_name: Mapped[str]
    num_pages: Mapped[int]
    num_chunks: Mapped[int]
    uploaded_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc)
    )
    session: Mapped["WorkspaceSession"] = relationship(back_populates="documents")


class WorkspaceSession(Base):
    __tablename__ = "workspace_sessions"
    id: Mapped[str] = mapped_column(primary_key=True, default=lambda: uuid.uuid4().hex)
    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(default="Default Workspace")
    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc)
    )
    user: Mapped["User"] = relationship(back_populates="sessions")
    documents: Mapped[list["DocumentRecord"]] = relationship(
        back_populates="session", cascade="all,delete-orphan"
    )


class User(Base):
    __tablename__ = "users"
    id: Mapped[str] = mapped_column(primary_key=True, default=lambda: uuid.uuid4().hex)
    email: Mapped[str] = mapped_column(nullable=False, unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc)
    )
    sessions: Mapped[list["WorkspaceSession"]] = relationship(
        back_populates="user", cascade="all,delete-orphan"
    )
