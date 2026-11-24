from fastapi import APIRouter

from app.api.routes import (
    admin,
    alerts,
    analytics,
    auth,
    children,
    content,
    geo,
    notifications,
    reports,
    share,
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
api_router.include_router(admin.router)
api_router.include_router(share.router)
