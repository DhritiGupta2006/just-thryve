import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.routers.auth import router as auth_router, profile_router
from app.routers.loans import router as loans_router
from app.routers.consent import router as consent_router
from app.routers.offers import router as offers_router
from app.routers.repayment import router as repayment_router
from app.routers.audit_logs import router as audit_logs_router
from app.routers.esg import router as esg_router
from app.routers.dashboard import router as dashboard_router
from app.routers.notifications import router as notifications_router
from app.routers.ocen import router as ocen_router

settings = get_settings()

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger("greenflowcredit")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("GreenFlowCredit API starting up (env=%s)", settings.environment)
    yield
    logger.info("GreenFlowCredit API shutting down")


app = FastAPI(
    title="GreenFlowCredit API",
    description="OCEN-based digital lending platform for green businesses",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=(
        ["http://localhost:5173", "http://localhost:3000"]
        if settings.environment == "development"
        else ([settings.frontend_url] if settings.frontend_url else [])
    ),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    elapsed = round((time.time() - start) * 1000, 2)
    logger.info("%s %s → %d  (%.2fms)", request.method, request.url.path, response.status_code, elapsed)
    return response


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled exception: %s", exc)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"},
    )


# Mount routers
app.include_router(auth_router)
app.include_router(profile_router)
app.include_router(loans_router)
app.include_router(consent_router)
app.include_router(offers_router)
app.include_router(repayment_router)
app.include_router(audit_logs_router)
app.include_router(esg_router)
app.include_router(dashboard_router)
app.include_router(notifications_router)
app.include_router(ocen_router)


@app.get("/", tags=["health"])
def health_check():
    return {"status": "ok", "service": "GreenFlowCredit API", "version": "1.0.0"}


@app.get("/health", tags=["health"])
def health():
    return {"status": "ok"}