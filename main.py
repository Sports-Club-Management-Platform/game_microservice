from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from db.create_database import create_tables, populate_db
from db.database import SessionLocal
from routers import club, game, pavilion


@asynccontextmanager
async def lifespan(app):
    create_tables()
    db: Session = SessionLocal()
    try:
        await populate_db(db)
    finally:
        db.close()
    yield



app = FastAPI(
    lifespan=lifespan,
    title="ClubSync Game_Microservice API",
    version="0.0.1",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    contact={
        "name": "ClubSync",
    },
    servers=[{"url": "http://localhost:8002", "description": "Local server"}],
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(club.router)
app.include_router(game.router)
app.include_router(pavilion.router)


@app.middleware("http")
async def db_session_middleware(request: Request, call_next):
    request.state.db = SessionLocal()
    response = await call_next(request)
    request.state.db.close()
    return response
