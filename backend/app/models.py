"""Domain models."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def _uuid() -> str:
    return str(uuid.uuid4())


UUID_PK = String(36)


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(UUID_PK, primary_key=True, default=_uuid)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    is_admin: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Conversation(Base):
    __tablename__ = "conversations"

    id: Mapped[str] = mapped_column(UUID_PK, primary_key=True, default=_uuid)
    session_key: Mapped[str] = mapped_column(String(64), index=True)
    title: Mapped[str | None] = mapped_column(String(512), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    messages: Mapped[list["Message"]] = relationship(
        back_populates="conversation", cascade="all, delete-orphan", order_by="Message.created_at"
    )


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[str] = mapped_column(UUID_PK, primary_key=True, default=_uuid)
    conversation_id: Mapped[str] = mapped_column(
        UUID_PK, ForeignKey("conversations.id", ondelete="CASCADE"), index=True
    )
    role: Mapped[str] = mapped_column(String(32))
    content: Mapped[str] = mapped_column(Text)
    meta: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    conversation: Mapped["Conversation"] = relationship(back_populates="messages")


class FAQ(Base):
    __tablename__ = "faqs"

    id: Mapped[str] = mapped_column(UUID_PK, primary_key=True, default=_uuid)
    question: Mapped[str] = mapped_column(Text)
    answer: Mapped[str] = mapped_column(Text)
    category: Mapped[str | None] = mapped_column(String(128), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class KnowledgeAsset(Base):
    """Uploaded document metadata after ingestion into vector store."""

    __tablename__ = "knowledge_assets"

    id: Mapped[str] = mapped_column(UUID_PK, primary_key=True, default=_uuid)
    filename: Mapped[str] = mapped_column(String(512))
    stored_path: Mapped[str] = mapped_column(String(1024))
    source_tag: Mapped[str] = mapped_column(String(512), unique=True, index=True)
    mime_type: Mapped[str | None] = mapped_column(String(128), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class VisualGuide(Base):
    """Tutorial screenshots / diagrams referenced by URL."""

    __tablename__ = "visual_guides"

    id: Mapped[str] = mapped_column(UUID_PK, primary_key=True, default=_uuid)
    title: Mapped[str] = mapped_column(String(512))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    image_path: Mapped[str] = mapped_column(String(1024))
    tags: Mapped[str | None] = mapped_column(String(512), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class SupportTicket(Base):
    __tablename__ = "support_tickets"

    id: Mapped[str] = mapped_column(UUID_PK, primary_key=True, default=_uuid)
    conversation_id: Mapped[str | None] = mapped_column(
        UUID_PK, ForeignKey("conversations.id", ondelete="SET NULL"), nullable=True
    )
    reason: Mapped[str] = mapped_column(Text)
    transcript_json: Mapped[list | dict | None] = mapped_column(JSON, nullable=True)
    status: Mapped[str] = mapped_column(String(64), default="open")
    confidence_at_escalation: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
