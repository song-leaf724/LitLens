import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def uuid_str() -> str:
    return str(uuid.uuid4())


class Base(DeclarativeBase):
    pass


class ChatSession(Base):
    __tablename__ = "sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    title: Mapped[str] = mapped_column(String(255), default="文学阅读会话")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    messages: Mapped[list["Message"]] = relationship(
        back_populates="session", cascade="all, delete-orphan"
    )


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    session_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("sessions.id"), index=True
    )
    role: Mapped[str] = mapped_column(String(32), index=True)
    content: Mapped[str] = mapped_column(Text)
    task_type: Mapped[str] = mapped_column(String(64), default="chat")
    use_rag: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    session: Mapped["ChatSession"] = relationship(back_populates="messages")


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    filename: Mapped[str] = mapped_column(String(255), index=True)
    file_type: Mapped[str] = mapped_column(String(32))
    storage_path: Mapped[str] = mapped_column(String(512))
    status: Mapped[str] = mapped_column(String(32), default="processing")
    chunk_count: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    author: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    source_name: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    source_id: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    source_url: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    license: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    document_type: Mapped[str] = mapped_column(String(64), default="unknown")
    type_confidence: Mapped[float] = mapped_column(Float, default=0.0)
    type_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    chunk_strategy: Mapped[str] = mapped_column(String(64), default="modern")

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    chunks: Mapped[list["Chunk"]] = relationship(
        back_populates="document", cascade="all, delete-orphan"
    )


class Chunk(Base):
    __tablename__ = "chunks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    document_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("documents.id"), index=True
    )
    chunk_index: Mapped[int] = mapped_column(Integer, index=True)
    content: Mapped[str] = mapped_column(Text)
    source_location: Mapped[str] = mapped_column(String(255))
    vector_id: Mapped[str] = mapped_column(String(128), index=True)
    chunk_type: Mapped[str] = mapped_column(String(64), default="text")
    section_title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    metadata_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    document: Mapped["Document"] = relationship(back_populates="chunks")


class AgentRun(Base):
    __tablename__ = "agent_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    session_id: Mapped[Optional[str]] = mapped_column(
        String(36), nullable=True, index=True
    )
    task_type: Mapped[str] = mapped_column(String(64), default="literature")
    status: Mapped[str] = mapped_column(String(32), default="running")
    input_text: Mapped[str] = mapped_column(Text)
    output_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    ended_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    steps: Mapped[list["AgentStep"]] = relationship(
        back_populates="run", cascade="all, delete-orphan"
    )


class AgentStep(Base):
    __tablename__ = "agent_steps"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    run_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("agent_runs.id"), index=True
    )
    role: Mapped[str] = mapped_column(String(64), default="LiteratureAgent")
    step_type: Mapped[str] = mapped_column(String(64))
    tool_name: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    input_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    output_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    run: Mapped["AgentRun"] = relationship(back_populates="steps")
