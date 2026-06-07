from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import essays, health, phrases, topics, words
from app.api.routes import pipeline
from app.config import settings
from app.db.init_data import ensure_seed_data
from app.db.models import Base
from app.db.session import engine
from app.db.session import SessionLocal

app = FastAPI(title="Deutsch Essay Trainer")

origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(essays.router)
app.include_router(words.router)
app.include_router(phrases.router)
app.include_router(topics.router)
app.include_router(pipeline.router)


@app.on_event("startup")
async def init_schema() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with SessionLocal() as session:
        await ensure_seed_data(session)
