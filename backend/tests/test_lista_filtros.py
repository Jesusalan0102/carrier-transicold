"""Filtros de la pantalla Evidencias: solo videos y por actividad."""
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from routers import evidencias_router as er


@pytest.fixture
def cli(monkeypatch):
    llamadas = []
    def read(sql, p=None):
        llamadas.append((sql, p))
        if "COUNT(*) AS total" in sql: return [{"total": 2}]
        if "GROUP BY e.asignacion_id" in sql:
            return [{"asignacion_id": 8820049, "actividad": "Evidencia", "tecnico_tarea": "LuisLlanes",
                     "videos": 1, "fotos": 54, "ultima": "2026-10-09 22:02:02"},
                    {"asignacion_id": None, "actividad": None, "tecnico_tarea": None,
                     "videos": 2, "fotos": 0, "ultima": None}]
        return [{"id": 5, "nombre_archivo": "v.webm", "tecnico": "X", "asignacion_id": 8820049, "tipo": "video",
                 "equipo": None, "fecha": "2026-10-09 22:01:33", "actividad": "Evidencia"}]
    monkeypatch.setattr(er, "execute_read", read)
    app = FastAPI(); app.include_router(er.router)
    app.dependency_overrides[er.require_admin_or_visor] = lambda: {"username": "a", "role": "admin"}
    return TestClient(app), llamadas


def test_filtro_solo_videos_y_actividad(cli):
    c, llamadas = cli
    r = c.get("/api/evidencias/lista/CW1?tipo=video&asignacion_id=8820049").json()
    assert r["total"] == 2 and r["fotos"][0]["tipo"] == "video" and r["fotos"][0]["asignacion_id"] == 8820049
    sql, params = llamadas[-1]
    assert "COALESCE(e.tipo,'foto')=%s" in sql and "e.asignacion_id=%s" in sql
    assert "ORDER BY e.created_at DESC" in sql                  # orden por fecha, no por id
    assert params[:3] == ("CW1", "video", 8820049)


def test_sin_filtros_trae_todo(cli):
    c, llamadas = cli
    c.get("/api/evidencias/lista/CW1")
    sql, params = llamadas[-1]
    assert "e.asignacion_id=%s" not in sql and params[0] == "CW1"


def test_filtro_tipo_invalido_se_ignora(cli):
    c, llamadas = cli
    c.get("/api/evidencias/lista/CW1?tipo=drop table")
    assert "COALESCE(e.tipo" not in llamadas[-1][0]


def test_resumen_por_actividad(cli):
    c, _ = cli
    r = c.get("/api/evidencias/resumen/CW1").json()
    assert r[0] == {"asignacion_id": 8820049, "actividad": "Evidencia", "tecnico": "LuisLlanes",
                    "fotos": 54, "videos": 1, "ultima": "2026-10-09 22:02:02"}
    assert r[1]["actividad"] == "Sin actividad" and r[1]["videos"] == 2
