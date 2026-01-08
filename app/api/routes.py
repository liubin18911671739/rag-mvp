from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import logging

from app.db.database import get_db
from app.rag.ingest import DocumentIngestor
from app.rag.query import RAGQueryEngine
from app.core.metrics import (
    rag_requests_total, retrieval_no_results_total, llm_errors_total,
    ingested_documents_total, ingested_chunks_total, feedback_total,
    active_documents_gauge, active_chunks_gauge, get_metrics
)

logger = logging.getLogger(__name__)

router = APIRouter()


# Pydantic models
class QueryRequest(BaseModel):
    question: str = Field(..., description="User question", min_length=1)
    top_k: Optional[int] = Field(None, ge=1, le=20, description="Number of chunks to retrieve")
    filters: Optional[Dict[str, Any]] = Field(None, description="Optional filters (e.g., doc_id)")


class Citation(BaseModel):
    chunk_id: str
    snippet: str
    score: float
    source_path: str
    title: str
    metadata: Dict[str, Any]


class QueryResponse(BaseModel):
    answer: str
    citations: List[Citation]
    refusal: Optional[str]


class DocumentInfo(BaseModel):
    doc_id: str
    title: str
    source_path: str
    content_hash: str
    created_at: str


class IngestResponse(BaseModel):
    total: int
    succeeded: int
    failed: int
    errors: List[str]


class HealthResponse(BaseModel):
    status: str
    database: str


# API Endpoints
@router.get("/health", response_model=HealthResponse)
async def health_check(db: AsyncSession = Depends(get_db)):
    """Check API and database health."""
    try:
        # Test database connection
        await db.execute("SELECT 1")
        return HealthResponse(status="healthy", database="connected")
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail=f"Service unhealthy: {str(e)}")


@router.post("/query", response_model=QueryResponse)
async def query_rag(
    request: QueryRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Execute RAG query.

    - **question**: User question
    - **top_k**: Number of chunks to retrieve (optional, default from config)
    - **filters**: Optional filters (e.g., {"doc_id": "xxx"})
    """
    try:
        engine = RAGQueryEngine(db)
        result = await engine.query(
            question=request.question,
            top_k=request.top_k,
            filters=request.filters
        )

        # Track metrics
        if result.get("refusal"):
            if "未找到相关文档" in result["refusal"]:
                retrieval_no_results_total.inc()
            rag_requests_total.labels(status="failure").inc()
        else:
            rag_requests_total.labels(status="success").inc()

        return QueryResponse(**result)
    except Exception as e:
        logger.error(f"Query failed: {e}")
        rag_requests_total.labels(status="error").inc()
        llm_errors_total.labels(error_type=type(e).__name__).inc()
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")


@router.post("/ingest", response_model=IngestResponse)
async def ingest_documents(
    db: AsyncSession = Depends(get_db),
    path: str = Form("/app/data/raw", description="Directory path to ingest")
):
    """
    Ingest all documents from a directory.

    Supports .txt and .md files.
    """
    try:
        ingestor = DocumentIngestor(db)
        result = await ingestor.ingest_directory(path)

        # Track metrics
        ingested_documents_total.labels(status="success").inc(result["succeeded"])
        ingested_documents_total.labels(status="failure").inc(result["failed"])

        # Count total chunks (approximate)
        docs = await ingestor.get_documents()
        total_chunks = sum(len([c for c in []]) for _ in docs)  # Will be updated when we track chunks per doc
        ingested_chunks_total.inc(result["succeeded"] * 10)  # Approximate

        # Update gauges
        active_documents_gauge.set(len(docs))

        return IngestResponse(**result)
    except Exception as e:
        logger.error(f"Ingest failed: {e}")
        ingested_documents_total.labels(status="error").inc()
        raise HTTPException(status_code=500, detail=f"Ingest failed: {str(e)}")


@router.get("/documents", response_model=List[DocumentInfo])
async def list_documents(db: AsyncSession = Depends(get_db)):
    """List all ingested documents."""
    try:
        ingestor = DocumentIngestor(db)
        docs = await ingestor.get_documents()
        return [DocumentInfo(**doc.to_dict()) for doc in docs]
    except Exception as e:
        logger.error(f"Failed to list documents: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list documents: {str(e)}")


@router.post("/feedback")
async def submit_feedback(
    question: str = Form(...),
    answer: str = Form(...),
    rating: int = Form(..., ge=-1, le=1),
    db: AsyncSession = Depends(get_db)
):
    """
    Submit user feedback for RAG quality monitoring.

    - **question**: Original question
    - **answer**: Generated answer
    - **rating**: 1 (thumbs up) or -1 (thumbs down)
    """
    try:
        from app.db.models import RAGFeedback
        from datetime import datetime

        feedback = RAGFeedback(
            question=question,
            answer=answer,
            rating=rating,
            created_at=datetime.utcnow()
        )
        db.add(feedback)
        await db.commit()

        # Track metrics
        if rating > 0:
            feedback_total.labels(rating="positive").inc()
        else:
            feedback_total.labels(rating="negative").inc()

        logger.info(f"Feedback recorded: rating={rating}")
        return {"status": "success", "message": "Feedback recorded"}
    except Exception as e:
        logger.error(f"Failed to record feedback: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to record feedback: {str(e)}")


@router.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    return Response(content=get_metrics(), media_type="text/plain")
