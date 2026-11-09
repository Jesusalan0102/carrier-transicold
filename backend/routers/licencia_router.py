"""Pantalla de activación (/activar) y API de licencia (/api/licencia/*). Ver licencia.py."""
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

import licencia

router = APIRouter(tags=["licencia"])


class ActivarRequest(BaseModel):
    serial: str


def _publico(est: dict) -> dict:
    """Solo lo que la pantalla de activación necesita mostrar (sin el id interno de la licencia)."""
    vence = None
    if est.get("vence_ts"):
        vence = datetime.fromtimestamp(est["vence_ts"], tz=timezone.utc).strftime("%Y-%m-%d")
    return {
        "requerida": est.get("requerida", False),
        "estado": est["estado"],
        "permitido": est["permitido"],
        "mensaje": est["mensaje"],
        "cliente": est.get("cliente"),
        "vence": vence,
        "dias_restantes": est.get("dias_restantes"),
        "instance_id": est.get("instance_id"),
    }


@router.get("/api/licencia/estado")
def estado_licencia():
    return _publico(licencia.estado_cacheado())


@router.post("/api/licencia/activar")
def activar_licencia(datos: ActivarRequest, request: Request):
    ip = (request.headers.get("x-forwarded-for", "").split(",")[0].strip()
          or (request.client.host if request.client else "?"))
    if licencia.demasiados_intentos(ip):
        raise HTTPException(status_code=429, detail="Demasiados intentos. Espera unos minutos e inténtalo de nuevo.")
    if not licencia.licencia_requerida():
        raise HTTPException(status_code=400, detail="Esta instalación no requiere activación.")
    try:
        est = licencia.activar(datos.serial, ip)
    except licencia.LicenciaError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return _publico(est)


@router.get("/activar", response_class=HTMLResponse, include_in_schema=False)
def pagina_activacion():
    return HTMLResponse(_HTML, headers={"Cache-Control": "no-store"})


_HTML = """<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Activar aplicación</title>
<style>
  :root { color-scheme: light dark; --azul:#0b3d91; --borde:#c9d3e6; --fondo:#f3f6fb; --txt:#1c2433; --tarjeta:#fff; }
  @media (prefers-color-scheme: dark) { :root { --fondo:#0f1624; --txt:#e8edf7; --tarjeta:#18223a; --borde:#2c3a5c; } }
  * { box-sizing: border-box; }
  body { margin:0; min-height:100vh; display:flex; align-items:center; justify-content:center; padding:16px;
         background:var(--fondo); color:var(--txt); font-family: system-ui, -apple-system, "Segoe UI", Roboto, sans-serif; }
  .card { width:100%; max-width:520px; background:var(--tarjeta); border:1px solid var(--borde); border-radius:14px;
          padding:28px; box-shadow:0 10px 30px rgba(0,0,0,.08); }
  h1 { margin:0 0 6px; font-size:1.35rem; }
  p { line-height:1.45; margin:.4rem 0; }
  .estado { margin:14px 0; padding:10px 12px; border-radius:10px; font-size:.92rem; border:1px solid var(--borde); }
  .ok { border-color:#2e9e5b; background:rgba(46,158,91,.12); }
  .warn { border-color:#d99a00; background:rgba(217,154,0,.12); }
  .err { border-color:#d64545; background:rgba(214,69,69,.12); }
  label { display:block; font-weight:600; margin:16px 0 6px; font-size:.9rem; }
  textarea { width:100%; min-height:110px; resize:vertical; padding:10px; border-radius:10px; border:1px solid var(--borde);
             background:transparent; color:inherit; font-family: ui-monospace, Consolas, monospace; font-size:.8rem; word-break:break-all; }
  button { cursor:pointer; border:0; border-radius:10px; padding:11px 18px; font-size:1rem; font-weight:600; }
  #btn { width:100%; margin-top:14px; background:var(--azul); color:#fff; }
  #btn[disabled] { opacity:.6; cursor:wait; }
  .inst { display:flex; gap:8px; align-items:center; margin-top:6px; }
  .inst code { flex:1; padding:8px 10px; border:1px dashed var(--borde); border-radius:8px; font-size:.85rem; word-break:break-all; }
  .inst button { padding:8px 12px; font-size:.85rem; background:transparent; border:1px solid var(--borde); color:inherit; }
  small { opacity:.7; }
  a.entrar { display:inline-block; margin-top:10px; color:var(--azul); font-weight:600; }
</style>
</head>
<body>
<div class="card">
  <h1>Activar la aplicación</h1>
  <p>Para iniciar sesión, ingresa el serial de activación que te entregó tu proveedor.</p>
  <div id="estado" class="estado">Verificando licencia…</div>

  <div id="formulario">
    <label for="serial">Serial de activación</label>
    <textarea id="serial" placeholder="CTL1.xxxxxxxx.xxxxxxxx" spellcheck="false" autocomplete="off"></textarea>
    <button id="btn" type="button">Activar</button>
  </div>

  <label style="margin-top:22px">ID de esta instalación <small>(si tu proveedor lo pide)</small></label>
  <div class="inst"><code id="inst">—</code><button type="button" id="copiar">Copiar</button></div>
</div>

<script>
const $ = (id) => document.getElementById(id);
function pintar(e) {
  const caja = $('estado');
  let clase = 'err', texto = e.mensaje || '';
  if (e.estado === 'activa' || e.estado === 'no_requerida') clase = 'ok';
  else if (e.estado === 'en_gracia') clase = 'warn';
  if (e.permitido && e.estado !== 'no_requerida') {
    texto = '✅ ' + (e.cliente ? 'Licencia de ' + e.cliente + '. ' : '') + e.mensaje + (e.vence ? ' Vence: ' + e.vence + '.' : '');
    caja.innerHTML = '';
    caja.className = 'estado ' + clase;
    caja.append(texto, document.createElement('br'));
    const a = document.createElement('a'); a.href = '/app'; a.className = 'entrar'; a.textContent = 'Ir a iniciar sesión →';
    caja.append(a);
  } else {
    caja.className = 'estado ' + clase;
    caja.textContent = texto;
  }
  $('inst').textContent = e.instance_id || '—';
}
async function cargar() {
  try { pintar(await (await fetch('/api/licencia/estado')).json()); }
  catch (_) { $('estado').className = 'estado err'; $('estado').textContent = 'No se pudo consultar el estado de la licencia.'; }
}
$('btn').addEventListener('click', async () => {
  const serial = $('serial').value.trim();
  if (!serial) { $('estado').className = 'estado err'; $('estado').textContent = 'Pega el serial de activación.'; return; }
  $('btn').disabled = true;
  try {
    const r = await fetch('/api/licencia/activar', { method: 'POST', headers: { 'Content-Type': 'application/json' },
                                                     body: JSON.stringify({ serial }) });
    const d = await r.json();
    if (!r.ok) { $('estado').className = 'estado err'; $('estado').textContent = d.detail || 'No se pudo activar.'; }
    else { pintar(d); setTimeout(() => { location.href = '/app'; }, 1200); }
  } catch (_) { $('estado').className = 'estado err'; $('estado').textContent = 'Error de conexión. Inténtalo de nuevo.'; }
  $('btn').disabled = false;
});
$('copiar').addEventListener('click', () => { navigator.clipboard && navigator.clipboard.writeText($('inst').textContent); });
cargar();
</script>
</body>
</html>
"""
