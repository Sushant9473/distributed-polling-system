from fastapi import FastAPI

from app.api.v1.api import api_router
from app.core.config import settings

app = FastAPI(title="Distributed Live Polling System")


@app.get("/")
async def health_check():
    return {"status": "healthy"}


app.include_router(api_router, prefix=settings.API_PREFIX)
