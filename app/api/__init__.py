"""API package."""
from app.api.routes_health import router as health_router
from app.api.routes_chat import router as chat_router
from app.api.routes_voice import router as voice_router
from app.api.routes_orders import router as orders_router

__all__ = ["health_router", "chat_router", "voice_router", "orders_router"]
