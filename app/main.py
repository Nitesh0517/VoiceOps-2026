"""FastAPI Main Application."""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database.connection import init_db
from app.database.ingest import ingest_all_data
from app.api.routes_health import router as health_router
from app.api.routes_chat import router as chat_router
from app.api.routes_voice import router as voice_router
from app.api.routes_orders import router as orders_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: ensure database exists and is populated
    if not settings.DATABASE_PATH.exists():
        init_db()
        ingest_all_data()
    yield
    # Shutdown cleanups


app = FastAPI(
    title="VoiceOps 2026 — AI Customer Support Voice Agent",
    description="Full-stack AI voice and text customer support agent for ZentroMart, grounded in company policies and Gnani.ai speech models.",
    version="1.0.0",
    lifespan=lifespan
)

# Enable CORS for local Streamlit / Frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health_router)
app.include_router(chat_router)
app.include_router(voice_router)
app.include_router(orders_router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.API_HOST, port=settings.API_PORT, reload=True)
