"""Galería del visor de Evidencias (JS real ejecutado con node, DOM y red simulados)."""
import asyncio, shutil, subprocess
import pytest
from routers import web_router as wr
from routers import evidencias_router as er


def _html():
    return asyncio.run(wr.admin()).body.decode("utf-8")


def test_html_tiene_flechas_contador_y_cerrar():
    h = _html()
    for k in ('id="ev-lb-prev"', 'id="ev-lb-next"', 'id="ev-lb-contador"', "evNavegar(1, event)", "evCerrarLightbox()"):
        assert k in h


def test_lista_acepta_hasta_500_por_pagina(monkeypatch):
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    vistos = []
    def read(sql, p=None):
        vistos.append(p)
        return [{"total": 0}] if "COUNT(*)" in sql else []
    monkeypatch.setattr(er, "execute_read", read)
    app = FastAPI(); app.include_router(er.router)
    app.dependency_overrides[er.require_admin_or_visor] = lambda: {"username": "a", "role": "admin"}
    TestClient(app).get("/api/evidencias/lista/CW1?per_page=99999")
    assert vistos[-1][-2:] == (500, 0)                       # LIMIT 500 OFFSET 0


@pytest.mark.skipif(not shutil.which("node"), reason="node no disponible")
def test_navegacion_de_la_galeria(tmp_path):
    h = _html()
    a, b = h.index("let evGal = "), h.index("// ── Banner de salud")
    js = """
const els = {}; const mk = id => els[id] = els[id] || { id, style: {}, textContent: '', innerHTML: '', value: '',
   removeAttribute(k){ delete this[k]; }, pause(){}, load(){}, append(){}, appendChild(){}, addEventListener(){} };
const document = { getElementById: mk, createElement: () => mk('x' + Math.random()),
   addEventListener: (ev, fn) => { if (ev === 'keydown') window.__teclado = fn; } };
const window = { addEventListener(){} };
const pedidos = [], revocados = [];
const URL = { createObjectURL: b => 'blob:' + b, revokeObjectURL: u => revocados.push(u) };
const LISTA = [1,2,3,4,5].map(i => ({ id: i, nombre: 'f'+i+'.jpg', tecnico: 'T', fecha: '2026-10-0'+i, actividad: 'Evidencia', tipo: i === 4 ? 'video' : 'foto' }));
const retardo = {};
const fetchAuth = async (url) => {
  pedidos.push(url);
  if (retardo[url.split('/').pop()]) await new Promise(r => setTimeout(r, retardo[url.split('/').pop()]));
  if (url.includes('/lista/')) return { ok: true, json: async () => ({ fotos: LISTA }) };
  const id = url.split('/').pop(); return { ok: true, blob: async () => 'b' + id };
};
mk('ev-select-unidad').value = 'CW1'; mk('ev-filtro-tipo').value = ''; mk('ev-filtro-act').value = '';
""" + h[a:b] + """
const espera = () => new Promise(r => setTimeout(r, 10));
const falla = m => { console.error(m); process.exit(1); };
(async () => {
  evAbrirLightbox(2, 'f2.jpg', 'T', '2026-10-02', 'Evidencia', 'foto', '');
  await espera();
  if (els['ev-lb-contador'].textContent !== '2 / 5') falla('contador inicial: ' + els['ev-lb-contador'].textContent);
  if (els['ev-lb-img'].src !== 'blob:b2') falla('debía mostrar la foto 2');
  if (!pedidos.some(u => u.includes('per_page=500'))) falla('debía pedir toda la lista');
  if (!pedidos.some(u => u.endsWith('/foto/3')) || !pedidos.some(u => u.endsWith('/foto/1'))) falla('debía precargar vecinas');
  evNavegar(1); await espera();                                   // -> 3
  if (els['ev-lb-img'].src !== 'blob:b3' || els['ev-lb-contador'].textContent !== '3 / 5') falla('siguiente');
  evNavegar(1); await espera();                                   // -> 4 (video: no se precarga y usa el reproductor)
  if (els['ev-lb-video'].style.display !== '' || els['ev-lb-video'].src !== 'blob:b4') falla('el video debe ir al reproductor');
  if (pedidos.filter(u => u.endsWith('/foto/4')).length !== 1) falla('el video no se debe descargar dos veces');
  evNavegar(1); evNavegar(1); await espera();                     // -> 5 -> 1 (da la vuelta)
  if (els['ev-lb-contador'].textContent !== '1 / 5') falla('debía dar la vuelta al final: ' + els['ev-lb-contador'].textContent);
  evNavegar(-1); await espera();                                  // -> 5 (hacia atrás desde el primero)
  if (els['ev-lb-contador'].textContent !== '5 / 5') falla('debía dar la vuelta al inicio');
  // desde la 5: +3 da la vuelta (1, 2, 3) y -2 vuelve a la 1
  evNavegar(1); evNavegar(1); evNavegar(1); evNavegar(-1); evNavegar(-1); await espera();
  if (els['ev-lb-img'].src !== 'blob:b1' || els['ev-lb-contador'].textContent !== '1 / 5') falla('cambio rápido: ' + els['ev-lb-img'].src);
  // teclado
  window.__teclado({ key: 'ArrowRight', preventDefault(){}, stopPropagation(){} }); await espera();
  if (els['ev-lb-contador'].textContent !== '2 / 5') falla('flecha derecha');
  window.__teclado({ key: 'ArrowLeft', preventDefault(){}, stopPropagation(){} }); await espera();
  if (els['ev-lb-contador'].textContent !== '1 / 5') falla('flecha izquierda');
  // cerrar con Esc: libera memoria y no navega más
  window.__teclado({ key: 'Escape', preventDefault(){}, stopPropagation(){} });
  if (els['ev-lightbox'].style.display !== 'none' || revocados.length === 0 || evGal.items.length !== 0) falla('Esc debía cerrar y liberar memoria');
  const antes = els['ev-lb-contador'].textContent;
  window.__teclado({ key: 'ArrowRight', preventDefault(){}, stopPropagation(){} });
  if (els['ev-lb-contador'].textContent !== antes) falla('con la galería cerrada las flechas no deben hacer nada');
  // una sola foto: sin flechas
  LISTA.length = 1; LISTA[0].id = 9;
  evAbrirLightbox(9, 'solo.jpg', 'T', '2026-10-09', '', 'foto', ''); await espera();
  if (els['ev-lb-prev'].style.display !== 'none' || els['ev-lb-contador'].textContent !== '') falla('con una sola foto no debe haber flechas');
  // respuesta TARDÍA: la foto 12 tarda en llegar, pero el usuario ya pasó a la 13 -> debe quedar la 13
  LISTA.length = 0; [11, 12, 13].forEach(i => LISTA.push({ id: i, nombre: 'f'+i+'.jpg', tecnico: 'T', fecha: '2026-10-10', actividad: '', tipo: 'foto' }));
  retardo['12'] = 60;
  evAbrirLightbox(11, 'f11.jpg', 'T', '2026-10-10', '', 'foto', ''); await espera();
  evNavegar(1); evNavegar(1);                                      // 12 (lenta) y enseguida 13
  await new Promise(r => setTimeout(r, 120));
  if (els['ev-lb-img'].src !== 'blob:b13') falla('una respuesta tardía pisó a la foto actual: ' + els['ev-lb-img'].src);
  console.log('OK');
})().catch(e => falla(e.stack || e.message));
"""
    f = tmp_path / "g.js"; f.write_text(js, encoding="utf-8")
    r = subprocess.run(["node", str(f)], capture_output=True, text=True)
    assert r.returncode == 0 and "OK" in r.stdout, r.stderr
