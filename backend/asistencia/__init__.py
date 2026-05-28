# asistencia/__init__.py
from .routes import router
from .horarios_routes import router as horarios_router

__all__ = ['router', 'horarios_router']
