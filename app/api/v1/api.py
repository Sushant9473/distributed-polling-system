from fastapi import APIRouter

from .endpoints import polls

api_router = APIRouter()
api_router.include_router(polls.router, tags=["polls"])
