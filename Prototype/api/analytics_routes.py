from fastapi import APIRouter

from api_analytics import get_analytics_results


analytics_router = APIRouter(
    prefix="/analytics",
    tags=["analytics"]
)


@analytics_router.get("/")
def get_analytics():
    return get_analytics_results()