"""Respaldo diario de la base de datos en OneDrive (DB y OneDrive simulados)."""
import io, json, time, zipfile
import pytest
import respaldo_onedrive as rb
import salud_evidencias as sv

TABLAS = {
    "asignaciones": {"cols": [("id", "int"), ("unidad", "varchar(50)"), ("estado", "varchar(20)")],
                     "pk": ["id"], "filas": [{"id": i, "unidad": f"U{i}", "estado": "completada"} for i in range(1, 4506)]},
    "evidencias": {"cols": [("id", "bigint"), ("unit_number", "varchar(50)"), ("contenido", "longblob"), ("onedrive_item_id", "varchar(200)")],
                   "pk": ["id"], "filas": [{"id": 1, "unit_number": "U1", "onedrive_item_id": "ITEM1"},
                                           {"id": 2, "unit_number": "U1", "onedrive_item_id": None}]},
    "evidencia_partes": {"cols": [("evidencia_id", "bigint"), ("contenido", "longblob")], "pk": [], "filas": []},
    "salud_sistema": {"cols": [("clave", "varchar(60)")], "pk": [], "filas": []},
}


def _fake_read(sql, p=None):
    if sql == "SHOW TABLES": return [{"Tables_in_carrier_db": t} for t in TABLAS]
    t = next((n for n in TABLAS if f"`{n}`" in sql), None)
    if sql.startswith("SHOW COLUMNS"): return [{"Field": c, "Type": ty} for c, ty in TABLAS[t]["cols"]]
    if sql.startswith("SHOW KEYS"): return [{"Column_name": c, "Seq_in_index": i + 1} for i, c in enumerate(TABLAS[t]["pk"])]
    if sql.startswith("SHOW CREATE TABLE"): return [{"Table": t, "Create Table": f"CREATE TABLE `{t}` (...)"}]
    if sql.startswith("SELECT"):
        lim = int(sql.split("LIMIT ")[1].split()[0]); off = int(sql.split("OFFSET ")[1])
        cols = [c.strip(" `") for c in sql.split("SELECT ")[1].split(" FROM ")[0].split(",")]
        return [{c: f.get(c) for c in cols} for f in TABLAS[t]["filas"][off:off + lim]]
    raise AssertionError(sql)


@pytest.fixture(autouse=True)
def db(monkeypatch):
    monkeypatch.setattr(rb, "execute_read", _fake_read)


def test_zip_incluye_tablas_sin_blobs_ni_partes_y_pagina_bien(tmp_path):
    ruta = tmp_path / "r.zip"
    res = rb.generar_zip(str(ruta))
    z = zipfile.ZipFile(ruta)
    nombres = set(z.namelist())
    assert {"asignaciones.jsonl", "evidencias.jsonl", "esquema.sql", "LEEME.txt"} <= nombres
    assert "evidencia_partes.jsonl" not in nombres and "salud_sistema.jsonl" not in nombres
    filas = [json.loads(l) for l in z.read("asignaciones.jsonl").decode().splitlines()]
    assert len(filas) == 4505 and [f["id"] for f in filas] == list(range(1, 4506))   # 3 lotes, sin perder ni repetir
    ev = [json.loads(l) for l in z.read("evidencias.jsonl").decode().splitlines()]
    assert "contenido" not in ev[0] and ev[0]["onedrive_item_id"] == "ITEM1" and ev[1]["onedrive_item_id"] is None
    assert res["tablas"] == 2 and res["filas"] == 4507 and "CREATE TABLE `asignaciones`" in z.read("esquema.sql").decode()


class FakeOD:
    TZ = None; BASE_FOLDER = "carrier-transicold"; GRAPH_BASE = "https://g"
    def __init__(self, tamano_ok=True): self.subidos, self.tamano_ok = [], tamano_ok
    def _upload_with_retry(self, fn, *a, **k): return "carrier-transicold/Respaldos"
    def _ensure_folder(self, p): return p
    def upload_large_file(self, contenido, ruta, ct): self.subidos.append((ruta, contenido)); return {"id": "RESP1"}
    def tamano_item(self, i): return len(self.subidos[-1][1]) if self.tamano_ok else 1
    def _get_token(self): return "t"
    def _borrar_item(self, i): self.borrados.append(i)


@pytest.fixture
def od(monkeypatch):
    from zoneinfo import ZoneInfo
    f = FakeOD(); f.TZ = ZoneInfo("America/Tijuana"); f.borrados = []
    import sys; monkeypatch.setitem(sys.modules, "onedrive_service", f)
    monkeypatch.setattr(rb, "_aplicar_retencion", lambda carpeta: 0)
    return f


def test_respaldo_sube_a_onedrive_y_verifica(od):
    r = rb.ejecutar_respaldo()
    assert r["ok"] and r["tablas"] == 2 and r["archivo"].startswith("respaldo_") and r["archivo"].endswith(".zip")
    ruta, contenido = od.subidos[0]
    assert ruta.startswith("carrier-transicold/Respaldos/respaldo_") and zipfile.ZipFile(io.BytesIO(contenido)).testzip() is None


def test_respaldo_falla_si_el_tamano_en_onedrive_no_coincide(od):
    od.tamano_ok = False
    r = rb.ejecutar_respaldo()
    assert not r["ok"] and "no coincide" in r["error"]


def test_respaldo_nunca_lanza_excepcion(od, monkeypatch):
    monkeypatch.setattr(rb, "generar_zip", lambda ruta: (_ for _ in ()).throw(RuntimeError("DB caída")))
    r = rb.ejecutar_respaldo()
    assert r["ok"] is False and "DB caída" in r["error"]


