from fastapi import APIRouter, HTTPException
import time
import logging

from app.models.schemas import (
    QueryRequest, RetrieveResponse,
    GenerateRequest, GenerateResponse,
    ChatRequest, ChatResponse,
)
from app.services.retriever import retrieve_documents
from app.services.generator import generate_exam
from app.services.intent import detect_intent, extract_doc_type, extract_course_hint

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1", tags=["study"])

# ── TTL cache for /courses ─────────────────────────────────────────────────────
_courses_cache: dict = {"data": None, "ts": 0.0}
COURSES_TTL = 120  # seconds


def _get_courses_cached() -> dict:
    now = time.time()
    if _courses_cache["data"] is not None and now - _courses_cache["ts"] < COURSES_TTL:
        return _courses_cache["data"]

    from app.core.vectorstore import get_qdrant_client
    from app.core.config import get_settings
    settings = get_settings()
    client = get_qdrant_client()

    courses: dict[str, set] = {}
    offset = None
    while True:
        results, next_offset = client.scroll(
            collection_name=settings.qdrant_collection,
            limit=500,
            offset=offset,
            with_payload=["course", "doc_type"],
            with_vectors=False,
        )
        for point in results:
            course = point.payload.get("course", "Unknown")
            doc_type = point.payload.get("doc_type", "other")
            courses.setdefault(course, set()).add(doc_type)
        if next_offset is None:
            break
        offset = next_offset

    data = {
        "courses": [
            {"name": c, "doc_types": sorted(list(dt))}
            for c, dt in sorted(courses.items())
        ]
    }
    _courses_cache["data"] = data
    _courses_cache["ts"] = now
    return data


def invalidate_courses_cache():
    _courses_cache["data"] = None
    _courses_cache["ts"] = 0.0


# ── Routes ─────────────────────────────────────────────────────────────────────

@router.post("/retrieve", response_model=RetrieveResponse)
async def retrieve(req: QueryRequest):
    try:
        return retrieve_documents(
            query=req.query,
            course=req.course,
            doc_type=req.doc_type.value if req.doc_type else None,
            year=req.year,
            top_k=req.top_k,
        )
    except Exception as e:
        logger.exception("Retrieve failed")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate", response_model=GenerateResponse)
async def generate(req: GenerateRequest):
    if not req.course.strip():
        raise HTTPException(status_code=422, detail="Course name cannot be empty.")
    try:
        return generate_exam(req)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.exception("Generation failed")
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")


@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    intent = detect_intent(req.message)
    doc_type = extract_doc_type(req.message)
    known_courses = [c["name"] for c in _get_courses_cached().get("courses", [])]
    course_hint = extract_course_hint(req.message, known_courses)

    if intent == "retrieve":
        try:
            results = retrieve_documents(
                query=req.message,
                course=course_hint,
                doc_type=doc_type,
                top_k=5,
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

        if not results.results:
            response_text = (
                "I couldn't find matching documents. "
                "Try including the course name and document type, "
                "e.g. *'Quiz 1 of Data Structures'*."
            )
        else:
            top = results.results[0]
            max_snippet = 1200
            snippet = top.content[:max_snippet].replace("\n", " ")
            response_text = (
                f"Found **{results.total}** result(s)"
                + (f" in **{course_hint}**" if course_hint else "")
                + f".\n\nTop match: **{top.filename}** ({top.course} · {top.doc_type})\n\n"
                f"> {snippet}{'...' if len(top.content) > max_snippet else ''}"
            )

        return ChatResponse(
            intent="retrieve",
            response=response_text,
            structured_data=results.model_dump(),
        )

    elif intent == "generate":
        hints = []
        if course_hint:
            hints.append(f"**Course:** {course_hint}")
        else:
            hints.append("**Course:** *(not detected — please specify)*")
        hints.append(f"**Type:** {doc_type}" if doc_type else "**Type:** *(quiz / mid / final?)*")

        return ChatResponse(
            intent="generate",
            response=(
                "I can generate that! Here is what I detected:\n\n"
                + "\n".join(f"- {h}" for h in hints)
                + "\n\nUse the **Generate Exam** panel in the sidebar to confirm and generate."
            ),
            structured_data={"detected_course": course_hint, "detected_doc_type": doc_type},
        )

    else:
        return ChatResponse(
            intent="clarify",
            response=(
                "I can help with two things:\n\n"
                "1. **Find** a past exam — *'Give me Quiz 1 of Data Structures'*\n"
                "2. **Generate** a new exam — *'Create a mid-term for OOP'*\n\n"
                "What would you like to do?"
            ),
        )


@router.get("/courses")
async def list_courses():
    """List all unique courses (cached for 2 minutes)."""
    return _get_courses_cached()


@router.post("/courses/refresh")
async def refresh_courses():
    """Bust the cache and return fresh course list."""
    invalidate_courses_cache()
    return _get_courses_cached()


# ── PDF Export ─────────────────────────────────────────────────────────────────

from fastapi import Response
from pydantic import BaseModel

class ExportRequest(BaseModel):
    exam_markdown: str
    answer_key_markdown: str | None = None
    course: str = ""
    doc_type: str = ""


@router.post("/export/pdf")
async def export_pdf(req: ExportRequest):
    """Convert exam markdown to a downloadable PDF."""
    from app.services.pdf_export import markdown_to_pdf
    try:
        pdf_bytes = markdown_to_pdf(
            exam_markdown=req.exam_markdown,
            answer_key_markdown=req.answer_key_markdown,
            course=req.course,
            doc_type=req.doc_type,
        )
        filename = f"{req.course or 'exam'}_{req.doc_type or 'exam'}.pdf".replace(" ", "_").lower()
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )
    except Exception as e:
        logger.exception("PDF export failed")
        raise HTTPException(status_code=500, detail=f"PDF export failed: {e}")