# -*- coding: utf-8 -*-
ASISTENCIA_STYLES = """
<style>
    .brand-blue { background-color: #004B87; }
    .brand-dark { background-color: #0A2540; }
    .text-brand { color: #004B87; }
    .bg-gray-custom { background-color: #F4F4F2; }
</style>
"""

def get_checkin_template() -> str:
    """
    Template actualizado - Carrier Transicold
    Incluye: Mis Horarios + Registro de Asistencia + Hora Tijuana correcta
    """
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
    
    /* Mis Horarios */
    .ct-horarios-table {
      width: 100%; border-collapse: collapse;
    }
    .ct-horarios-table th {
      text-align: left; font-size: 11px; color: #888; padding: 8px 0;
    }
    .ct-horarios-table td {
      padding: 10px 0; border-top: 0.5px solid #f0ede5;
      font-size: 14px;
    }
    .ct-horarios-table .hora { font-family: 'DM Mono', monospace; font-weight: 500; }
  </style>
</head>
<body>
<div class="ct-wrap">

  <!-- Header -->
  <div class="ct-header">
    <div class="ct-logo">
      <i class="ti ti-building-factory" style="font-size:28px;color:white;"></i>
    </div>
    <div>
      <div class="ct-title">Carrier Transicold</div>
      <small id="ct-fecha" style="color:#666;"></small>
    </div>
  </div>

  <!-- MIS HORARIOS -->
  <div class="ct-card">
    <div class="ct-section-label">📅 Mis Horarios</div>
    <table class="ct-horarios-table" id="tabla-mis-horarios">
      <thead>
        <tr>
          <th>Fecha</th>
          <th>Entrada</th>
          <th>Salida</th>
        </tr>
      </thead>
      <tbody></tbody>
    </table>
  </div>

  <!-- HORARIO DE HOY -->
  <div class="ct-card">
    <div class="ct-section-label">Hoy • <span id="ct-hora-actual"></span></div>
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
    <button class="ct-btn-primary" onclick="abrirModalQR()" style="width:100%; margin-top:12px; padding:14px;">
      <i class="ti ti-qrcode"></i> Registrar Asistencia (QR)
    </button>
  </div>

</div>

<script>
(async function () {
  const username = window.__ct_username || '';

  // Fecha y hora Tijuana
  function actualizarHoraTijuana() {
    const opciones = { timeZone: 'America/Tijuana', hour: '2-digit', minute: '2-digit' };
    const hora = new Intl.DateTimeFormat('es-MX', opciones).format(new Date());
    document.getElementById('ct-hora-actual').textContent = hora;
  }
  setInterval(actualizarHoraTijuana, 30000);
  actualizarHoraTijuana();

  // Fecha legible
  document.getElementById('ct-fecha').textContent = new Date().toLocaleDateString('es-MX', {
    weekday: 'long', day: 'numeric', month: 'long'
  });

  // Cargar Mis Horarios
  async function cargarMisHorarios() {
    try {
      const res = await window.fetchAuth('/api/horarios/mios');
      const data = await res.json();
      const tbody = document.querySelector('#tabla-mis-horarios tbody');
      tbody.innerHTML = '';

      if (!data || data.length === 0) {
        tbody.innerHTML = `<tr><td colspan="3" style="text-align:center;color:#888;padding:20px;">No tienes horarios asignados</td></tr>`;
        return;
      }

      data.forEach(h => {
        const row = document.createElement('tr');
        row.innerHTML = `
          <td>${h.fecha}</td>
          <td class="hora">${h.hora_entrada || '—'}</td>
          <td class="hora">${h.hora_salida || '—'}</td>
        `;
        tbody.appendChild(row);
      });
    } catch (e) {
      console.error("Error cargando mis horarios:", e);
    }
  }

  // Cargar horario de hoy
  async function cargarHorarioHoy() {
    try {
      const hoy = new Date().toISOString().split('T')[0];
      const res = await window.fetchAuth(`/api/horarios/hoy?username=${encodeURIComponent(username)}&fecha=${hoy}`);
      const data = await res.json();
      const h = data.horario || {};

      document.getElementById('p-hora-entrada').textContent = h.hora_entrada ? h.hora_entrada.slice(0,5) : '--:--';
      document.getElementById('p-hora-salida').textContent = h.hora_salida ? h.hora_salida.slice(0,5) : '--:--';
    } catch (e) {
      console.warn("No se pudo cargar horario de hoy", e);
    }
  }

  // Inicializar
  await Promise.all([cargarMisHorarios(), cargarHorarioHoy()]);

})();
</script>
</body>
</html>"""
