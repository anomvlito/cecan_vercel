import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from api.routes import publications

app = FastAPI(
    title="CECAN API",
    description="Plataforma de gestión de publicaciones científicas CECAN",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(publications.router, prefix="/api")


@app.get("/health")
def health_check() -> dict:
    return {"status": "ok", "version": "1.0.0"}
