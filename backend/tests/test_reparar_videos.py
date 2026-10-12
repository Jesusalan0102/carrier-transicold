"""Reparación de videos atorados, con DB y OneDrive simulados."""
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from auth import verify_token
from routers import evidencias_router as er
import onedrive_service as od


@pytest.fixture
def env(monkeypatch):
    log = []
    def read(sql, p=None):
        if "(tipo IS NULL OR tipo<>'video')" in sql: return [{"id": 1, "nombre_archivo": "a.mp4"}]
        if "tipo='video' AND (mime_type" in sql: return []
        if "LEFT JOIN unidades" in sql: return []
        if "SELECT onedrive_item_id" in sql: return [{"onedrive_item_id": "YA"}]
        if "SELECT unit_number FROM unidades" in sql: return [{"unit_number": "U1"}]
        if "contenido IS NULL AND" in sql: return [{"id": 2, "unit_number": "U1", "nombre_archivo": "b.mp4"},
                                                    {"id": 3, "unit_number": "U1", "nombre_archivo": "perdido.mp4"}]
        if "FROM asignaciones" in sql: return [{"tecnico": "juan"}]
        raise AssertionError(sql)
    monkeypatch.setattr(er, "execute_read", read)
    monkeypatch.setattr(er, "execute_write", lambda sql, p=None: log.append((sql, p)) or 1)
    monkeypatch.setattr(er, "ONEDRIVE_ENABLED", True)
    monkeypatch.setattr(od, "listar_videos_evidencias", lambda: [
        {"id": "YA", "name": "x.mp4", "carpeta": "U1_RF1", "ruta": "L/U1_RF1", "webUrl": "", "modificado": ""},
        {"id": "N1", "name": "A9_deadbeef_b.mp4", "carpeta": "U1_RF1", "ruta": "L/U1_RF1", "webUrl": "w", "modificado": "2026-06-01T10:00:00Z"},
        {"id": "N2", "name": "suelto.mp4", "carpeta": "U1_RF1", "ruta": "L/U1_RF1", "webUrl": "w2", "modificado": "2026-06-02T10:00:00Z"},
        {"id": "N3", "name": "raro.mp4", "carpeta": "OTRA", "ruta": "L/OTRA", "webUrl": "", "modificado": ""},
    ])
    app = FastAPI(); app.include_router(er.router)
    app.dependency_overrides[verify_token] = lambda: {"username": "admin", "role": "admin"}
    return TestClient(app), log


def test_simulacion_no_escribe(env):
    c, log = env
    j = c.post("/api/evidencias/reparar").json()
    assert log == [] and j["A_reclasificados_como_video"] == 1
    assert j["B_filas_reenlazadas_a_onedrive"] == 1 and len(j["B_filas_SIN_archivo_irrecuperables"]) == 1
    assert j["C_videos_en_onedrive_sin_fila_registrados"] == 1 and len(j["C_ignorados_carpeta_no_reconocida"]) == 1


def test_aplicar_repara(env):
    c, log = env
    c.post("/api/evidencias/reparar?aplicar=true")
    sqls = " ".join(s for s, _ in log)
    assert "SET tipo='video'" in sqls and "SET onedrive_item_id" in sqls and "INSERT INTO evidencias" in sqls


def test_solo_admin(env, monkeypatch):
    c, _ = env
    c.app.dependency_overrides[verify_token] = lambda: {"username": "t", "role": "tecnico"}
    assert c.post("/api/evidencias/reparar").status_code == 403
