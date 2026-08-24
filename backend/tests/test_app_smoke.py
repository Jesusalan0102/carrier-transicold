"""
Tests de humo (smoke tests).

El objetivo de estos tests NO es cubrir lógica de negocio a fondo todavía —
es la red mínima que hoy no existe: si alguien rompe un import, un router,
o el arranque de la app, esto lo detecta en el push, no en producción.
"""
from fastapi.testclient import TestClient


def test_app_importa_sin_errores():
    """
    Si algún router tiene un error de sintaxis, un import roto, o una
    referencia a algo que no existe, esto falla aquí en vez de en Clever Cloud.
    """
    import main  # noqa: F401
    assert main.app is not None


def test_health_check_responde_200():
    from main import app

    # Sin "with TestClient(app) as client": así NO se dispara el evento
    # startup (que llama a init_db() y necesitaría una base de datos real).
    client = TestClient(app)
    response = client.get("/api/health")

    assert response.status_code == 200
    body = response.json()
    assert "message" in body
    assert body.get("version") == "2.1"


def test_ruta_inexistente_da_404():
    from main import app

    client = TestClient(app)
    response = client.get("/esta-ruta-no-existe-en-ningun-lado")

    assert response.status_code == 404


def test_todos_los_routers_quedaron_registrados():
    """
    Verifica que la app tenga rutas registradas de cada módulo de negocio
    principal. No valida el comportamiento de cada endpoint (eso vendrá con
    tests específicos por router más adelante), pero sí detecta si alguien
    olvida un app.include_router(...) al agregar/mover un router.
    """
    from main import app

    paths = {route.path for route in app.routes}
    prefijos_esperados = [
        "/api/auth/login",
        "/api/health",
    ]
    for prefijo in prefijos_esperados:
        assert any(p.startswith(prefijo.rsplit("/", 1)[0]) for p in paths), (
            f"No se encontró ninguna ruta bajo {prefijo!r} — "
            f"¿se movió o se dejó de registrar ese router?"
        )
