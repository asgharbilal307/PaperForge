from langchain_groq import ChatGroq
from langchain.prompts import ChatPromptTemplate
from typing import Optional
import logging

from app.core.config import get_settings
from app.core.vectorstore import get_qdrant_client, embed_texts
from app.models.schemas import GenerateRequest, GenerateResponse
from qdrant_client.models import Filter, FieldCondition, MatchValue

logger = logging.getLogger(__name__)

DIFFICULTY_INSTRUCTIONS = {
    "easy":   "Focus on definitions, basic recall, and simple application questions.",
    "medium": "Include conceptual understanding, moderate problem-solving, and application-level questions.",
    "hard":   "Include analysis, synthesis, edge cases, tricky scenarios, and in-depth problem solving.",
}

QUESTION_TYPE_INSTRUCTIONS = {
    "mcq":   "All questions must be multiple-choice with 4 options (A-D). Mark the correct answer.",
    "short": "All questions require short answers (2-5 sentences).",
    "long":  "All questions require detailed essay or problem-solving answers.",
    "mixed": "Mix question types: ~40% MCQ, ~30% short answer, ~30% long answer.",
}

EXAM_GENERATION_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are an expert academic exam generator for university-level computer science courses.
You create well-structured, pedagogically sound exams based on actual course material.

Guidelines:
- Use the provided course material as your primary source
- Ensure questions test different cognitive levels (recall, understanding, application, analysis)
- Format output in clean Markdown
- Number all questions clearly
- For MCQ: provide options A, B, C, D on separate lines
- Separate sections with clear headers
- Be precise and unambiguous in question wording
"""),
    ("human", """Generate a {doc_type} exam for the course: **{course}**

Difficulty: {difficulty}
{difficulty_instruction}

Question types: {question_type}
{question_type_instruction}

Number of questions: {num_questions}
{topics_instruction}
{duration_instruction}

--- COURSE MATERIAL ---
{context}
--- END MATERIAL ---

Generate the exam now. Format it professionally with:
- A header (Course name, Exam type, Total marks, Duration if given)
- Numbered questions
- Clear section dividers if mixing question types
"""),
])

ANSWER_KEY_PROMPT = ChatPromptTemplate.from_messages([
    ("system", "You are an expert exam answer key generator. Provide accurate, detailed answers."),
    ("human", """Generate a complete answer key for the following exam.

For MCQ: state the correct option letter and briefly explain why.
For short/long answers: provide model answers.

--- EXAM ---
{exam_text}
--- END EXAM ---

--- COURSE MATERIAL ---
{context}
--- END MATERIAL ---

Generate the answer key now, numbered to match the exam questions.
"""),
])


def fetch_context(course: str, topics: Optional[list[str]], top_k: int = 15) -> tuple[str, bool]:
    """
    Fetch RAG context for the given course.

    Strategy:
    1. Build a rich query from course name + topics.
    2. Try a filtered search (course field match) first.
    3. If that returns fewer than 3 results, fall back to global semantic search.
       This handles messy folder structures where course names may not match exactly.

    Returns (context_string, used_fallback).
    """
    settings = get_settings()
    client = get_qdrant_client()

    query_text = course
    if topics:
        query_text += " " + " ".join(topics)

    query_vector = embed_texts([query_text])[0]

    # Attempt 1: filtered by course name
    course_filter = Filter(
        must=[FieldCondition(key="course", match=MatchValue(value=course.lower()))]
    )
    results = client.search(
        collection_name=settings.qdrant_collection,
        query_vector=query_vector,
        query_filter=course_filter,
        limit=top_k,
        with_payload=True,
    )

    used_fallback = False

    # Attempt 2: global search if filtered results are thin
    if len(results) < 3:
        logger.info(
            f"Only {len(results)} results for course filter '{course}'. "
            f"Falling back to global semantic search."
        )
        results = client.search(
            collection_name=settings.qdrant_collection,
            query_vector=query_vector,
            query_filter=None,
            limit=top_k,
            with_payload=True,
        )
        used_fallback = len(results) > 0

    if not results:
        logger.warning(f"No context found anywhere for: '{course}'")
        return (
            f"[No course material found for '{course}'. "
            f"Generate a reasonable exam based on standard CS curriculum for this topic.]",
            True,
        )

    context_parts = []
    for hit in results:
        p = hit.payload
        header = f"[{p.get('doc_type','doc').upper()} | {p.get('filename','')} | {p.get('full_path', p.get('raw_path',''))}]"
        context_parts.append(f"{header}\n{p.get('content', '')}")

    return "\n\n---\n\n".join(context_parts), used_fallback


def generate_exam(request: GenerateRequest) -> GenerateResponse:
    """RAG pipeline: fetch context -> generate exam -> optionally generate answer key."""
    settings = get_settings()

    if not request.course.strip():
        raise ValueError("Course name is required.")

    llm = ChatGroq(
        api_key=settings.groq_api_key,
        model="llama-3.3-70b-versatile",
        temperature=0.4,
        max_tokens=4096,
    )

    context, used_fallback = fetch_context(
        course=request.course,
        topics=request.topics,
    )

    topics_instruction = (
        f"Focus specifically on these topics: {', '.join(request.topics)}"
        if request.topics else ""
    )
    duration_instruction = (
        f"This exam should be completable in {request.duration_minutes} minutes."
        if request.duration_minutes else ""
    )

    try:
        exam_chain = EXAM_GENERATION_PROMPT | llm
        exam_result = exam_chain.invoke({
            "doc_type":              request.doc_type.value.upper(),
            "course":                request.course,
            "difficulty":            request.difficulty.value.upper(),
            "difficulty_instruction": DIFFICULTY_INSTRUCTIONS[request.difficulty.value],
            "question_type":         request.question_type.value.upper(),
            "question_type_instruction": QUESTION_TYPE_INSTRUCTIONS[request.question_type.value],
            "num_questions":         request.num_questions,
            "topics_instruction":    topics_instruction,
            "duration_instruction":  duration_instruction,
            "context":               context,
        })
        exam_markdown = exam_result.content
    except Exception as e:
        logger.exception("LLM call failed during exam generation")
        raise RuntimeError(f"Exam generation failed: {e}") from e

    answer_key_markdown = None
    if request.include_answer_key:
        try:
            key_chain = ANSWER_KEY_PROMPT | llm
            key_result = key_chain.invoke({
                "exam_text": exam_markdown,
                "context":   context,
            })
            answer_key_markdown = key_result.content
        except Exception as e:
            logger.warning(f"Answer key generation failed (non-fatal): {e}")
            answer_key_markdown = "_Answer key generation failed. Please try again._"

    return GenerateResponse(
        intent="generate",
        course=request.course,
        doc_type=request.doc_type.value,
        exam_markdown=exam_markdown,
        answer_key_markdown=answer_key_markdown,
        metadata={
            "difficulty":            request.difficulty.value,
            "question_type":         request.question_type.value,
            "num_questions":         request.num_questions,
            "topics":                request.topics,
            "context_chunks_used":   len([p for p in context.split("---") if p.strip()]),
            "used_fallback_context": used_fallback,
        },
    )