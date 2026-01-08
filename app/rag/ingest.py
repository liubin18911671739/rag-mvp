import os
import hashlib
from pathlib import Path
from typing import List, Optional
import logging
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Document, Chunk
from app.core.config import settings

logger = logging.getLogger(__name__)


class DocumentIngestor:
    """Handle document ingestion, chunking, and embedding."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.chunk_size = settings.chunk_size
        self.chunk_overlap = settings.chunk_overlap

    async def ingest_directory(self, dir_path: str) -> dict:
        """
        Ingest all supported documents from a directory.

        Args:
            dir_path: Path to directory containing documents

        Returns:
            dict with statistics: {total, succeeded, failed, errors}
        """
        results = {"total": 0, "succeeded": 0, "failed": 0, "errors": []}

        try:
            path = Path(dir_path)
            if not path.exists() or not path.is_dir():
                raise ValueError(f"Invalid directory path: {dir_path}")

            # Find all supported files
            supported_extensions = {'.txt', '.md'}
            files = [
                f for f in path.rglob('*')
                if f.is_file() and f.suffix.lower() in supported_extensions
            ]

            results["total"] = len(files)
            logger.info(f"Found {len(files)} documents to ingest")

            for file_path in files:
                try:
                    await self.ingest_file(str(file_path))
                    results["succeeded"] += 1
                    logger.info(f"Successfully ingested: {file_path.name}")
                except Exception as e:
                    results["failed"] += 1
                    error_msg = f"{file_path.name}: {str(e)}"
                    results["errors"].append(error_msg)
                    logger.error(f"Failed to ingest {file_path.name}: {e}")

        except Exception as e:
            logger.error(f"Directory ingestion failed: {e}")
            raise

        return results

    async def ingest_file(self, file_path: str) -> Document:
        """
        Ingest a single document: read, chunk, embed, and store.

        Args:
            file_path: Path to document file

        Returns:
            Document object
        """
        # Read file content
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            # Try with alternative encoding
            with open(file_path, 'r', encoding='gbk') as f:
                content = f.read()

        if not content.strip():
            raise ValueError("File is empty")

        # Calculate content hash for deduplication
        content_hash = hashlib.sha256(content.encode()).hexdigest()

        # Check if document already exists
        existing_doc = await self._get_document_by_hash(content_hash)
        if existing_doc:
            logger.info(f"Document already exists (hash: {content_hash[:8]}...), skipping")
            return existing_doc

        # Create document record
        path_obj = Path(file_path)
        doc = Document(
            title=path_obj.stem,
            source_path=file_path,
            content_hash=content_hash
        )
        self.db.add(doc)
        await self.db.flush()  # Get doc_id without committing

        # Chunk and embed content
        chunks_data = self._chunk_text(content)
        logger.info(f"Created {len(chunks_data)} chunks for {path_obj.name}")

        # Store chunks with embeddings
        for chunk_data in chunks_data:
            chunk = Chunk(
                doc_id=doc.doc_id,
                text=chunk_data["text"],
                metadata=chunk_data["metadata"]
            )
            self.db.add(chunk)

        await self.db.commit()
        await self.db.refresh(doc)

        logger.info(f"Ingested document: {doc.title} ({len(chunks_data)} chunks)")
        return doc

    def _chunk_text(self, text: str) -> List[dict]:
        """
        Split text into overlapping chunks.

        Args:
            text: Input text

        Returns:
            List of dicts with keys: text, metadata
        """
        chunks = []
        start = 0
        chunk_idx = 0

        while start < len(text):
            end = start + self.chunk_size
            chunk_text = text[start:end]

            chunks.append({
                "text": chunk_text,
                "metadata": {
                    "chunk_index": chunk_idx,
                    "char_start": start,
                    "char_end": end,
                    "length": len(chunk_text)
                }
            })

            start += (self.chunk_size - self.chunk_overlap)
            chunk_idx += 1

        return chunks

    async def _get_document_by_hash(self, content_hash: str) -> Optional[Document]:
        """Check if document with given hash already exists."""
        result = await self.db.execute(
            select(Document).where(Document.content_hash == content_hash)
        )
        return result.scalar_one_or_none()

    async def get_documents(self) -> List[Document]:
        """Get all documents."""
        result = await self.db.execute(select(Document).order_by(Document.created_at.desc()))
        return result.scalars().all()
