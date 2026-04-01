from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from app.api.routes import router
from app.core.config import get_settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

settings = get_settings()

app = FastAPI(
    title="UniStudy RAG Assistant",
    description="Retrieve past exams and generate new ones using RAG over your university study materials.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/health")
async def health():
    return {"status": "ok", "env": settings.app_env}


@app.on_event("startup")
async def startup():
    from app.core.vectorstore import ensure_collection_exists
    logger.info("Starting UniStudy RAG API...")
    ensure_collection_exists()
    logger.info("Ready.")