# UniStudy RAG Assistant

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

```bash
python -m venv venv
source venv/bin/activate
