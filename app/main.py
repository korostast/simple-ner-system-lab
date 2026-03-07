"""
Main FastAPI application for NER System
"""

import json
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api import categories, entities, explanations, llm, texts
from app.core.config import settings
from app.core.logger import logger
from app.database.neo4j_client import neo4j_client
from app.repositories.category_repository import CategoryRepository
from app.services.ner_service import ner_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    logger.info("Starting NER System...")
    try:
        neo4j_client.initialize_schema()
        logger.info("Database schema initialized")
        CategoryRepository.initialize_default_categories()
        logger.info("Default NER categories initialized")
    except Exception as e:
        logger.exception(f"Failed to initialize application: {e}")
        raise

    yield

    logger.info("Shutting down NER System...")
    neo4j_client.close()
    logger.info("Database connection closed")


app = FastAPI(
    title="NER System",
    description="Named Entity Recognition and Management System with GLiNER, Neo4j, and LLM integration",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(entities.router)
app.include_router(texts.router)
app.include_router(categories.router)
app.include_router(explanations.router)
app.include_router(llm.router, prefix="/api/llm", tags=["LLM"])

# Frontend
static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


@app.get("/")
async def root():
    """Serve the web application"""
    index_path = static_dir / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path))
    return {
        "message": "NER System API",
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/health",
        "web_ui": "Open http://localhost:8000/ in your browser",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    # Check database connection
    try:
        neo4j_client.execute_query("RETURN 1 as test")
    except Exception:
        database_status = False
        logger.exception("Couldn't connect to database")
    else:
        database_status = True

    # Check models status
    try:
        gliner_status = bool(ner_service.model)
        stanza_en_status = bool(ner_service.nlp_en)
        stanza_ru_status = bool(ner_service.nlp_ru)
        # llm_status = TODO check server connectivity

        models_loaded = all([ner_service.model, ner_service.nlp_en, ner_service.nlp_ru])

        if not models_loaded:
            raise HTTPException(
                status_code=503,
                detail="Models not loaded. Please run ./scripts/download_models.sh to download models.",
            )

        status_overall = database_status & gliner_status & stanza_en_status & stanza_ru_status

        if not status_overall:
            logger.error(
                json.dumps(
                    {
                        "status_ok": status_overall,
                        "database_ok": database_status,
                        "models": {
                            "gliner_ok": gliner_status,
                            "stanza_en_ok": stanza_en_status,
                            "stanza_ru_ok": stanza_ru_status,
                            # "llm_ok": TODO,
                        },
                    },
                    indent=2,
                )
            )
            raise HTTPException(
                status_code=503,
                detail="Service not ready yet",
            )

        return {
            "status_ok": status_overall,
            "database_ok": database_status,
            "models": {
                "gliner_ok": gliner_status,
                "stanza_en_ok": stanza_en_status,
                "stanza_ru_ok": stanza_ru_status,
                # "llm_ok": TODO,
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unhealthy")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host=settings.app_host, port=settings.app_port, reload=True)
