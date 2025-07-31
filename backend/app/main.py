import logging
import logging.config
from contextlib import asynccontextmanager

from app.api import webhook, instruments
from app.config import LOGGING_CONFIG, settings
from app.db.models import Base
from app.db.session import engine
from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware

logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger("app")


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield

    await engine.dispose()


app = FastAPI(lifespan=lifespan)
v1 = APIRouter()

v1.include_router(webhook.router)
v1.include_router(instruments.router)


app.include_router(v1, prefix="/api/v1")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition"],
)
