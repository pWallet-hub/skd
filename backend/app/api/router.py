from fastapi import APIRouter

from app.api.routes import (
    alerts,
    analytics,
    auth,
    children,
    content,
    geo,
    notifications,
    reports,
    signals,
)

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(children.router)
api_router.include_router(reports.router)
api_router.include_router(geo.router)
api_router.include_router(analytics.router)
api_router.include_router(signals.router)
api_router.include_router(alerts.router)
api_router.include_router(notifications.router)
api_router.include_router(content.router)
