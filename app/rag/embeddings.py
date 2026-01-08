import logging
from typing import List, Optional
import numpy as np
from sentence_transformers import SentenceTransformer
from app.core.config import settings

logger = logging.getLogger(__name__)


class EmbeddingModel:
    """Handle text embedding generation using local models."""

    def __init__(self):
        self.model: Optional[SentenceTransformer] = None
        self.device = settings.embed_device

    def load(self):
        """Load embedding model (lazy loading)."""
        if self.model is None:
            try:
                logger.info(f"Loading embedding model from {settings.embed_model_path}")
                self.model = SentenceTransformer(
                    settings.embed_model_path,
                    device=self.device
                )
                logger.info("Embedding model loaded successfully")
            except Exception as e:
                logger.error(f"Failed to load embedding model: {e}")
                raise

    def encode(self, texts: List[str]) -> List[List[float]]:
        """
        Encode texts to embeddings.

        Args:
            texts: List of text strings

        Returns:
            List of embedding vectors
        """
        if self.model is None:
            self.load()

        try:
            embeddings = self.model.encode(
                texts,
                batch_size=settings.embed_batch_size,
                show_progress_bar=False,
                normalize_embeddings=True  # L2 normalization for cosine similarity
            )
            return embeddings.tolist()
        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            raise

    def encode_single(self, text: str) -> List[float]:
        """Encode single text to embedding."""
        return self.encode([text])[0]


# Global embedding model instance
embedding_model = EmbeddingModel()