def test_una_tabla_rota_no_tira_el_respaldo_pero_se_reporta(od, monkeypatch):
    original = _fake_read
    def rota(sql, p=None):
        if "FROM `evidencias`" in sql and sql.startswith("SELECT"): raise RuntimeError("tabla corrupta")
        return original(sql, p)
    monkeypatch.setattr(rb, "execute_read", rota)
    r = rb.ejecutar_respaldo()
    assert r["ok"] is False and "evidencias" in r["error"] and od.subidos      # igual se subió lo demás


def test_retencion_borra_solo_los_mas_viejos(monkeypatch):
    import sys, types, requests
    nombres = [f"respaldo_2026-10-{d:02d}_0300.zip" for d in range(1, 21)] + ["otra_cosa.zip"]
    fake = types.SimpleNamespace(GRAPH_BASE="https://g", _get_token=lambda: "t", borrados=[])
    fake._borrar_item = lambda i: fake.borrados.append(i)
    monkeypatch.setitem(sys.modules, "onedrive_service", fake)
    class R:
        def raise_for_status(self): pass
        def json(self): return {"value": [{"id": n, "name": n} for n in nombres]}
    monkeypatch.setattr(requests, "get", lambda *a, **k: R())
    assert rb._aplicar_retencion("x") == 6                                      # 20 respaldos - 14 que se conservan
    assert sorted(fake.borrados) == sorted(nombres[:6]) and "otra_cosa.zip" not in fake.borrados


# ── programación y avisos ───────────────────────────────────────────────────────
def test_cuando_toca_respaldar_y_cuando_es_problema():
    ahora = time.time()
    assert sv.toca_respaldo(None, ahora) and sv.toca_respaldo({"ok": False}, ahora)
    assert not sv.toca_respaldo({"ok": True, "ts_ok": ahora - 3600}, ahora)
    assert not sv.toca_respaldo({"ok": True, "ts_ok": ahora - 23 * 3600}, ahora)      # la noche es la que respalda
    assert sv.toca_respaldo({"ok": True, "ts_ok": ahora - 31 * 3600}, ahora)           # red de seguridad
    aud = {"tareas_sin_evidencia": [], "videos_sin_archivo": 0, "subidas_incompletas": []}
    assert sv.problemas({"ok": True}, aud, {"ok": True, "ts_ok": ahora - 3600}, ahora) == []
    assert "falló" in sv.problemas({"ok": True}, aud, {"ok": False, "error": "x"}, ahora)[0]
    assert "4 días" in sv.problemas({"ok": True}, aud, {"ok": True, "ts_ok": ahora - 4 * 86400}, ahora)[0]


# ── programador nocturno ────────────────────────────────────────────────────────
def test_segundos_hasta_la_hora_del_respaldo():
    from datetime import datetime
    from zoneinfo import ZoneInfo
    tz = ZoneInfo("America/Tijuana")
    assert rb.segundos_hasta_hora(2, datetime(2026, 10, 16, 23, 0, tzinfo=tz)) == 3 * 3600     # cruza la medianoche
    assert rb.segundos_hasta_hora(2, datetime(2026, 10, 16, 1, 30, tzinfo=tz)) == 1800
    assert rb.segundos_hasta_hora(2, datetime(2026, 10, 16, 2, 0, tzinfo=tz)) == 24 * 3600     # justo a la hora: mañana


def test_nocturno_reintenta_y_avisa_si_todo_falla(monkeypatch):
    import asyncio
    avisos, llamadas = [], []
    monkeypatch.setattr(sv, "leer_estado", lambda c: None)
    monkeypatch.setattr(sv, "respaldar", lambda forzar=False: llamadas.append(1) or {"ok": False, "error": "invalid_grant"})
    monkeypatch.setattr(sv, "_avisar_admins", lambda t, c: avisos.append((t, c)))
    monkeypatch.setattr(rb, "ESPERA_REINTENTO_SEG", 0)
    r = asyncio.run(rb.ejecutar_nocturno())
    assert not r["ok"] and len(llamadas) == rb.REINTENTOS and len(avisos) == 1 and "invalid_grant" in avisos[0][1]


def test_nocturno_se_detiene_al_primer_exito_y_no_duplica(monkeypatch):
    import asyncio
    llamadas = []
    monkeypatch.setattr(sv, "leer_estado", lambda c: None)
    monkeypatch.setattr(sv, "respaldar", lambda forzar=False: llamadas.append(1) or {"ok": True, "archivo": "x.zip"})
    monkeypatch.setattr(rb, "ESPERA_REINTENTO_SEG", 0)
    assert asyncio.run(rb.ejecutar_nocturno())["ok"] and len(llamadas) == 1
    monkeypatch.setattr(sv, "leer_estado", lambda c: {"ok": True, "ts_ok": time.time() - 3600})   # ya hay uno de hace 1 h
    assert asyncio.run(rb.ejecutar_nocturno()) == {"omitido": True} and len(llamadas) == 1


def test_descarga_directa_solo_admin(monkeypatch, tmp_path):
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from routers.respaldo_router import router
    from auth import verify_token
    app = FastAPI(); app.include_router(router)
    app.dependency_overrides[verify_token] = lambda: {"username": "t", "role": "tecnico"}
    assert TestClient(app).get("/api/respaldo/descargar").status_code == 403
    app.dependency_overrides[verify_token] = lambda: {"username": "a", "role": "admin"}
    r = TestClient(app).get("/api/respaldo/descargar")
    assert r.status_code == 200 and r.headers["content-type"] == "application/zip"
    assert zipfile.ZipFile(io.BytesIO(r.content)).testzip() is None and "attachment" in r.headers["content-disposition"]
