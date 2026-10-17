"""Respaldo de fotos/videos de la DB -> OneDrive: sin duplicar carpetas ni archivos (DB y OneDrive simulados)."""
import sys, types
import pytest
import respaldo_evidencias as rev

CARPETA = "carrier-transicold/Evidencias/L1/U1_S1"


class Mundo:
    """Estado simulado: filas de `evidencias`, partes y lo que hay en OneDrive."""
    def __init__(self):
        self.filas = []            # dicts: id, unit_number, nombre_archivo, asignacion_id, tipo, blob(bytes|None), item_id
        self.partes = {}           # id -> bytes
        self.onedrive = {}         # carpeta -> {nombre: bytes}
        self.carpetas_creadas = []
        self.subidas = []          # (ruta, n_bytes, via)
        self.updates = []
        self.tamano_malo = False

    def pendientes(self, unidad=None):
        out = []
        for f in self.filas:
            if f.get("item_id"):
                continue
            if f["blob"] is None and f["id"] not in self.partes:
                continue
            if unidad and f["unit_number"] != unidad:
                continue
            out.append(f)
        return out


@pytest.fixture
def mundo(monkeypatch):
    m = Mundo()

    def read(sql, p=None):
        if sql.startswith("SELECT DISTINCT e.unit_number"):
            fs = m.pendientes()
            if "REGEXP" in sql:
                fs = [f for f in fs if rev._es_video(f)]
            return [{"unit_number": u} for u in sorted({f["unit_number"] for f in fs})]
        if "FROM evidencias e WHERE e.unit_number=%s" in sql:
            return [{**{k: f[k] for k in ("id", "unit_number", "nombre_archivo", "asignacion_id", "tipo")},
                     "mime_type": None, "bytes": len(f["blob"] or b"")} for f in sorted(m.pendientes(p[0]), key=lambda f: f["id"])]
        if sql.startswith("SELECT contenido FROM evidencias"):
            f = next(f for f in m.filas if f["id"] == p[0])
            return [{"contenido": f["blob"]}]
        raise AssertionError(sql)

    def write(sql, p=None):
        assert sql.startswith("UPDATE evidencias SET onedrive_item_id")
        f = next(f for f in m.filas if f["id"] == p[3])
        f["item_id"] = p[0]
        m.updates.append(p)
        return 1

    od = types.SimpleNamespace(GRAPH_BASE="https://g", TZ=None)
    od.carpeta_evidencia_unidad = lambda u: (m.carpetas_creadas.append(u), m.onedrive.setdefault(CARPETA, {}), CARPETA)[2]
    od._upload_with_retry = lambda fn, *a, **k: fn(*a, **k)

    def upload_bytes(contenido, ruta, ct):
        carpeta, nombre = ruta.rsplit("/", 1)
        m.onedrive.setdefault(carpeta, {})[nombre] = contenido
        m.subidas.append((ruta, len(contenido), "simple"))
        return {"id": f"ID-{nombre}", "webUrl": f"https://od/{nombre}"}
    od.upload_bytes = upload_bytes
    od.tamano_item = lambda i: (1 if m.tamano_malo else len(m.onedrive[CARPETA][i[3:]]))
    monkeypatch.setitem(sys.modules, "onedrive_service", od)

    def subir_trozos(od_, ruta_local, ruta, ct):
        datos = open(ruta_local, "rb").read()
        carpeta, nombre = ruta.rsplit("/", 1)
        m.onedrive.setdefault(carpeta, {})[nombre] = datos
        m.subidas.append((ruta, len(datos), "trozos"))
        return {"id": f"ID-{nombre}", "webUrl": f"https://od/{nombre}"}
    monkeypatch.setattr(rev, "_subir_por_trozos", subir_trozos)
    monkeypatch.setattr(rev, "_listar", lambda od_, carpeta: {n.lower(): {"id": f"ID-{n}", "size": len(b), "webUrl": ""}
                                                              for n, b in m.onedrive.get(carpeta, {}).items()})
    monkeypatch.setattr(rev, "execute_read", read)
    monkeypatch.setattr(rev, "execute_write", write)
    monkeypatch.setattr(rev.ep, "tamano_total", lambda i: len(m.partes.get(i, b"")))
    monkeypatch.setattr(rev.ep, "iterar_rango", lambda i, a, b: iter([m.partes[i][:3], m.partes[i][3:]]))
    return m


def foto(i, nombre="a.jpg", blob=b"x" * 100, unidad="U1"):
    return {"id": i, "unit_number": unidad, "nombre_archivo": nombre, "asignacion_id": 5, "tipo": "foto", "blob": blob}


def test_sube_lo_que_falta_omite_lo_que_ya_esta_y_no_toca_filas_de_fotos(mundo):
    mundo.filas = [foto(1, "a.jpg"), foto(2, "b.jpg", b"y" * 50)]
    mundo.onedrive[CARPETA] = {"a.jpg": b"x" * 100}                    # a.jpg ya estaba igual en OneDrive
    r = rev.respaldar_evidencias()
    assert r["ok"] and r["subidos"] == 1 and r["ya_respaldados"] == 1 and mundo.subidas == [(f"{CARPETA}/b.jpg", 50, "simple")]
    assert mundo.updates == [] and mundo.carpetas_creadas == ["U1"]    # fotos: la fila no se modifica; carpeta canónica


def test_es_idempotente_y_nunca_duplica(mundo):
    mundo.filas = [foto(1), foto(2, "b.jpg")]
    rev.respaldar_evidencias()
    n = len(mundo.subidas)
    r = rev.respaldar_evidencias()
    assert len(mundo.subidas) == n and r["subidos"] == 0 and r["ya_respaldados"] == 2
    assert set(mundo.onedrive[CARPETA]) == {"a.jpg", "b.jpg"}          # un solo archivo por foto


