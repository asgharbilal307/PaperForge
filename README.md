#PaperForge

<<<<<<< Updated upstream
A smart university study assistant that indexes course materials and helps with:

- Semantic retrieval of past exams (quiz/mid/final/etc.)
- Generative exam creation using LangChain + Groq LLM
- Conversational chat with intent parsing
- PDF export for generated exams and answer keys

## 🏗️ Architecture

- **Backend (`backend/`)** – FastAPI application:
  - `app/main.py` – startup and health check
  - `app/api/routes.py` – endpoints (`/retrieve`, `/generate`, `/chat`, `/courses`, `/export/pdf`)
  - `app/core/config.py` – environment-based settings
  - `app/core/vectorstore.py` – Qdrant client + embeddings
  - `app/services/` – logic for retrieval, generation, intent parsing, and PDF export
- **Frontend (`frontend/`)** – Streamlit UI (`app.py`)
- **Scripts (`backend/scripts/ingest.py`)** – Ingest course material from GitHub (PDF, DOCX, PPTX, IPYNB, Markdown, TXT, code)
- **Qdrant (`qdrant_data/`)** – stores vector embeddings locally

## ⚡ Features

- **Retrieve** relevant exam documents with semantic search
- **Generate** new exams with difficulty, question type, topics, and optional answer key
- **Chat** interface interprets natural queries and routes them to retrieve/generate
- **Export PDF** for exams and answer keys

## ⚙️ Setup

1. Clone the repo and create a virtual environment:
=======
> A university study assistant that indexes course materials in Qdrant and provides:
> - semantic retrieval of past exams (quiz/mid/final/etc.)
> - generative exam creation via LangChain + Groq LLM
> - smart conversational “chat” intent parsing
> - PDF export for generated exam and answer key

## ✅ Architecture

- `backend/` : FastAPI application
  - `app/main.py` : FastAPI startup + health check
  - `app/api/routes.py` : endpoints (`/retrieve`, `/generate`, `/chat`, `/courses`, `/export/pdf`)
  - `app/core/config.py` : env-based settings
  - `app/core/vectorstore.py` : Qdrant client + embeddings
  - `app/services/retriever.py` : semantic retrieval + filters
  - `app/services/generator.py` : RAG exam generation
  - `app/services/intent.py` : intent utilities
  - `app/services/pdf_export.py` : markdown -> PDF (via WeasyPrint / wkhtmltopdf style)
- `backend/scripts/ingest.py` : GitHub repo ingestion (PDF, DOCX, PPTX, IPYNB, markdown, txt, code files)
- `frontend/` : Streamlit UI (`app.py`)
- `start.py` : run backend + frontend concurrently
- `qdrant_data/` : local Qdrant persisted collection files

## 🔧 Requirements

- Python 3.11+ (recommended)
- `pip install -r backend/requirements.txt`
- Local Qdrant is embedded, no separate Docker needed
- `streamlit` for frontend
- A valid Groq API key and GitHub token + repo for ingestion model data

## 🛠️ Environment Variables

Create a `.env` in the repository root with:

```env
GROQ_API_KEY=<your_groq_api_key>
GITHUB_TOKEN=<your_github_pat_or_token>
GITHUB_REPO=<owner/repo>  # repo containing study material for ingestion
QDRANT_PATH=./backend/qdrant_data   # optional, local persistence path
APP_ENV=development
LOG_LEVEL=INFO
```

> Note: `app/core/config.py` uses `pydantic-settings` and auto-loads `.env`.

## 🚀 Local Setup

1. Create venv and activate:
>>>>>>> Stashed changes

```bash
python -m venv venv
source venv/bin/activate
<<<<<<< Updated upstream
=======
```

2. Install dependencies:

```bash
pip install -r backend/requirements.txt
pip install streamlit
```

3. Ingest course docs from GitHub:

```bash
python backend/scripts/ingest.py --force
```

4. Run app locally:

```bash
python start.py
```

- Backend: `http://localhost:8000`
- Frontend: `http://localhost:8501`

## 🧩 API Endpoints

Base path: `http://localhost:8000/api/v1`

- POST `/retrieve`
  - body: `{ "query": "...", "course": "...", "doc_type": "quiz|mid|final|...", "year": "2024", "top_k": 5 }`
  - returns `RetrieveResponse`
- POST `/generate`
  - body: `{ "course": "Data Structures", "doc_type": "mid", "difficulty": "medium", "question_type": "mixed", "num_questions": 10, "topics": ["trees","hashing"], "include_answer_key": true }`
  - returns `GenerateResponse`
- POST `/chat`
  - body: `{ "message": "Give me Quiz 1 of Algorithms" }`
  - returns `ChatResponse` with intent router
- GET `/courses` and POST `/courses/refresh`
  - list known courses + derived doc types
- POST `/export/pdf`
  - body: `{ "exam_markdown": "...", "answer_key_markdown": "...", "course": "...", "doc_type": "..." }`
  - returns PDF bytes

## 🧠 Intent Parsing

`app/services/intent.py` does intent classification (retrieve/generate/clarify) and extracts doc types/course hints.

## 📦 Embeddings + Vector Store

- `app/core/vectorstore.py` uses `SentenceTransformer` (`all-MiniLM-L6-v2`) and Qdrant local collection `uni_study_materials`.
- Ingest script chunking: 600 char chunk size with 100 overlap

## 🛡️ Health check

- GET `/health` returns `{"status": "ok", "env": "development"}`

## 🧪 Development notes

- Streamlit UI uses wizard-like chat bubbles and side panels for direct retrieve + generate calls.
- `/chat` is safe fallback for clarifying queries.
- Generation uses Groq `llama-3.3-70b-versatile` with RAG context and answer key optional.

## 📝 Troubleshooting

- If empty results in retrieval, verify Qdrant collection has indexed docs and `course`/`doc_type` filters are correct.
- If generator fails: check `GROQ_API_KEY` and LLM quota.
- If ingestion hits `GithubException`, check GitHub token and repo path.

---

Big win: your project is now documented and runnable from `README.md`. You can iterate with additional sections as required.
>>>>>>> Stashed changes
