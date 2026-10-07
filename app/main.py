from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import (
    analytics,
    anomaly,
    auth,
    community,
    emergency,
    notifications,
    phone_auth,
    privacy,
    risk,
    routes,
    trips,
    users,
)
from app.config import get_settings
from app.database import Base, SessionLocal, engine
from app.seed import seed_community, seed_routes

from app.models import (  # noqa: F401
    anomaly as _anomaly_models,
    community as _community_models,
    notification as _notification_models,
    privacy as _privacy_models,
    risk_log as _risk_log_models,
    route as _route_models,
    trip as _trip_models,
    user as _user_models,
)

settings = get_settings()

app = FastAPI(
    title=settings.APP_NAME,
    version="0.9.0",
    description="SENTRA backend - Phase 6 (emergency notifications)",
)

if settings.CORS_ORIGINS.strip() == "*":
    allow_origins = ["*"]
else:
    allow_origins = [o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if settings.AUTO_CREATE_TABLES:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_community(db)
        seed_routes(db)
    finally:
        db.close()

app.include_router(auth.router)
app.include_router(phone_auth.router)
app.include_router(users.router)
app.include_router(risk.router)
app.include_router(routes.router)
app.include_router(trips.router)
app.include_router(privacy.router)
app.include_router(anomaly.router)
app.include_router(community.router)
app.include_router(analytics.router)
app.include_router(notifications.router)
app.include_router(emergency.router)


@app.get("/", tags=["root"])
def root():
    return {
        "name": settings.APP_NAME,
        "version": "0.9.0",
        "status": "ok",
        "docs": "/docs",
    }


@app.get("/health", tags=["root"])
def health():
    return {"status": "healthy"}
