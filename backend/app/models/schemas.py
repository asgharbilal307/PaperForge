from pydantic import BaseModel, Field
from typing import Optional, Literal
from enum import Enum


class DocType(str, Enum):
    QUIZ = "quiz"
    MID = "mid"
    FINAL = "final"
    NOTES = "notes"
    ASSIGNMENT = "assignment"
    OTHER = "other"


class Difficulty(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class QuestionType(str, Enum):
    MCQ = "mcq"
    SHORT = "short"
    LONG = "long"
    MIXED = "mixed"


# ── Query request ───────────────────────────────────────────────────────────

class QueryRequest(BaseModel):
    query: str = Field(..., min_length=3, description="Natural language query")
    course: Optional[str] = Field(None, description="Filter by course name")
    doc_type: Optional[DocType] = Field(None, description="Filter by document type")
    year: Optional[str] = Field(None, description="Filter by year, e.g. '2023'")
    top_k: int = Field(10, ge=1, le=20)


class DocumentChunk(BaseModel):
    content: str
    course: str
    doc_type: str
    filename: str
    year: Optional[str]
    score: float
    source_url: Optional[str]


class RetrieveResponse(BaseModel):
    intent: Literal["retrieve"]
    query: str
    results: list[DocumentChunk]
    total: int


# ── Generate request ─────────────────────────────────────────────────────────

class GenerateRequest(BaseModel):
    course: str = Field(..., min_length=1, description="Course name, e.g. 'Data Structures'")
    doc_type: DocType = Field(..., description="Type of exam to generate")
    difficulty: Difficulty = Field(Difficulty.MEDIUM)
    question_type: QuestionType = Field(QuestionType.MIXED)
    num_questions: int = Field(10, ge=3, le=30)
    topics: Optional[list[str]] = Field(None, description="Specific topics to focus on")
    include_answer_key: bool = Field(True)
    duration_minutes: Optional[int] = Field(None, description="Exam duration hint")


class GenerateResponse(BaseModel):
    intent: Literal["generate"]
    course: str
    doc_type: str
    exam_markdown: str
    answer_key_markdown: Optional[str]
    metadata: dict


# ── Smart chat (auto-detects intent) ────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str
    history: list[dict] = Field(default_factory=list)


class ChatResponse(BaseModel):
    intent: Literal["retrieve", "generate", "clarify"]
    response: str
    structured_data: Optional[dict] = None