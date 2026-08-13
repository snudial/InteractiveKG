"""Entry point for the InteractiveKG backend API."""

import logging
import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.chatbot_routes import router as chatbot_router
from app.api.kgot_routes import router as kgot_router
from app.database.connection import db_connection
from app.routers.graph_router import router as graph_router

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DEFAULT_ALLOWED_ORIGINS = (
    "http://localhost:3000,http://localhost:3001,http://localhost:3002,http://localhost:3003"
)


def get_allowed_origins() -> list[str]:
    """Parse ALLOWED_ORIGINS into a list, dropping blanks and stray whitespace."""
    raw = os.getenv("ALLOWED_ORIGINS", DEFAULT_ALLOWED_ORIGINS)
    return [origin.strip() for origin in raw.split(",") if origin.strip()]


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Open the Neo4j connection on startup and close it on shutdown."""
    logger.info("Starting Knowledge Graph Management System API...")
    if db_connection.connect():
        logger.info("Database connection established")
    else:
        logger.error("Failed to establish database connection")

    yield

    logger.info("Shutting down API...")
    db_connection.close()


app = FastAPI(
    title="Knowledge Graph Management System",
    description="A system for managing knowledge graphs with Neo4j",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_allowed_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(graph_router)
app.include_router(kgot_router)
app.include_router(chatbot_router)


@app.get("/")
async def root():
    """Report the API name and version."""
    return {"message": "Knowledge Graph Management System API", "version": "1.0.0"}


@app.get("/health")
async def health_check():
    """Liveness probe."""
    return {"status": "healthy", "message": "API is running"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=os.getenv("API_HOST", "0.0.0.0"),
        port=int(os.getenv("API_PORT", "8000")),
        reload=os.getenv("DEBUG", "True").lower() == "true",
    )
