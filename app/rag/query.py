import logging
from typing import List, Optional, Dict, Any
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession
import httpx

from app.db.models import Chunk, Document
from app.rag.embeddings import embedding_model
from app.core.config import settings

logger = logging.getLogger(__name__)


class RAGQueryEngine:
    """Handle RAG queries: retrieval and generation."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def query(
        self,
        question: str,
        top_k: int = None,
        filters: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Execute RAG query: retrieve relevant chunks and generate answer.

        Args:
            question: User question
            top_k: Number of chunks to retrieve (default from config)
            filters: Optional filters (e.g., {"doc_id": "xxx"})

        Returns:
            dict with keys: answer, citations, refusal
        """
        top_k = top_k or settings.top_k

        # Retrieve relevant chunks
        try:
            chunks = await self._retrieve(question, top_k, filters)
        except Exception as e:
            logger.error(f"Retrieval failed: {e}")
            return {
                "answer": "",
                "citations": [],
                "refusal": f"检索失败: {str(e)}"
            }

        # Check if we have enough evidence
        if not chunks:
            return {
                "answer": "",
                "citations": [],
                "refusal": "未找到相关文档。请先上传相关资料或尝试其他关键词。"
            }

        if len(chunks) < 3 or chunks[0]["score"] < settings.score_threshold:
            return {
                "answer": "",
                "citations": chunks[:3],  # Show what we found
                "refusal": "相关度不足，无法基于现有文档生成可靠答案。建议提供更具体的问题或上传更多相关资料。"
            }

        # Generate answer using retrieved chunks
        try:
            answer = await self._generate(question, chunks)
            return {
                "answer": answer,
                "citations": chunks,
                "refusal": None
            }
        except Exception as e:
            logger.error(f"Generation failed: {e}")
            return {
                "answer": "",
                "citations": chunks,
                "refusal": f"答案生成失败: {str(e)}"
            }

    async def _retrieve(
        self,
        question: str,
        top_k: int,
        filters: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant chunks using vector similarity search.

        Args:
            question: User question
            top_k: Number of results
            filters: Optional filters

        Returns:
            List of dicts with keys: chunk_id, snippet, score, source_path, metadata
        """
        # Generate question embedding
        question_embedding = embedding_model.encode_single(question)
        embedding_array = "[" + ",".join(map(str, question_embedding)) + "]"

        # Build SQL query with optional filters
        where_clause = ""
        if filters and "doc_id" in filters:
            where_clause = f"AND c.doc_id = '{filters['doc_id']}'::uuid"

        # Vector similarity search using cosine distance
        sql_query = text(f"""
            SELECT
                c.chunk_id,
                c.text as snippet,
                c.metadata,
                1 - (c.embedding <=> :embedding::vector) as score,
                d.title,
                d.source_path
            FROM chunks c
            JOIN documents d ON c.doc_id = d.doc_id
            WHERE c.embedding IS NOT NULL
            {where_clause}
            ORDER BY c.embedding <=> :embedding::vector
            LIMIT :top_k
        """)

        result = await self.db.execute(
            sql_query,
            {"embedding": embedding_array, "top_k": top_k}
        )

        rows = result.fetchall()
        chunks = []
        for row in rows:
            chunks.append({
                "chunk_id": str(row.chunk_id),
                "snippet": row.snippet,
                "score": float(row.score),
                "source_path": row.source_path,
                "title": row.title,
                "metadata": row.metadata
            })

        logger.info(f"Retrieved {len(chunks)} chunks for query")
        return chunks

    async def _generate(self, question: str, chunks: List[Dict]) -> str:
        """
        Generate answer using Ollama LLM based on retrieved chunks.

        Args:
            question: User question
            chunks: Retrieved chunks

        Returns:
            Generated answer with citations
        """
        # Build context from chunks
        context_parts = []
        for i, chunk in enumerate(chunks, 1):
            context_parts.append(
                f"[{i}] 来源: {chunk['title']}\n{chunk['snippet']}"
            )
        context = "\n\n".join(context_parts)

        # Build prompt
        prompt = f"""你是一个专业的企业知识库助手。请基于以下参考文档回答用户问题。

参考文档:
{context}

问题: {question}

回答要求:
1. 仅基于参考文档回答,不要编造信息
2. 在相关句子后添加引用标记,如[1][2]
3. 如果文档内容不足以回答问题,明确说明
4. 保持回答简洁准确

回答:"""

        # Call Ollama API
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    f"{settings.ollama_url}/api/generate",
                    json={
                        "model": settings.ollama_model,
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "temperature": 0.3,
                            "top_p": 0.9,
                            "num_predict": 512
                        }
                    }
                )
                response.raise_for_status()
                result = response.json()
                answer = result.get("response", "").strip()
                return answer

        except httpx.RequestError as e:
            logger.error(f"Ollama API request failed: {e}")
            raise
        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            raise
