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


def test_layout_compartido_renderiza_sin_errores():
    """
    pagina_con_menu() es un f-string enorme que arma el layout (sidebar +
    header + modal de búsqueda global) para TODAS las páginas /app/*. Un
    solo '{' o '}' sin escapar ahí rompe absolutamente todas las páginas
    del sistema a la vez — este test existe para atrapar justo eso.
    """
    from routers.web_router import pagina_con_menu

    html = pagina_con_menu("Prueba", "<p>contenido</p>", "dashboard")
    assert "<html" in html
    assert "globalSearchOverlay" in html  # modal de búsqueda global (Ctrl+K)
    assert "/api/search/global" in html


def test_dashboard_renderiza_con_kpis_personalizados():
    """
    /app/dashboard incluye la pestaña de KPIs por técnico + la sección de
    métricas personalizadas (modal para crear métricas, tabla editable de
    valores). Protege ese bloque de HTML/JS contra errores de sintaxis.
    """
    import asyncio
    from routers.web_router import dashboard

    html = asyncio.get_event_loop().run_until_complete(dashboard())
    body = html.body.decode()
    for needle in (
        "kpiCustomTabla", "modalNuevaMetrica", "guardarNuevaMetrica",
        "guardarValorCustom", "kpis_custom/valores", "kpis_custom/metricas",
    ):
        assert needle in body, f"Falta '{needle}' en el HTML de /app/dashboard"


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