def test_fotos_con_el_mismo_nombre_no_se_pisan_y_el_nombre_es_estable(mundo):
    mundo.filas = [foto(1, "IMG.jpg", b"1" * 10), foto(2, "IMG.jpg", b"2" * 20)]
    rev.respaldar_evidencias()
    assert mundo.onedrive[CARPETA] == {"IMG.jpg": b"1" * 10, "IMG_E2.jpg": b"2" * 20}
    n = len(mundo.subidas)
    rev.respaldar_evidencias()
    assert len(mundo.subidas) == n                                      # segunda corrida: nada que subir


def test_video_en_blob_se_sube_con_nombre_fijo_y_se_enlaza_la_fila(mundo):
    v = {**foto(9, "clip.mp4", b"v" * 300), "tipo": "video"}
    mundo.filas = [v]
    r = rev.respaldar_evidencias()
    assert r["ok"] and r["vinculados"] == 1 and v["item_id"] == "ID-A5_E9_clip.mp4"
    assert list(mundo.onedrive[CARPETA]) == ["A5_E9_clip.mp4"] and v["blob"] == b"v" * 300   # la DB conserva el blob
    assert rev.respaldar_evidencias()["revisados"] == 0                # ya enlazado: no vuelve a salir


def test_video_grande_en_partes_se_arma_en_disco_y_sube_por_trozos(mundo, monkeypatch):
    monkeypatch.setattr(rev, "SIMPLE_MAX", 5)
    v = {**foto(3, "grande.mov", None), "tipo": "video"}
    mundo.filas, mundo.partes[3] = [v], b"0123456789"
    r = rev.respaldar_evidencias()
    assert r["ok"] and mundo.subidas == [(f"{CARPETA}/A5_E3_grande.mov", 10, "trozos")]
    assert mundo.onedrive[CARPETA]["A5_E3_grande.mov"] == b"0123456789" and v["item_id"]


def test_video_que_ya_estaba_en_onedrive_solo_se_enlaza_sin_resubir(mundo):
    v = {**foto(4, "c.mp4", b"z" * 40), "tipo": "video"}
    mundo.filas, mundo.onedrive[CARPETA] = [v], {"A5_E4_c.mp4": b"z" * 40}
    r = rev.respaldar_evidencias()
    assert r["subidos"] == 0 and r["vinculados"] == 1 and v["item_id"] and mundo.subidas == []


def test_simulacion_cuenta_pero_no_sube_ni_cambia_nada(mundo):
    mundo.filas = [foto(1), {**foto(2, "v.mp4", b"v" * 2097152), "tipo": "video"}]
    r = rev.respaldar_evidencias(aplicar=False)
    assert r["por_subir"] == 2 and r["mb_por_subir"] == 2.0 and mundo.subidas == [] and mundo.updates == []


def test_si_el_tamano_en_onedrive_no_coincide_se_reporta_y_no_se_enlaza(mundo):
    v = {**foto(1, "c.mp4", b"z" * 40), "tipo": "video"}
    mundo.filas, mundo.tamano_malo = [v], True
    r = rev.respaldar_evidencias()
    assert not r["ok"] and "no coincide" in r["errores"][0]["error"] and not v.get("item_id") and r["vinculados"] == 0


def test_solo_videos_ignora_las_fotos(mundo):
    mundo.filas = [foto(1), {**foto(2, "v.mp4", b"v" * 9), "tipo": "video"}]
    r = rev.respaldar_evidencias(solo_videos=True)
    assert r["subidos"] == 1 and list(mundo.onedrive[CARPETA]) == ["A5_E2_v.mp4"]


def test_si_se_acaba_el_tiempo_queda_incompleto_y_continua_despues(mundo):
    mundo.filas = [foto(1, "a.jpg"), foto(2, "b.jpg", unidad="U2")]
    r = rev.respaldar_evidencias(presupuesto_seg=-1)
    assert r["completo"] is False and r["ok"] is False and mundo.subidas == []
    assert rev.respaldar_evidencias()["completo"] is True


def test_nombres_prohibidos_por_onedrive_se_limpian():
    assert rev.nombre_foto({"id": 1, "nombre_archivo": 'a:b*c?.jpg'}, set()) == "a_b_c_.jpg"
    assert rev.nombre_video({"id": 8, "asignacion_id": None, "nombre_archivo": "mi video.mp4"}) == "A0_E8_mi video.mp4"


def test_subida_por_trozos_manda_rangos_correctos_y_no_carga_todo(monkeypatch, tmp_path):
    archivo = tmp_path / "v.mp4"
    archivo.write_bytes(b"a" * 25)
    monkeypatch.setattr(rev, "CHUNK", 10)
    od = types.SimpleNamespace(GRAPH_BASE="https://g", _get_token=lambda: "T")
    puts = []

    class R:
        def __init__(self, j=None): self._j, self.content, self.status_code = j or {}, b"x" if j else b"", 200
        def json(self): return self._j
        def raise_for_status(self): pass
    monkeypatch.setattr(rev.requests, "post", lambda url, **k: R({"uploadUrl": "https://up"}))
    monkeypatch.setattr(rev.requests, "put", lambda url, headers=None, data=None, timeout=0: puts.append((headers["Content-Range"], len(data))) or R({"id": "X"}))
    r = rev._subir_por_trozos(od, str(archivo), "carrier-transicold/Evidencias/a b.mp4", "video/mp4")
    assert puts == [("bytes 0-9/25", 10), ("bytes 10-19/25", 10), ("bytes 20-24/25", 5)] and r["id"] == "X"
