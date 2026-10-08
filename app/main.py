from fastapi import FastAPI

from app.api.files import router as files_router
from app.core.config import settings

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="High-performance backend API for processing geospatial files and calculating metric measurements.",
    version="1.0.0",
)

app.include_router(files_router)


@app.get("/", tags=["Health"])
def root():
    return {
        "message": "Geospatial Measurement API is running"
    }


@app.get("/health", tags=["Health"])
def health():
    return {
        "status": "ok"
    }
