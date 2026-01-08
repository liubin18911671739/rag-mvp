from sqlalchemy import Column, String, DateTime, Text, Float, Integer, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import UUID, JSONB
from datetime import datetime
import uuid

Base = declarative_base()


class Document(Base):
    """Document metadata table."""

    __tablename__ = "documents"

    doc_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(500), nullable=False, index=True)
    source_path = Column(String(1000), nullable=False)
    content_hash = Column(String(64), nullable=False, unique=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def to_dict(self):
        return {
            "doc_id": str(self.doc_id),
            "title": self.title,
            "source_path": self.source_path,
            "content_hash": self.content_hash,
            "created_at": self.created_at.isoformat()
        }


class Chunk(Base):
    """Text chunks with embeddings for semantic search."""

    __tablename__ = "chunks"

    chunk_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    doc_id = Column(UUID(as_uuid=True), ForeignKey("documents.doc_id", ondelete="CASCADE"), nullable=False, index=True)
    text = Column(Text, nullable=False)
    metadata = Column(JSONB, nullable=False, default=dict)
    # embedding will be added via migration (vector column)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def to_dict(self):
        return {
            "chunk_id": str(self.chunk_id),
            "doc_id": str(self.doc_id),
            "text": self.text,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat()
        }


class RAGFeedback(Base):
    """User feedback for RAG quality monitoring."""

    __tablename__ = "rag_feedback"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    rating = Column(Integer, nullable=False)  # 1 (thumbs down) or -1 (thumbs up)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def to_dict(self):
        return {
            "id": str(self.id),
            "question": self.question,
            "answer": self.answer,
            "rating": self.rating,
            "created_at": self.created_at.isoformat()
        }
