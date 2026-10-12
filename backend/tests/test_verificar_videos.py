"""Verificación de videos por unidad y tarea, con la DB simulada."""
import asyncio
import re
import shutil
import subprocess

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from auth import verify_token
from routers import evidencias_router as er

BASE = {"unit_number": "U1", "nombre_archivo": "v.mp4", "tecnico": "juan", "asignacion_id": 10,
        "tipo": "video", "onedrive_item_id": None, "en_db": 1, "bytes_db": 2097152, "fecha": "2026-06-01",
        "u_unit": "U1", "u_oculto": 0, "id_lote": "L1", "a_id": 10, "a_unidad": "U1",
        "actividad": "PDI", "estado_tarea": "completada"}


def fila(**cambios):
    return {**BASE, **cambios}


# ── reglas por video ────────────────────────────────────────────────────────
def test_video_sano_se_ve():
    ev = er._evaluar_video(fila())
    assert ev["visible"] and ev["problemas"] == [] and ev["ubicacion"] == "base_de_datos"


def test_video_solo_en_onedrive_se_ve():
    ev = er._evaluar_video(fila(en_db=0, onedrive_item_id="X"))
    assert ev["visible"] and ev["ubicacion"] == "onedrive"


@pytest.mark.parametrize("cambios, texto, reparable", [
    ({"tipo": "foto"}, "guardado como foto", True),
    ({"tipo": None}, "guardado como foto", True),
    ({"en_db": 0, "onedrive_item_id": None}, "no tiene archivo", True),
    ({"u_unit": None, "u_oculto": None}, "no existe en Registro de unidades", False),
    ({"u_oculto": 1}, "oculta", False),
    ({"asignacion_id": None, "a_id": None}, "ninguna tarea", False),
    ({"a_id": None}, "ya no existe", False),
])
def test_problemas_detectados(cambios, texto, reparable):
    ev = er._evaluar_video(fila(**cambios))
    assert not ev["visible"]
    assert any(texto in p for p in ev["problemas"]), ev["problemas"]
    assert ev["reparable"] is reparable


def test_tarea_de_otra_unidad_es_solo_aviso():
    ev = er._evaluar_video(fila(a_unidad="U2"))
    assert ev["visible"] and len(ev["avisos"]) == 1


# ── endpoint ────────────────────────────────────────────────────────────────
@pytest.fixture
def cliente(monkeypatch):
    filas = [
        fila(id=1),
        fila(id=2, asignacion_id=11, a_id=11, tipo="foto", nombre_archivo="b.mp4"),
        fila(id=3, unit_number="U2", u_unit="U2", u_oculto=1, asignacion_id=None, a_id=None, a_unidad=None, en_db=0,
             onedrive_item_id="X", bytes_db=None),
        fila(id=4, unit_number="U9", u_unit=None, u_oculto=None, id_lote=None, asignacion_id=None, a_id=None, a_unidad=None),
    ]
    monkeypatch.setattr(er, "execute_read", lambda sql, p=None: filas)
    app = FastAPI()
    app.include_router(er.router)
    app.dependency_overrides[verify_token] = lambda: {"username": "admin", "role": "admin"}
    return TestClient(app)


def test_agrupa_por_unidad_y_tarea(cliente):
    d = cliente.get("/api/evidencias/verificar-videos").json()
    assert d["resumen"]["total"] == 4 and d["resumen"]["visibles"] == 1 and d["resumen"]["con_problema"] == 3
    por_unidad = {u["unit_number"]: u for u in d["unidades"]}
    assert set(por_unidad) == {"U1", "U2", "U9"}
    u1 = por_unidad["U1"]
    assert sorted(t["asignacion_id"] for t in u1["tareas"]) == [10, 11]
    assert por_unidad["U2"]["unidad_oculta"] is True
    assert por_unidad["U9"]["unidad_existe"] is False
    assert por_unidad["U2"]["tareas"][0]["asignacion_id"] is None       # grupo "sin tarea"
    assert d["resumen"]["base_de_datos"] == 3 and d["resumen"]["onedrive"] == 1


def test_solo_problemas_oculta_los_sanos(cliente):
    d = cliente.get("/api/evidencias/verificar-videos?solo_problemas=true").json()
    ids = [v["id"] for u in d["unidades"] for t in u["tareas"] for v in t["videos"]]
    assert 1 not in ids and sorted(ids) == [2, 3, 4]
    assert d["resumen"]["total"] == 4          # el resumen cuenta todos


def test_verificar_solo_admin(cliente):
    cliente.app.dependency_overrides[verify_token] = lambda: {"username": "t", "role": "tecnico"}
    assert cliente.get("/api/evidencias/verificar-videos").status_code == 403


# ── página ──────────────────────────────────────────────────────────────────
def _html():
    from routers.web_router import verificar_videos_page
    loop = asyncio.new_event_loop()      # no dejar cerrado el loop global
    try:
        return loop.run_until_complete(verificar_videos_page()).body.decode("utf-8")
    finally:
        loop.close()


def test_pagina_renderiza_y_apunta_a_los_endpoints_correctos():
    html = _html()
    for ruta in ("/api/evidencias/verificar-videos", "/api/evidencias/reparar",
                 "/api/evidencias/copiar-videos-a-onedrive", "/api/evidencias/foto/"):
        assert ruta in html
    assert "/app/verificar-videos" in html      # entrada en el menú lateral de admin


@pytest.mark.skipif(shutil.which("node") is None, reason="node no disponible")
def test_javascript_de_la_pagina_es_valido(tmp_path):
    html = _html()
    scripts = re.findall(r"<script>(.*?)</script>", html, flags=re.S)
    mio = next(s for s in scripts if "vvCargar" in s)
    f = tmp_path / "vv.js"
    f.write_text(mio, encoding="utf-8")
    r = subprocess.run(["node", "--check", str(f)], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
