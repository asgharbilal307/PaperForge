from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PayloadSchemaType
from sentence_transformers import SentenceTransformer
from functools import lru_cache
import logging
import os

from app.core.config import get_settings

logger = logging.getLogger(__name__)

# Singleton client — shared across the process
_qdrant_client: QdrantClient | None = None


def get_qdrant_client() -> QdrantClient:
    """
    Returns a Qdrant client.
    - If QDRANT_PATH is set, persists data to that local folder (recommended).
    - Otherwise runs fully in-memory (data lost on restart, fine for dev/demo).
    No Docker required for either mode.
    """
    global _qdrant_client
    if _qdrant_client is not None:
        return _qdrant_client

    settings = get_settings()
    qdrant_path = settings.qdrant_path

    if qdrant_path:
        logger.info(f"Qdrant: persisting to local folder → {qdrant_path}")
        _qdrant_client = QdrantClient(path=qdrant_path)
    else:
        logger.info("Qdrant: running in-memory (set QDRANT_PATH to persist data)")
        _qdrant_client = QdrantClient(":memory:")

    return _qdrant_client


@lru_cache()
def get_embedding_model() -> SentenceTransformer:
    settings = get_settings()
    logger.info(f"Loading embedding model: {settings.embedding_model}")
    return SentenceTransformer(settings.embedding_model)


def embed_texts(texts: list[str]) -> list[list[float]]:
    model = get_embedding_model()
    return model.encode(texts, show_progress_bar=False).tolist()


def ensure_collection_exists():
    """Create Qdrant collection if it doesn't exist yet."""
    settings = get_settings()
    client = get_qdrant_client()

    existing = [c.name for c in client.get_collections().collections]
    if settings.qdrant_collection in existing:
        logger.info(f"Collection '{settings.qdrant_collection}' already exists.")
        return

    client.create_collection(
        collection_name=settings.qdrant_collection,
        vectors_config=VectorParams(
            size=settings.embedding_dim,
            distance=Distance.COSINE,
        ),
    )

    # Create payload indexes for fast filtering
    for field in ["course", "doc_type", "year"]:
        client.create_payload_index(
            collection_name=settings.qdrant_collection,
            field_name=field,
            field_schema=PayloadSchemaType.KEYWORD,
        )

    logger.info(f"Collection '{settings.qdrant_collection}' created with indexes.")
