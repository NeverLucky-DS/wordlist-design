from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import dashboard, essays, health, phrases, topics, training, words
from app.config import settings

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
app.include_router(training.router)
app.include_router(dashboard.router)
app.include_router(topics.router)
