from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.api.routes import health
from app.core.config import settings
from app.core.version import VERSION

app = FastAPI(
    title=settings.project_name,
    version=VERSION,
    description=(
        "API for SmartKids – Smile & Grow. Parent-reported symptoms are observations, "
        "not diagnoses; community signals require human review before any alert."
    ),
    openapi_url="/api/openapi.json",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/api")
app.include_router(api_router, prefix=settings.api_v1_prefix)
