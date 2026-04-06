from app.routers.auth import router as auth_router
from app.routers.loans import router as loans_router
from app.routers.consent import router as consent_router
from app.routers.offers import router as offers_router
from app.routers.repayment import router as repayment_router

__all__ = [
    "auth_router",
    "loans_router",
    "consent_router",
    "offers_router",
    "repayment_router",
]
