from contextlib import asynccontextmanager
from typing import AsyncIterator
from fastapi import FastAPI
from .config import settings
from .db import create_pool
from .routes import drops

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    app.state.pool = await create_pool(settings.database_url)
    yield
    await app.state.pool.close()

app = FastAPI(title="DropCart API", lifespan=lifespan)
app.include_router(drops.router)

@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}