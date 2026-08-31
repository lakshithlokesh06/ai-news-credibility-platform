from fastapi import APIRouter

from app.api.v1.endpoints import articles, experiments, health, history, imports, ml, models, monitoring, reviews, statistics

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(imports.router, tags=["dataset-imports"])
api_router.include_router(articles.router, tags=["articles"])
api_router.include_router(statistics.router, tags=["dataset-statistics"])
api_router.include_router(ml.router, tags=["ml"])
api_router.include_router(experiments.router, tags=["experiments"])
api_router.include_router(models.router, tags=["models"])
api_router.include_router(history.router, tags=["history"])
api_router.include_router(monitoring.router, tags=["monitoring"])
api_router.include_router(reviews.router, tags=["reviews"])
