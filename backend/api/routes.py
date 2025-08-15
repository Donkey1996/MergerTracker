from fastapi import APIRouter
from .endpoints import deals, companies, news, auth, analytics

# Create main API router
api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(
    deals.router,
    prefix="/deals",
    tags=["deals"]
)

api_router.include_router(
    companies.router,
    prefix="/companies",
    tags=["companies"]
)

api_router.include_router(
    news.router,
    prefix="/news",
    tags=["news"]
)

api_router.include_router(
    auth.router,
    prefix="/auth",
    tags=["authentication"]
)

api_router.include_router(
    analytics.router,
    prefix="/analytics",
    tags=["analytics"]
)