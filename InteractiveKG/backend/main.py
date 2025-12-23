from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os
import logging
from dotenv import load_dotenv

from app.routers.graph_router import router as graph_router
from app.api.kgot_routes import router as kgot_router
from app.api.chatbot_routes import router as chatbot_router
from app.database.connection import db_connection

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

app = FastAPI(
    title="Knowledge Graph Management System",
    description="A system for managing knowledge graphs with Neo4j",
    version="1.0.0"
)

allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:3001,http://localhost:3002,http://localhost:3003").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(graph_router)
app.include_router(kgot_router)
app.include_router(chatbot_router)
@app.on_event("startup")
async def startup_event():

    logger.info("Starting Knowledge Graph Management System API...")
    if db_connection.connect():
        logger.info("Database connection established")
    else:
        logger.error("Failed to establish database connection")
@app.on_event("shutdown")
async def shutdown_event():

    logger.info("Shutting down API...")
    db_connection.close()
@app.get("/")
async def root():

    return {"message": "Knowledge Graph Management System API", "version": "1.0.0"}
@app.get("/health")
async def health_check():

    return {"status": "healthy", "message": "API is running"}
if __name__ == "__main__":
    import uvicorn

    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", 8000))
    debug = os.getenv("DEBUG", "True").lower() == "true"

    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=debug
    )