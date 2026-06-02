# -*- coding: utf-8 -*-
ASISTENCIA_STYLES = """
<style>
    .brand-blue { background-color: #004B87; }
    .text-brand { color: #004B87; }
</style>
"""

def get_checkin_template() -> str:
    return """<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Carrier Transicold — Asistencia</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,300;0,9..40,400;0,9..40,500;0,9..40,600;1,9..40,400&family=DM+Mono:wght@400;500&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@tabler/icons-webfont@latest/tabler-icons.min.css">
  <style>
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

    :root {
      --blue:       #004B87;
      --blue-light: #0066BB;
      --blue-dim:   #E8F0F8;
      --green:      #16A34A;
      --green-dim:  #DCFCE7;
      --amber:      #D97706;
      --amber-dim:  #FEF3C7;
      --red:        #DC2626;
      --red-dim:    #FEE2E2;
      --bg:         #F2F1ED;
      --card:       #FFFFFF;
      --border:     rgba(0,0,0,0.07);
      --text:       #111827;
      --muted:      #6B7280;
      --radius:     16px;
    }

    body {
      font-family: 'DM Sans', system-ui, sans-serif;
      background: var(--bg);
      min-height: 100vh;
      color: var(--text);
      padding: 1rem 1rem 6rem;
    }

    .ct-wrap { width: 100%; max-width: 460px; margin: 0 auto; }

    /* ── Greeting card ── */
    .ct-greeting {
      background: var(--blue);
      border-radius: var(--radius);
      padding: 1.25rem 1.5rem;
      color: white;
      margin-bottom: 1rem;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
    }
    .ct-greeting-left h2 { font-size: 18px; font-weight: 600; }
    .ct-greeting-left p  { font-size: 13px; opacity: 0.75; margin-top: 2px; }
    .ct-greeting-time {
      font-family: 'DM Mono', monospace;
      font-size: 28px;
      font-weight: 500;
      letter-spacing: -1px;
      white-space: nowrap;
    }

    /* ── Estado de hoy ── */
    .ct-today {
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: var(--radius);
      padding: 1.25rem;
      margin-bottom: 1rem;
    }
    .ct-today-label {
      font-size: 11px; font-weight: 600; letter-spacing: 0.08em;
      text-transform: uppercase; color: var(--muted); margin-bottom: 14px;
    }
    .ct-times {
      display: grid; grid-template-columns: 1fr 1fr; gap: 10px;
      margin-bottom: 16px;
    }
    .ct-time-box {
      background: var(--bg);
      border-radius: 12px;
      padding: 14px;
      text-align: center;
    }
    .ct-time-box .label { font-size: 11px; color: var(--muted); margin-bottom: 6px; }
    .ct-time-box .value {
      font-family: 'DM Mono', monospace;
      font-size: 24px; font-weight: 500; color: var(--text);
    }
    .ct-time-box .value.registered { color: var(--green); }

    /* GPS pill */
    .ct-gps-pill {
      display: inline-flex; align-items: center; gap: 6px;
      background: var(--bg); border-radius: 20px;
      padding: 6px 12px; font-size: 12px; color: var(--muted);
      margin-bottom: 16px;
    }
    .ct-gps-pill .dot {
      width: 8px; height: 8px; border-radius: 50%;
      background: var(--muted); flex-shrink: 0;
      transition: background 0.3s;
    }
    .ct-gps-pill .dot.ok   { background: var(--green); }
    .ct-gps-pill .dot.warn { background: var(--amber); }
    .ct-gps-pill .dot.bad  { background: var(--red); }

    /* Botones de acción */
    .ct-actions { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
    .ct-btn {
      padding: 14px 10px; border: none; border-radius: 12px;
      font-family: inherit; font-size: 14px; font-weight: 600;
      cursor: pointer; display: flex; align-items: center;
      justify-content: center; gap: 7px; transition: opacity 0.15s, transform 0.1s;
    }
    .ct-btn:active { transform: scale(0.97); opacity: 0.85; }
    .ct-btn-entrada { background: var(--blue); color: white; }
    .ct-btn-salida  { background: var(--blue-dim); color: var(--blue); }
    .ct-btn:disabled { opacity: 0.4; pointer-events: none; }

    /* ── Historial ── */
    .ct-history {
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: var(--radius);
      overflow: hidden;
      margin-bottom: 1rem;
    }
    .ct-history-header {
      padding: 1rem 1.25rem 0.75rem;
      font-size: 11px; font-weight: 600; letter-spacing: 0.08em;
      text-transform: uppercase; color: var(--muted);
      border-bottom: 1px solid var(--border);
    }
    .ct-history-row {
      display: grid; grid-template-columns: 1fr 80px 80px;
      padding: 11px 1.25rem;
      border-bottom: 1px solid var(--border);
      align-items: center; font-size: 14px;
    }
    .ct-history-row:last-child { border-bottom: none; }
    .ct-history-row .fecha { color: var(--muted); font-size: 13px; }
    .ct-history-row .mono  { font-family: 'DM Mono', monospace; font-size: 13px; font-weight: 500; }
    .ct-history-row .mono.ok  { color: var(--green); }
    .ct-history-row .mono.dim { color: var(--muted); }

    /* ── Modal overlay ── */
    .ct-modal-overlay {
      position: fixed; inset: 0;
      background: rgba(0,0,0,0.55);
      backdrop-filter: blur(4px);
      z-index: 999;
      display: none; align-items: flex-end; justify-content: center;
    }
    .ct-modal-overlay.open { display: flex; }

    .ct-modal {
      background: var(--card);
      border-radius: 24px 24px 0 0;
      width: 100%; max-width: 480px;
      max-height: 92vh;
      overflow-y: auto;
      animation: slideUp 0.28s cubic-bezier(0.34,1.3,0.64,1);
    }
    @keyframes slideUp {
      from { transform: translateY(60px); opacity: 0; }
      to   { transform: translateY(0);    opacity: 1; }
    }

    /* Progress steps */
    .ct-steps {
      display: flex; align-items: center; justify-content: center;
      gap: 8px; padding: 20px 24px 0;
    }
    .ct-step-dot {
      width: 8px; height: 8px; border-radius: 50%;
      background: #E5E7EB; transition: all 0.3s;
    }
    .ct-step-dot.active  { background: var(--blue); width: 24px; border-radius: 4px; }
    .ct-step-dot.done    { background: var(--green); }

    .ct-modal-drag {
      width: 40px; height: 4px; background: #E5E7EB;
      border-radius: 2px; margin: 12px auto 0;
    }

    .ct-modal-head {
      display: flex; align-items: center; justify-content: space-between;
      padding: 16px 20px 12px;
    }
    .ct-modal-head h3 { font-size: 17px; font-weight: 600; }
    .ct-modal-head p  { font-size: 13px; color: var(--muted); margin-top: 2px; }
    .ct-modal-close {
      width: 32px; height: 32px; border-radius: 50%;
      background: var(--bg); border: none; cursor: pointer;
      font-size: 16px; display: flex; align-items: center; justify-content: center;
      color: var(--muted); flex-shrink: 0;
    }

    .ct-paso { padding: 0 20px 24px; }

    /* Scanner */
    .ct-scanner-wrap {
      position: relative; background: #0A1521;
      border-radius: 16px; overflow: hidden;
      aspect-ratio: 1 / 1;
    }
    #ct-qr-video { width: 100%; height: 100%; object-fit: cover; display: block; }
    .ct-scanner-frame {
      position: absolute; inset: 0;
      display: flex; align-items: center; justify-content: center;
    }
    .ct-scanner-frame svg { width: 65%; height: 65%; opacity: 0.6; }
    .ct-scan-line {
      position: absolute; left: 12%; right: 12%;
      height: 2px;
      background: linear-gradient(90deg, transparent, #00FFCC, #00FFCC, transparent);
      animation: scanMove 2s ease-in-out infinite;
    }
    @keyframes scanMove {
      0%   { top: 20%; }
      50%  { top: 80%; }
      100% { top: 20%; }
    }
    #ct-qr-status {
      text-align: center; font-size: 13px; color: var(--muted);
      margin-top: 12px; min-height: 20px;
    }
    .ct-qr-ok {
      background: var(--green-dim); color: var(--green);
      border-radius: 8px; padding: 8px 14px;
      font-size: 13px; font-weight: 500;
      text-align: center; display: none; margin-top: 10px;
    }

    /* Selfie paso 2 */
    .ct-selfie-area {
      text-align: center; padding: 10px 0 6px;
    }
    .ct-selfie-icon {
      width: 80px; height: 80px; border-radius: 50%;
      background: var(--blue-dim);
      display: flex; align-items: center; justify-content: center;
      margin: 0 auto 16px;
      font-size: 36px; color: var(--blue);
    }
    .ct-selfie-area h4 { font-size: 16px; font-weight: 600; margin-bottom: 6px; }
    .ct-selfie-area p  { font-size: 13px; color: var(--muted); line-height: 1.5; }

    /* Preview paso 3 */
    #ct-preview-img {
      width: 100%; border-radius: 14px;
      margin-bottom: 14px; display: none;
      max-height: 240px; object-fit: cover;
    }
    .ct-confirm-info {
      background: var(--bg); border-radius: 12px;
      padding: 14px; margin-bottom: 16px;
      display: grid; grid-template-columns: 1fr 1fr; gap: 10px;
    }
    .ct-confirm-info .item .k { font-size: 11px; color: var(--muted); text-transform: uppercase; letter-spacing: 0.05em; }
    .ct-confirm-info .item .v { font-size: 14px; font-weight: 600; margin-top: 2px; }

    /* Botón primario modal */
    .ct-modal-btn {
      width: 100%; padding: 15px; border: none; border-radius: 12px;
      background: var(--blue); color: white;
      font-family: inherit; font-size: 15px; font-weight: 600;
      cursor: pointer; display: flex; align-items: center;
      justify-content: center; gap: 8px;
      transition: opacity 0.15s, transform 0.1s;
    }
    .ct-modal-btn:active  { transform: scale(0.98); opacity: 0.9; }
    .ct-modal-btn:disabled { opacity: 0.4; pointer-events: none; }
    .ct-modal-btn.success { background: var(--green); }

    /* Toast */
    .ct-toast {
      position: fixed; bottom: 80px; left: 50%; transform: translateX(-50%) translateY(20px);
      background: #111; color: white; border-radius: 12px;
      padding: 12px 20px; font-size: 14px; font-weight: 500;
      white-space: nowrap; opacity: 0; pointer-events: none;
      transition: all 0.3s; z-index: 1100;
    }
    .ct-toast.show { opacity: 1; transform: translateX(-50%) translateY(0); }
    .ct-toast.green { background: var(--green); }
    .ct-toast.red   { background: var(--red); }

    /* Animación scan */
    @keyframes scan {
      0%   { top: 10%; }
      50%  { top: 85%; }
      100% { top: 10%; }
    }
  </style>
</head>
<body>
<div class="ct-wrap">

  <!-- Saludo / tiempo -->
  <div class="ct-greeting">
    <div class="ct-greeting-left">
      <h2 id="ct-saludo">Hola 👋</h2>
      <p id="ct-fecha">—</p>
    </div>
    <div class="ct-greeting-time" id="ct-hora-actual">--:--</div>
  </div>

  <!-- Estado de hoy -->
  <div class="ct-today">
    <div class="ct-today-label">Turno de hoy</div>

    <div class="ct-times">
      <div class="ct-time-box">
        <div class="label"><i class="ti ti-login"></i> Entrada</div>
        <div class="value" id="p-hora-entrada">--:--</div>
      </div>
      <div class="ct-time-box">
        <div class="label"><i class="ti ti-logout"></i> Salida</div>
        <div class="value" id="p-hora-salida">--:--</div>
      </div>
    </div>

    <div class="ct-gps-pill">
      <div class="dot" id="ct-gps-dot"></div>
      <span id="ct-gps-label">Obteniendo ubicación...</span>
    </div>

    <div class="ct-actions">
      <button class="ct-btn ct-btn-entrada" onclick="abrirModalQR('entrada')">
        <i class="ti ti-login"></i> Entrada
      </button>
      <button class="ct-btn ct-btn-salida" onclick="abrirModalQR('salida')">
        <i class="ti ti-logout"></i> Salida
      </button>
    </div>
  </div>

  <!-- Historial reciente -->
  <div class="ct-history">
    <div class="ct-history-header">📋 Historial reciente</div>
    <div id="ct-historial-body">
      <div style="padding:20px;text-align:center;color:var(--muted);font-size:13px;">Cargando...</div>
    </div>
  </div>

</div>

<!-- ==================== MODAL ==================== -->
<div class="ct-modal-overlay" id="ct-modal-overlay">
  <div class="ct-modal">
    <div class="ct-modal-drag"></div>

    <!-- Progress dots -->
    <div class="ct-steps">
      <div class="ct-step-dot active" id="dot1"></div>
      <div class="ct-step-dot" id="dot2"></div>
      <div class="ct-step-dot" id="dot3"></div>
    </div>

    <div class="ct-modal-head">
      <div>
        <h3 id="ct-modal-title">Escanear QR</h3>
        <p id="ct-modal-subtitle">Apunta la cámara al código QR</p>
      </div>
      <button class="ct-modal-close" onclick="cerrarModalQR()">✕</button>
    </div>

    <!-- Paso 1: QR Scanner -->
    <div id="ct-paso1" class="ct-paso">
      <div class="ct-scanner-wrap">
        <video id="ct-qr-video" playsinline autoplay muted></video>
        <canvas id="ct-qr-canvas" style="display:none;"></canvas>
        <div class="ct-scanner-frame">
          <svg viewBox="0 0 200 200" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M20 60V20H60" stroke="white" stroke-width="6" stroke-linecap="round"/>
            <path d="M140 20H180V60" stroke="white" stroke-width="6" stroke-linecap="round"/>
            <path d="M180 140V180H140" stroke="white" stroke-width="6" stroke-linecap="round"/>
            <path d="M60 180H20V140" stroke="white" stroke-width="6" stroke-linecap="round"/>
          </svg>
        </div>
        <div class="ct-scan-line"></div>
      </div>
      <div id="ct-qr-status">Buscando código QR...</div>
      <div class="ct-qr-ok" id="ct-qr-result">✅ QR válido detectado</div>
    </div>

    <!-- Paso 2: Selfie -->
    <div id="ct-paso2" class="ct-paso" style="display:none;">
      <div class="ct-selfie-area">
        <div class="ct-selfie-icon"><i class="ti ti-camera-selfie"></i></div>
        <h4>Confirma tu identidad</h4>
        <p>Toma una foto para verificar<br>que eres tú quien registra la asistencia</p>
      </div>
      <div style="height:16px;"></div>
      <button class="ct-modal-btn" onclick="ct_lanzarFotoConfirmacion()">
        <i class="ti ti-camera"></i> Tomar selfie
      </button>
      <input type="file" id="ct-input-selfie" accept="image/*" capture="user"
             style="display:none;" onchange="ct_onSelfieSeleccionada(this)">
    </div>

    <!-- Paso 3: Confirmar -->
    <div id="ct-paso3" class="ct-paso" style="display:none;">
      <img id="ct-preview-img" alt="Selfie">
      <div class="ct-confirm-info">
        <div class="item">
          <div class="k">Tipo</div>
          <div class="v" id="ct-paso3-tipo">—</div>
        </div>
        <div class="item">
          <div class="k">Hora</div>
          <div class="v" id="ct-paso3-hora">—</div>
        </div>
        <div class="item">
          <div class="k">GPS</div>
          <div class="v" id="ct-paso3-gps">—</div>
        </div>
        <div class="item">
          <div class="k">Usuario</div>
          <div class="v" id="ct-paso3-user">—</div>
        </div>
      </div>
      <button id="ct-btn-confirmar" class="ct-modal-btn" onclick="ct_confirmarRegistro()">
        ✅ Confirmar registro
      </button>
    </div>

  </div>
</div>

<!-- Toast -->
<div class="ct-toast" id="ct-toast"></div>

<script>
// ── Utilidades UI ──────────────────────────────────────────────────────────
function ctToast(msg, type) {
  var t = document.getElementById('ct-toast');
  t.textContent = msg;
  t.className = 'ct-toast show ' + (type || '');
  setTimeout(function() { t.className = 'ct-toast'; }, 3200);
}

// ── Hora / Fecha ───────────────────────────────────────────────────────────
function actualizarHora() {
  var tz = 'America/Tijuana';
  var hora = new Intl.DateTimeFormat('es-MX', { timeZone: tz, hour: '2-digit', minute: '2-digit', hour12: false }).format(new Date());
  document.getElementById('ct-hora-actual').textContent = hora;
}
setInterval(actualizarHora, 15000);
actualizarHora();

var ahora = new Date();
document.getElementById('ct-fecha').textContent = ahora.toLocaleDateString('es-MX', { weekday:'long', day:'numeric', month:'long' });

var h = new Date().toLocaleString('es-MX', { timeZone:'America/Tijuana', hour:'numeric', hour12:false });
var saludo = parseInt(h) < 12 ? '¡Buenos días 👋' : parseInt(h) < 19 ? '¡Buenas tardes 👋' : '¡Buenas noches 👋';
document.getElementById('ct-saludo').textContent = saludo;

// ── Carga de datos ─────────────────────────────────────────────────────────
async function cargarHorarioHoy() {
  try {
    var hoy = new Date().toISOString().split('T')[0];
    var username = window.__ct_username || '';
    var res = await window.fetchAuth('/api/horarios/hoy?username=' + username + '&fecha=' + hoy);
    var data = await res.json();
    var h = data.horario || {};
    var eEl = document.getElementById('p-hora-entrada');
    var sEl = document.getElementById('p-hora-salida');
    if (h.hora_entrada) { eEl.textContent = h.hora_entrada.slice(0,5); eEl.classList.add('registered'); }
    if (h.hora_salida)  { sEl.textContent = h.hora_salida.slice(0,5);  sEl.classList.add('registered'); }
  } catch(e) {}
}

async function cargarMisHorarios() {
  try {
    var res = await window.fetchAuth('/api/horarios/mios');
    var data = await res.json();
    var body = document.getElementById('ct-historial-body');
    if (!data || data.length === 0) {
      body.innerHTML = '<div style="padding:20px;text-align:center;color:var(--muted);font-size:13px;">Sin registros recientes</div>';
      return;
    }
    body.innerHTML = data.slice(0, 7).map(function(h) {
      var entrada = h.hora_entrada ? '<span class="mono ok">' + h.hora_entrada.slice(0,5) + '</span>' : '<span class="mono dim">—</span>';
      var salida  = h.hora_salida  ? '<span class="mono ok">' + h.hora_salida.slice(0,5)  + '</span>' : '<span class="mono dim">—</span>';
      return '<div class="ct-history-row"><span class="fecha">' + h.fecha + '</span>' + entrada + salida + '</div>';
    }).join('');
  } catch(e) {}
}

// Las funciones abrirModalQR y cerrarModalQR son inyectadas por web_router.py (init_script)

// ── GPS badge ──────────────────────────────────────────────────────────────
function _actualizarGPSBadge(accuracy) {
  var dot   = document.getElementById('ct-gps-dot');
  var label = document.getElementById('ct-gps-label');
  if (!dot) return;
  if (accuracy <= 50) {
    dot.className = 'dot ok';
    label.textContent = 'Ubicación precisa (±' + Math.round(accuracy) + 'm)';
  } else if (accuracy <= 120) {
    dot.className = 'dot warn';
    label.textContent = 'Ubicación aceptable (±' + Math.round(accuracy) + 'm)';
  } else {
    dot.className = 'dot bad';
    label.textContent = 'Señal GPS débil (±' + Math.round(accuracy) + 'm)';
  }
}

// ── Init ───────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', function() {
  cargarHorarioHoy();
  cargarMisHorarios();
  if (navigator.geolocation) {
    navigator.geolocation.getCurrentPosition(
      function(pos) { _actualizarGPSBadge(pos.coords.accuracy); },
      function() {
        var dot = document.getElementById('ct-gps-dot');
        var label = document.getElementById('ct-gps-label');
        if (dot) dot.className = 'dot bad';
        if (label) label.textContent = 'Sin permiso de ubicación';
      },
      { enableHighAccuracy: true, timeout: 10000 }
    );
  }
});
</script>
</body>
</html>"""
