from qdrant_client.models import Filter, FieldCondition, MatchValue
from typing import Optional
import logging

from app.core.config import get_settings
from app.core.vectorstore import get_qdrant_client, embed_texts
from app.models.schemas import DocumentChunk, RetrieveResponse

logger = logging.getLogger(__name__)


def build_filter(
    course: Optional[str] = None,
    doc_type: Optional[str] = None,
    year: Optional[str] = None,
) -> Optional[Filter]:
    """
    Build a Qdrant filter only when the user explicitly provides constraints.
    If nothing is provided, returns None so the search covers the entire collection.
    """
    conditions = []

    if course:
        conditions.append(FieldCondition(key="course", match=MatchValue(value=course.lower())))
    if doc_type:
        conditions.append(FieldCondition(key="doc_type", match=MatchValue(value=doc_type)))
    if year:
        conditions.append(FieldCondition(key="year", match=MatchValue(value=year)))

    return Filter(must=conditions) if conditions else None


def retrieve_documents(
    query: str,
    course: Optional[str] = None,
    doc_type: Optional[str] = None,
    year: Optional[str] = None,
    top_k: int = 5,
) -> RetrieveResponse:
    """
    Embed the query and search Qdrant.
    - If course/doc_type/year are provided they act as filters.
    - If none are provided the search is global across all indexed files.
    - Score threshold is intentionally low (0.2) so fuzzy matches still surface.
    """
    settings = get_settings()
    client = get_qdrant_client()

    query_vector = embed_texts([query])[0]
    payload_filter = build_filter(course=course, doc_type=doc_type, year=year)

    results = client.search(
        collection_name=settings.qdrant_collection,
        query_vector=query_vector,
        query_filter=payload_filter,
        limit=top_k,
        with_payload=True,
        score_threshold=0.2,
    )

    chunks = []
    for hit in results:
        p = hit.payload
        chunks.append(DocumentChunk(
            content=p.get("content", ""),
            course=p.get("course", "Unknown"),
            doc_type=p.get("doc_type", "other"),
            filename=p.get("filename", ""),
            year=p.get("year"),
            score=round(hit.score, 4),
            source_url=p.get("source_url"),
        ))

    return RetrieveResponse(
        intent="retrieve",
        query=query,
        results=chunks,
        total=len(chunks),
    )