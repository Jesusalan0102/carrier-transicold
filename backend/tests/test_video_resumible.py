"""Pruebas de la subida de video por partes, con DB y OneDrive simulados."""
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import db
from auth import verify_token
from routers import evidencias_video_router as vr

CH = 12 * 320 * 1024


class FakeResp:
    def __init__(self, code, js=None):
        self.status_code, self._js, self.text = code, js or {}, str(js)
    def json(self):
        return self._js


class FakeOneDrive:
    VIDEO_CHUNK_BYTES = CH
    def __init__(self):
        self.sesiones, self.items, self.n = {}, {}, 0
        self.caida = 0            # nº de peticiones que fallan con excepción de red
        self.sesion_expira = False
    def carpeta_evidencia_unidad(self, u): return f"Evidencias/L1/{u}"
    def crear_sesion_video(self, ruta):
        self.n += 1
        url = f"https://up/{self.n}"
        self.sesiones[url] = {"ruta": ruta, "recibido": 0}
        return url
    def subir_parte_video(self, url, start, data, total):
        if self.caida:
            self.caida -= 1
            raise ConnectionError("sin señal")
        s = self.sesiones.get(url)
        if s is None or self.sesion_expira:
            return FakeResp(404)
        if start != s["recibido"]:
            return FakeResp(416)
        s["recibido"] += len(data)
        if s["recibido"] >= total:
            self.items[s["ruta"]] = {"id": "ITEM1", "size": total, "webUrl": "https://od/x"}
            return FakeResp(201, self.items[s["ruta"]])
        return FakeResp(202, {"nextExpectedRanges": [f"{s['recibido']}-{total-1}"]})
    def estado_sesion_video(self, url):
        if self.sesion_expira or url not in self.sesiones: return None
        return self.sesiones[url]["recibido"]
    def buscar_item_por_ruta(self, ruta): return self.items.get(ruta)


class FakeDB:
    def __init__(self): self.up, self.ev = {}, []
    def read(self, sql, p=None):
        if "FROM video_uploads WHERE upload_id" in sql: return [dict(self.up[p[0]])] if p[0] in self.up else []
        if "FROM video_uploads WHERE tecnico" in sql:
            return [dict(r) for r in self.up.values() if (r["tecnico"], r["client_id"]) == tuple(p)]
        if "SELECT evidencia_id FROM video_uploads" in sql: return [{"evidencia_id": self.up[p[0]]["evidencia_id"]}]
        if "COUNT(*)" in sql: return [{"total": 0}]
        if "FROM users" in sql: return [{"username": p[0]}] if p[0] in ("maria", "juan") else []
        raise AssertionError(sql)
    def write(self, sql, p=None):
        if sql.startswith("INSERT INTO video_uploads"):
            k = ["upload_id","client_id","tecnico","unidad","asignacion_id","equipo","nombre_archivo","mime_type","tamano","onedrive_path","upload_url"]
            r = dict(zip(k, p)); r["evidencia_id"] = None; self.up[r["upload_id"]] = r; return 1
        if "SET evidencia_id=0" in sql:
            r = self.up[p[0]]
            if r["evidencia_id"] is None: r["evidencia_id"] = 0; return 1
            return 0
        if "SET evidencia_id=NULL" in sql: self.up[p[0]]["evidencia_id"] = None; return 1
        if "SET evidencia_id=%s" in sql: self.up[p[1]]["evidencia_id"] = p[0]; return 1
        if "SET upload_url" in sql: self.up[p[1]]["upload_url"] = p[0]; return 1
        raise AssertionError(sql)
    def write_id(self, sql, p=None):
        self.ev.append(p); return len(self.ev)


@pytest.fixture
def env(monkeypatch):
    fdb, fod = FakeDB(), FakeOneDrive()
    monkeypatch.setattr(vr, "execute_read", fdb.read)
    monkeypatch.setattr(vr, "execute_write", fdb.write)
    monkeypatch.setattr(db, "execute_write_with_id", fdb.write_id)
    monkeypatch.setattr(vr, "od", fod)
    monkeypatch.setattr(vr, "ONEDRIVE_ENABLED", True)
    app = FastAPI(); app.include_router(vr.router)
    app.dependency_overrides[verify_token] = lambda: {"username": "juan", "role": "tecnico"}
    return TestClient(app), fdb, fod


def iniciar(c, total, cid="c1", nombre="clip.mp4"):
    return c.post("/api/evidencias/video/iniciar", json={
        "client_id": cid, "unidad": "U1", "asignacion_id": 7, "nombre": nombre, "tamano": total})


def subir_todo(c, uid, total, off=0):
    r = None
    while off < total:
        n = min(CH, total - off)
        r = c.put(f"/api/evidencias/video/{uid}/parte", content=b"x" * n, headers={"X-Offset": str(off)})
        assert r.status_code == 200, r.text
        j = r.json()
        if j["done"]: return j
        off = j["next_start"]
    return r.json()


