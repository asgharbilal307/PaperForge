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

    # Deduplicate by raw_path — one result per file
    seen_paths = {}
    for hit in results:
        path = hit.payload.get("raw_path", "")
        if path not in seen_paths or hit.score > seen_paths[path].score:
            seen_paths[path] = hit

    chunks = []
    for hit in seen_paths.values():
        p = hit.payload
        # Fetch the FULL document content by reassembling all chunks
        full_content = fetch_full_document(p.get("raw_path", ""))
        chunks.append(DocumentChunk(
            content=full_content,  # full document now
            course=p.get("course", "Unknown"),
            doc_type=p.get("doc_type", "other"),
            filename=p.get("filename", ""),
            year=p.get("year"),
            score=round(hit.score, 4),
            source_url=p.get("source_url"),
        ))

    # Sort by score descending
    chunks.sort(key=lambda c: c.score, reverse=True)

    return RetrieveResponse(
        intent="retrieve",
        query=query,
        results=chunks,
        total=len(chunks),
    )

# Add this new function
def fetch_full_document(raw_path: str) -> str:
    """Fetch all chunks of a file and reassemble in order."""
    settings = get_settings()
    client = get_qdrant_client()

    results, _ = client.scroll(
        collection_name=settings.qdrant_collection,
        scroll_filter=Filter(
            must=[FieldCondition(key="raw_path", match=MatchValue(value=raw_path))]
        ),
        limit=500,
        with_payload=True,
        with_vectors=False,
    )

    # Sort by chunk index and join
    chunks = sorted(results, key=lambda r: r.payload.get("chunk_index", 0))
    return "\n".join(r.payload.get("content", "") for r in chunks)