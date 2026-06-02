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
  <link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600&family=DM+Mono:wght@400;500&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@tabler/icons-webfont@latest/tabler-icons.min.css">
  <style>
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: 'DM Sans', system-ui, sans-serif;
      background: #F4F4F0;
      min-height: 100vh;
      color: #1a1a1a;
      padding: 1rem;
    }
    .ct-wrap { width: 100%; max-width: 440px; margin: 0 auto; }
    .ct-header { display: flex; align-items: center; gap: 12px; margin-bottom: 1.5rem; }
    .ct-logo { width: 50px; height: 50px; background: #004B87; border-radius: 12px; display: flex; align-items: center; justify-content: center; }
    .ct-title { font-size: 18px; font-weight: 600; }
    .ct-card {
      background: white;
      border: 0.5px solid #e0ddd5;
      border-radius: 14px;
      padding: 1.25rem;
      margin-bottom: 1rem;
    }
    .ct-section-label {
      font-size: 10px; font-weight: 600; letter-spacing: 0.08em; 
      text-transform: uppercase; color: #888; margin-bottom: 12px;
    }
    .ct-schedule {
      display: grid; grid-template-columns: 1fr 1fr; gap: 12px;
      background: #F7F6F2; border-radius: 12px; padding: 14px;
    }
    .ct-schedule-col { text-align: center; }
    .ct-schedule-label { font-size: 11px; color: #666; }
    .ct-schedule-time { font-family: 'DM Mono', monospace; font-size: 26px; font-weight: 500; }

    /* Tabla Horarios */
    .ct-horarios-table { width: 100%; border-collapse: collapse; }
    .ct-horarios-table th { text-align: left; font-size: 11px; color: #888; padding: 8px 0; }
    .ct-horarios-table td { padding: 10px 0; border-top: 0.5px solid #f0ede5; font-size: 14px; }
    .ct-horarios-table .hora { font-family: 'DM Mono', monospace; font-weight: 500; }

    /* Botón */
    .ct-btn-primary {
      width: 100%; padding: 14px; background: #004B87; color: white;
      border: none; border-radius: 10px; font-weight: 600; font-size: 15px;
      cursor: pointer; display: flex; align-items: center; justify-content: center; gap: 8px;
    }
  </style>
</head>
<body>
<div class="ct-wrap">

  <!-- Header -->
  <div class="ct-header">
    <div class="ct-logo"><i class="ti ti-building-factory" style="font-size:28px;color:white;"></i></div>
    <div>
      <div class="ct-title">Carrier Transicold</div>
      <small id="ct-fecha" style="color:#666;"></small>
    </div>
  </div>

  <!-- MIS HORARIOS -->
  <div class="ct-card">
    <div class="ct-section-label">📅 Mis Horarios</div>
    <table class="ct-horarios-table" id="tabla-mis-horarios">
      <thead><tr><th>Fecha</th><th>Entrada</th><th>Salida</th></tr></thead>
      <tbody></tbody>
    </table>
  </div>

  <!-- HORARIO DE HOY -->
  <div class="ct-card">
    <div class="ct-section-label">HOY • <span id="ct-hora-actual"></span></div>
    <div class="ct-schedule">
      <div class="ct-schedule-col">
        <div class="ct-schedule-label">Entrada</div>
        <div class="ct-schedule-time" id="p-hora-entrada">--:--</div>
      </div>
      <div class="ct-schedule-col">
        <div class="ct-schedule-label">Salida</div>
        <div class="ct-schedule-time" id="p-hora-salida">--:--</div>
      </div>
    </div>
    <button class="ct-btn-primary" onclick="abrirModalQR()" style="margin-top: 16px;">
      <i class="ti ti-qrcode"></i> Registrar Asistencia (QR)
    </button>
  </div>

</div>

<!-- ==================== MODAL QR COMPLETO ==================== -->
<div class="ct-modal-overlay" id="ct-modal-overlay">
  <div class="ct-modal">
    <div class="ct-modal-header">
      <div class="ct-modal-title"><i class="ti ti-qrcode"></i> Validación de Asistencia</div>
      <button class="ct-modal-close" onclick="cerrarModalQR()">✕</button>
    </div>

    <!-- Paso 1: Escanear QR -->
    <div id="ct-paso1" class="ct-paso">
      <div style="padding:16px;">
        <div style="position:relative;background:#0A1521;border-radius:12px;overflow:hidden;">
          <video id="ct-qr-video" style="width:100%;display:block;" playsinline autoplay muted></video>
          <canvas id="ct-qr-canvas" style="display:none;"></canvas>
          <div id="ct-scan-line" style="position:absolute;left:0;right:0;height:3px;background:linear-gradient(90deg,transparent,#00ffcc,#00ffcc,transparent);animation:scan 2s linear infinite;"></div>
        </div>
        <div style="text-align:center;margin-top:12px;color:#666;font-size:13px;">Apunta al código QR de la sucursal</div>
      </div>
    </div>

    <!-- Paso 2: Selfie -->
    <div id="ct-paso2" class="ct-paso" style="display:none;padding:16px;">
      <div style="text-align:center;">
        <button class="ct-btn-primary" onclick="ct_lanzarFotoConfirmacion()" style="margin:20px 0;">
          <i class="ti ti-camera-selfie"></i> Tomar Selfie
        </button>
      </div>
    </div>

    <!-- Paso 3: Confirmar -->
    <div id="ct-paso3" class="ct-paso" style="display:none;padding:16px;">
      <img id="ct-preview-img" style="width:100%;border-radius:12px;margin-bottom:12px;">
      <button id="ct-btn-confirmar" class="ct-btn-primary" onclick="ct_confirmarRegistro()">
        ✅ Confirmar Registro
      </button>
    </div>
  </div>
</div>

<script>
// Variables globales
let currentTipo = "entrada";
let currentFoto = null;

// Hora Tijuana
function actualizarHoraTijuana() {
  const opciones = { timeZone: 'America/Tijuana', hour: '2-digit', minute: '2-digit', hour12: true };
  document.getElementById('ct-hora-actual').textContent = new Intl.DateTimeFormat('es-MX', opciones).format(new Date());
}
setInterval(actualizarHoraTijuana, 30000);
actualizarHoraTijuana();

// Fecha
document.getElementById('ct-fecha').textContent = new Date().toLocaleDateString('es-MX', { weekday:'long', day:'numeric', month:'long' });

// Cargar Mis Horarios
async function cargarMisHorarios() {
  try {
    const res = await window.fetchAuth('/api/horarios/mios');
    const data = await res.json();
    const tbody = document.querySelector('#tabla-mis-horarios tbody');
    tbody.innerHTML = data.map(h => `
      <tr>
        <td>${h.fecha}</td>
        <td class="hora">${h.hora_entrada || '—'}</td>
        <td class="hora">${h.hora_salida || '—'}</td>
      </tr>
    `).join('');
  } catch(e) { console.error(e); }
}

// Cargar horario hoy
async function cargarHorarioHoy() {
  try {
    const hoy = new Date().toISOString().split('T')[0];
    const username = window.__ct_username || '';
    const res = await window.fetchAuth(`/api/horarios/hoy?username=${username}&fecha=${hoy}`);
    const data = await res.json();
    const h = data.horario || {};
    document.getElementById('p-hora-entrada').textContent = h.hora_entrada?.slice(0,5) || '--:--';
    document.getElementById('p-hora-salida').textContent = h.hora_salida?.slice(0,5) || '--:--';
  } catch(e) {}
}

// Modal
window.abrirModalQR = () => {
  document.getElementById('ct-modal-overlay').style.display = 'flex';
  document.getElementById('ct-paso1').style.display = 'block';
  document.getElementById('ct-paso2').style.display = 'none';
  document.getElementById('ct-paso3').style.display = 'none';
};

window.cerrarModalQR = () => {
  document.getElementById('ct-modal-overlay').style.display = 'none';
};

// Iniciar
document.addEventListener('DOMContentLoaded', () => {
  cargarMisHorarios();
  cargarHorarioHoy();
});
</script>
</body>
</html>"""