def test_subida_completa_crea_una_sola_fila(env):
    c, fdb, fod = env
    total = CH * 2 + 1000
    j = iniciar(c, total).json()
    r = subir_todo(c, j["upload_id"], total)
    assert r["done"] and r["evidencia_id"] == 1
    assert len(fdb.ev) == 1 and fdb.ev[0][5] == "ITEM1"


def test_reintento_tras_corte_no_duplica(env):
    c, fdb, fod = env
    total = CH * 3
    j = iniciar(c, total).json()
    fod.caida = 1
    r = c.put(f"/api/evidencias/video/{j['upload_id']}/parte", content=b"x" * CH, headers={"X-Offset": "0"})
    assert r.status_code == 502                       # el cliente reintenta
    r = subir_todo(c, j["upload_id"], total)
    assert r["done"]
    # el celular reinicia con el mismo client_id -> misma subida, sin fila nueva
    again = iniciar(c, total).json()
    assert again["done"] and again["evidencia_id"] == r["evidencia_id"] and len(fdb.ev) == 1


def test_reanuda_desde_donde_quedo(env):
    c, fdb, fod = env
    total = CH * 3
    j = iniciar(c, total).json()
    c.put(f"/api/evidencias/video/{j['upload_id']}/parte", content=b"x" * CH, headers={"X-Offset": "0"})
    reanudar = iniciar(c, total).json()            # app reiniciada
    assert reanudar["upload_id"] == j["upload_id"] and reanudar["next_start"] == CH


def test_ultimo_trozo_perdido_se_recupera_sin_resubir(env):
    c, fdb, fod = env
    total = CH + 500
    j = iniciar(c, total).json()
    c.put(f"/api/evidencias/video/{j['upload_id']}/parte", content=b"x" * CH, headers={"X-Offset": "0"})
    # OneDrive completó el archivo pero la respuesta nunca llegó; la sesión ya no existe
    ruta = fdb.up[j["upload_id"]]["onedrive_path"]
    fod.items[ruta] = {"id": "ITEM9", "size": total, "webUrl": "u"}
    fod.sesion_expira = True
    r = c.put(f"/api/evidencias/video/{j['upload_id']}/parte", content=b"x" * 500, headers={"X-Offset": str(CH)})
    assert r.json()["done"] and len(fdb.ev) == 1


def test_sesion_expirada_se_reinicia(env):
    c, fdb, fod = env
    total = CH * 2
    j = iniciar(c, total).json()
    fod.sesion_expira = True
    r = c.put(f"/api/evidencias/video/{j['upload_id']}/parte", content=b"x" * CH, headers={"X-Offset": "0"})
    assert r.status_code == 410
    fod.sesion_expira = False
    fod.sesiones.clear()                              # la sesión vieja ya no existe
    nuevo = iniciar(c, total).json()
    assert nuevo["upload_id"] == j["upload_id"] and nuevo["next_start"] == 0
    assert subir_todo(c, nuevo["upload_id"], total)["done"]


def test_validaciones(env):
    c, _, _ = env
    assert iniciar(c, 10, nombre="doc.pdf").status_code == 400
    assert iniciar(c, 400 * 1024 * 1024, cid="g").status_code == 400
    j = iniciar(c, CH * 2, cid="h").json()
    r = c.put(f"/api/evidencias/video/{j['upload_id']}/parte", content=b"x" * 1000, headers={"X-Offset": "0"})
    assert r.status_code == 400                       # trozo intermedio no múltiplo de 320 KiB


def test_onedrive_caido_pide_respaldo_en_db(env):
    c, _, fod = env
    def falla(_): raise RuntimeError("token vencido")
    fod.crear_sesion_video = falla
    assert iniciar(c, CH, cid="z").status_code == 503     # el cliente cae al método clásico


def _como_admin(c):
    from fastapi import FastAPI  # noqa
    c.app.dependency_overrides[verify_token] = lambda: {"username": "admin", "role": "admin"}


def test_admin_sube_video_a_nombre_del_tecnico(env):
    c, fdb, _ = env
    _como_admin(c)
    total = CH + 10
    j = c.post("/api/evidencias/video/iniciar", json={"client_id": "a1", "unidad": "U1", "asignacion_id": 7,
                                                      "nombre": "clip.mp4", "tamano": total, "tecnico": "maria"}).json()
    assert fdb.up[j["upload_id"]]["tecnico"] == "maria"
    assert subir_todo(c, j["upload_id"], total)["done"]            # el admin puede continuar la sesión de 'maria'
    assert fdb.ev[0][2] == "maria"                                  # la evidencia queda a nombre del técnico


def test_tecnico_no_puede_subir_a_nombre_de_otro_ni_tecnico_inexistente(env):
    c, _, _ = env
    r = c.post("/api/evidencias/video/iniciar", json={"client_id": "t1", "unidad": "U1", "nombre": "a.mp4",
                                                      "tamano": 10, "tecnico": "maria"})
    assert r.status_code == 403
    _como_admin(c)
    r = c.post("/api/evidencias/video/iniciar", json={"client_id": "t2", "unidad": "U1", "nombre": "a.mp4",
                                                      "tamano": 10, "tecnico": "fantasma"})
    assert r.status_code == 400
