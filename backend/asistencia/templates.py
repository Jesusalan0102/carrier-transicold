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
    Retorna el diseño HTML profesional para el registro de asistencia.
    Carrier Transicold — v2.0
    Incluye: vista pendiente, vista rechazada con explicación, modal QR animado.
    Datos dinámicos inyectados vía JS desde el backend (/api/horarios/hoy, /api/asistencia/registros).
    """
    return """<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Carrier Transicold — Registrar Asistencia</title>
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
      display: flex;
      flex-direction: column;
      align-items: center;
      padding: 1.25rem 1rem 3rem;
      color: #1a1a1a;
    }

    .ct-wrap { width: 100%; max-width: 420px; }

    /* ── Tabs ── */
    .ct-tabs {
      display: flex; gap: 6px;
      background: #eceae3;
      border: 0.5px solid #d8d5cc;
      border-radius: 12px;
      padding: 5px;
      margin-bottom: 1.25rem;
    }
    .ct-tab {
      flex: 1; padding: 9px 6px;
      font-size: 11px; font-weight: 500; line-height: 1.3;
      text-align: center;
      border-radius: 8px;
      border: none; background: transparent;
      color: #777; cursor: pointer;
      transition: all 0.15s;
      font-family: 'DM Sans', system-ui, sans-serif;
    }
    .ct-tab.active        { background: white; color: #1a1a1a; box-shadow: 0 1px 3px rgba(0,0,0,0.08); font-weight: 600; }
    .ct-tab.active-red    { background: #FCEBEB; color: #A32D2D; box-shadow: 0 1px 3px rgba(0,0,0,0.06); font-weight: 600; }

    /* ── Header ── */
    .ct-header {
      display: flex; align-items: center; gap: 12px;
      padding-bottom: 1rem;
      border-bottom: 0.5px solid #e0ddd5;
      margin-bottom: 1rem;
    }
    .ct-logo {
      width: 46px; height: 46px;
      background: #004B87;
      border-radius: 10px;
      display: flex; align-items: center; justify-content: center;
      flex-shrink: 0;
    }
    .ct-logo svg { width: 22px; height: 22px; stroke: white; fill: none; stroke-width: 2; stroke-linecap: round; stroke-linejoin: round; }
    .ct-title { font-size: 16px; font-weight: 600; color: #111; }
    .ct-sub   { font-size: 12px; color: #888; margin-top: 2px; }
    .ct-pill-online {
      margin-left: auto; flex-shrink: 0;
      display: flex; align-items: center; gap: 5px;
      padding: 5px 10px; border-radius: 999px;
      font-size: 11px; font-weight: 500;
      background: #EAF3DE; color: #3B6D11;
      border: 0.5px solid #C0DD97;
    }
    .ct-online-dot { width: 7px; height: 7px; border-radius: 50%; background: #639922; }

    /* ── Location tags ── */
    .ct-tags { display: flex; gap: 8px; margin-bottom: 1rem; flex-wrap: wrap; }
    .ct-tag {
      display: flex; align-items: center; gap: 5px;
      padding: 6px 10px; border-radius: 8px;
      font-size: 12px; font-weight: 500;
      border: 0.5px solid #ddd;
      background: white; color: #555;
    }
    .ct-tag i { font-size: 13px; }
    .ct-tag.gps-ok   { background: #EAF3DE; color: #3B6D11; border-color: #C0DD97; }
    .ct-tag.gps-warn { background: #FAEEDA; color: #854F0B; border-color: #FAC775; }
    .ct-tag.gps-bad  { background: #FCEBEB; color: #A32D2D; border-color: #F09595; }

    /* ── Cards ── */
    .ct-card {
      background: white;
      border: 0.5px solid #e0ddd5;
      border-radius: 14px;
      padding: 1rem 1.125rem;
      margin-bottom: 0.75rem;
    }
    .ct-section-label {
      font-size: 10px; font-weight: 600;
      letter-spacing: 0.08em; text-transform: uppercase;
      color: #aaa; margin-bottom: 12px;
    }

    /* ── Schedule ── */
    .ct-schedule {
      display: grid; grid-template-columns: 1fr 1fr;
      background: #F7F6F2;
      border: 0.5px solid #e8e5dd;
      border-radius: 10px; overflow: hidden;
      margin-bottom: 12px;
    }
    .ct-schedule-col { padding: 14px; text-align: center; }
    .ct-schedule-col:first-child { border-right: 0.5px solid #e8e5dd; }
    .ct-schedule-label { font-size: 10px; font-weight: 600; letter-spacing: 0.06em; text-transform: uppercase; color: #aaa; }
    .ct-schedule-time { font-family: 'DM Mono', monospace; font-size: 24px; font-weight: 500; color: #111; margin-top: 3px; }

    /* ── Alerts ── */
    .ct-alert {
      display: flex; align-items: center; gap: 8px;
      padding: 10px 12px; border-radius: 9px;
      font-size: 12px; font-weight: 500;
      margin-bottom: 12px; border: 0.5px solid;
    }
    .ct-alert i { font-size: 15px; flex-shrink: 0; }
    .ct-alert.warning { background: #FAEEDA; color: #854F0B; border-color: #FAC775; }
    .ct-alert.danger  { background: #FCEBEB; color: #A32D2D; border-color: #F09595; }
    .ct-alert.success { background: #EAF3DE; color: #3B6D11; border-color: #C0DD97; }

    /* ── Status row ── */
    .ct-status-row {
      display: flex; align-items: center; gap: 10px;
      padding: 12px;
      background: #F7F6F2;
      border: 0.5px dashed #ccc;
      border-radius: 10px; margin-bottom: 12px;
    }
    .ct-dot { width: 10px; height: 10px; border-radius: 50%; flex-shrink: 0; }
    .ct-dot.amber { background: #EF9F27; }
    .ct-dot.red   { background: #E24B4A; }
    .ct-dot.green { background: #639922; }
    .ct-status-label { font-size: 13px; font-weight: 500; color: #111; }
    .ct-status-sub   { font-size: 11px; color: #888; margin-top: 2px; }

    /* ── Buttons ── */
    .ct-btn-primary {
      width: 100%; padding: 13px;
      background: #004B87; color: white;
      border: none; border-radius: 10px;
      font-family: 'DM Sans', system-ui, sans-serif;
      font-size: 13px; font-weight: 600;
      cursor: pointer;
      display: flex; align-items: center; justify-content: center; gap: 8px;
      transition: background 0.15s;
    }
    .ct-btn-primary:hover   { background: #003d70; }
    .ct-btn-primary:active  { background: #002f56; }
    .ct-btn-primary i { font-size: 16px; }
    .ct-btn-secondary {
      width: 100%; padding: 12px;
      background: white; color: #444;
      border: 0.5px solid #ccc; border-radius: 10px;
      font-family: 'DM Sans', system-ui, sans-serif;
      font-size: 13px; font-weight: 500;
      cursor: pointer;
      display: flex; align-items: center; justify-content: center; gap: 8px;
      transition: background 0.15s;
    }
    .ct-btn-secondary:hover { background: #F7F6F2; }

    /* ── Record rows ── */
    .ct-record {
      display: flex; align-items: center; gap: 10px;
      padding: 10px 0;
    }
    .ct-record + .ct-record { border-top: 0.5px solid #f0ede5; }
    .ct-record-icon {
      width: 36px; height: 36px; border-radius: 50%;
      background: #F4F4F0;
      display: flex; align-items: center; justify-content: center;
      flex-shrink: 0;
    }
    .ct-record-icon i { font-size: 16px; color: #888; }
    .ct-record-title { font-size: 13px; font-weight: 500; color: #111; }
    .ct-record-dist  { font-size: 11px; color: #888; margin-top: 2px; display: flex; align-items: center; gap: 3px; }
    .ct-record-dist i { font-size: 11px; }
    .ct-record-right { text-align: right; margin-left: auto; }
    .ct-record-time  { font-family: 'DM Mono', monospace; font-size: 13px; font-weight: 500; color: #111; }
    .ct-badge {
      display: inline-block; font-size: 10px; font-weight: 600;
      padding: 3px 8px; border-radius: 6px; margin-top: 4px;
      border: 0.5px solid; letter-spacing: 0.02em;
    }
    .ct-badge.approved { background: #EAF3DE; color: #3B6D11; border-color: #C0DD97; }
    .ct-badge.rejected { background: #FCEBEB; color: #A32D2D; border-color: #F09595; }
    .ct-badge.pending  { background: #FAEEDA; color: #854F0B; border-color: #FAC775; }

    /* ── Info box ── */
    .ct-info-box {
      display: flex; gap: 10px; align-items: flex-start;
      padding: 12px;
      background: #FAEEDA20;
      border: 0.5px solid #FAC775;
      border-radius: 10px;
      margin-top: 0.75rem;
    }
    .ct-info-box i { font-size: 16px; color: #854F0B; flex-shrink: 0; margin-top: 1px; }
    .ct-info-title { font-size: 12px; font-weight: 600; color: #854F0B; margin-bottom: 4px; }
    .ct-info-body  { font-size: 11px; color: #854F0B; line-height: 1.6; }

    /* ── Empty state ── */
    .ct-empty { display: flex; flex-direction: column; align-items: center; padding: 1.75rem 0; gap: 8px; }
    .ct-empty i { font-size: 28px; color: #bbb; }
    .ct-empty p { font-size: 12px; color: #999; }

    /* ── Views ── */
    .ct-view { display: none; }
    .ct-view.active { display: block; }

    /* ── Modal ── */
    .ct-modal-overlay {
      display: none; position: fixed; inset: 0;
      background: rgba(10,17,32,0.6);
      backdrop-filter: blur(4px);
      z-index: 100;
      align-items: flex-end; justify-content: center;
      padding: 0;
    }
    .ct-modal-overlay.open { display: flex; }
    .ct-modal {
      background: white;
      border-radius: 20px 20px 0 0;
      width: 100%; max-width: 480px;
      overflow: hidden;
      animation: slideUp 0.25s ease-out;
    }
    @keyframes slideUp {
      from { transform: translateY(60px); opacity: 0; }
      to   { transform: translateY(0);    opacity: 1; }
    }
    .ct-modal-header {
      display: flex; align-items: center; justify-content: space-between;
      padding: 16px 18px 12px;
      border-bottom: 0.5px solid #f0ede5;
    }
    .ct-modal-title { font-size: 15px; font-weight: 600; color: #111; display: flex; align-items: center; gap: 7px; }
    .ct-modal-title i { font-size: 16px; color: #004B87; }
    .ct-modal-close {
      width: 28px; height: 28px; border-radius: 50%;
      background: #F4F4F0; border: 0.5px solid #ddd;
      display: flex; align-items: center; justify-content: center;
      cursor: pointer; color: #666; font-size: 13px;
      font-family: inherit;
    }
    .ct-modal-close:hover { background: #ebe9e2; }
    .ct-qr-area {
      background: #0A1521; margin: 14px 14px 0;
      border-radius: 12px; height: 200px;
      display: flex; flex-direction: column;
      align-items: center; justify-content: center;
      position: relative; overflow: hidden;
    }
    .ct-scan-line {
      position: absolute; left: 0; right: 0; height: 2px;
      background: linear-gradient(90deg, transparent, #00d4ff88, #00d4ff, #00d4ff88, transparent);
      animation: ctScan 2.2s ease-in-out infinite;
    }
    @keyframes ctScan {
      0%,100% { top: 18%; } 50% { top: 78%; }
    }
    .ct-corner-tl, .ct-corner-tr, .ct-corner-bl, .ct-corner-br {
      position: absolute; width: 20px; height: 20px;
      border-color: #00d4ff; border-style: solid;
    }
    .ct-corner-tl { top: 20px;  left: 20px;  border-width: 2.5px 0 0 2.5px; border-radius: 3px 0 0 0; }
    .ct-corner-tr { top: 20px;  right: 20px; border-width: 2.5px 2.5px 0 0; border-radius: 0 3px 0 0; }
    .ct-corner-bl { bottom: 20px; left: 20px;  border-width: 0 0 2.5px 2.5px; border-radius: 0 0 0 3px; }
    .ct-corner-br { bottom: 20px; right: 20px; border-width: 0 2.5px 2.5px 0; border-radius: 0 0 3px 0; }
    .ct-qr-icon { color: rgba(255,255,255,0.25); font-size: 40px; }
    .ct-qr-tip  { font-size: 11px; color: rgba(255,255,255,0.45); margin-top: 10px; }
    .ct-modal-footer { padding: 14px; display: flex; flex-direction: column; gap: 8px; }
    .ct-modal-hint { font-size: 11px; color: #999; text-align: center; padding: 0 8px; line-height: 1.6; }
  </style>
</head>
<body>
<div class="ct-wrap">

  <!-- Tabs de vista (solo para dev/preview) -->
  <div class="ct-tabs" role="tablist">
    <button class="ct-tab active" role="tab" aria-selected="true"  onclick="setTab('pendiente',this)">Pendiente<br>entrada</button>
    <button class="ct-tab"        role="tab" aria-selected="false" onclick="setTab('rechazado',this)">Rechazado</button>
    <button class="ct-tab"        role="tab" aria-selected="false" onclick="setTab('modal',this)">Modal QR</button>
  </div>

  <!-- Header -->
  <div class="ct-header">
    <div class="ct-logo" aria-hidden="true">
      <svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="9"/><polyline points="12,7 12,12 15,15"/></svg>
    </div>
    <div>
      <p class="ct-title">Registrar asistencia</p>
      <p class="ct-sub">Carrier Transicold &nbsp;·&nbsp; <span id="ct-fecha"></span></p>
    </div>
    <div class="ct-pill-online" aria-label="Conexión activa">
      <span class="ct-online-dot"></span> En línea
    </div>
  </div>

  <!-- Tags de ubicación/GPS -->
  <div class="ct-tags">
    <div class="ct-tag" id="ct-ubicacion-tag">
      <i class="ti ti-map-pin"></i>
      <span id="ct-ciudad">Tijuana</span> &nbsp;<span id="ct-hora-tag">--:--</span>
    </div>
    <div class="ct-tag gps-warn" id="ct-gps-tag">
      <i class="ti ti-satellite"></i>
      GPS <span id="ct-gps-precision">±90m</span>
    </div>
  </div>

  <!-- ══ Vista: PENDIENTE ══ -->
  <div class="ct-view active" id="view-pendiente" role="tabpanel">
    <div class="ct-card">
      <div class="ct-section-label">Tu horario de hoy</div>
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
      <div class="ct-alert warning" id="p-retardo-alert" style="display:none;" role="alert">
        <i class="ti ti-clock-exclamation"></i>
        Llegas con <strong id="p-retardo-min"></strong> min de retardo
      </div>
      <div class="ct-status-row">
        <div class="ct-dot amber"></div>
        <div>
          <div class="ct-status-label">Entrada pendiente</div>
          <div class="ct-status-sub">Hora actual: <span id="p-hora-actual">--:--</span></div>
        </div>
      </div>
      <button class="ct-btn-primary" onclick="abrirModalQR()">
        <i class="ti ti-qrcode"></i>
        Escanear QR y registrar entrada
      </button>
    </div>
    <div class="ct-card">
      <div class="ct-section-label">Registros de hoy</div>
      <div class="ct-empty" id="p-empty">
        <i class="ti ti-calendar-off"></i>
        <p>Sin registros por ahora</p>
      </div>
      <div id="p-registros-lista"></div>
    </div>
  </div>

  <!-- ══ Vista: RECHAZADO ══ -->
  <div class="ct-view" id="view-rechazado" role="tabpanel">
    <div class="ct-card">
      <div class="ct-section-label">Tu horario de hoy</div>
      <div class="ct-schedule">
        <div class="ct-schedule-col">
          <div class="ct-schedule-label">Entrada</div>
          <div class="ct-schedule-time" id="r-hora-entrada">--:--</div>
        </div>
        <div class="ct-schedule-col">
          <div class="ct-schedule-label">Salida</div>
          <div class="ct-schedule-time" id="r-hora-salida">--:--</div>
        </div>
      </div>
      <div class="ct-alert danger" role="alert">
        <i class="ti ti-map-pin-off"></i>
        Registro rechazado por geofencing
      </div>
      <div class="ct-status-row" style="border-color:#F09595;">
        <div class="ct-dot red"></div>
        <div>
          <div class="ct-status-label">Entrada rechazada</div>
          <div class="ct-status-sub" id="r-distancia-msg">Fuera del perímetro autorizado</div>
        </div>
      </div>
      <button class="ct-btn-primary" onclick="abrirModalQR()">
        <i class="ti ti-refresh"></i>
        Intentar de nuevo
      </button>
    </div>
    <div class="ct-card">
      <div class="ct-section-label">Registros de hoy</div>
      <div id="r-registros-lista"></div>
      <div class="ct-empty" id="r-empty" style="display:none;">
        <i class="ti ti-calendar-off"></i>
        <p>Sin registros</p>
      </div>
    </div>
    <div class="ct-info-box">
      <i class="ti ti-info-circle"></i>
      <div>
        <div class="ct-info-title">¿Por qué fue rechazado?</div>
        <div class="ct-info-body" id="r-info-body">
          Tu GPS reportó una distancia superior al radio permitido del punto fijo de la empresa.
          Verifica que estés físicamente en la sucursal y que el GPS tenga buena señal, luego intenta de nuevo.
        </div>
      </div>
    </div>
  </div>

  <!-- ══ Vista: MODAL QR (placeholder) ══ -->
  <div class="ct-view" id="view-modal" role="tabpanel">
    <div class="ct-card" style="text-align:center;padding:2rem;color:#aaa;font-size:12px;">
      <i class="ti ti-device-mobile" style="font-size:28px;display:block;margin-bottom:8px;"></i>
      El modal QR se abre sobre la pantalla.
    </div>
    <button class="ct-btn-primary" onclick="abrirModalQR()">
      <i class="ti ti-qrcode"></i>
      Abrir cámara de validación
    </button>
  </div>

</div><!-- /ct-wrap -->

<!-- ══ Modal QR ══ -->
<div class="ct-modal-overlay" id="ct-modal-overlay" role="dialog" aria-modal="true" aria-label="Escanear QR de asistencia">
  <div class="ct-modal">
    <div class="ct-modal-header">
      <div class="ct-modal-title">
        <i class="ti ti-qrcode"></i>
        Validación de asistencia
      </div>
      <button class="ct-modal-close" onclick="cerrarModalQR()" aria-label="Cerrar">
        <i class="ti ti-x"></i>
      </button>
    </div>

    <!-- Inputs ocultos para cámara nativa (más confiable en iOS) -->
    <input type="file" id="ct-input-foto"   accept="image/*" capture="environment" style="display:none" onchange="ct_onFotoSeleccionada(this)">
    <input type="file" id="ct-input-selfie" accept="image/*" capture="user"        style="display:none" onchange="ct_onSelfieSeleccionada(this)">

    <!-- PASO 1: Fotografiar el QR del administrador -->
    <div id="ct-paso1" style="padding:16px;">
      <div style="background:#0A1521;border-radius:12px;padding:28px 16px;text-align:center;margin-bottom:14px;">
        <div style="font-size:48px;margin-bottom:8px;">📷</div>
        <p style="color:rgba(255,255,255,0.8);font-size:13px;font-weight:500;">Toma una foto del QR del administrador</p>
        <p style="color:rgba(255,255,255,0.4);font-size:11px;margin-top:4px;">Apunta la cámara al código QR de la sucursal</p>
      </div>
      <div id="ct-qr-result" style="font-size:12px;color:#854F0B;background:#FAEEDA;border-radius:8px;padding:8px 12px;margin-bottom:10px;display:none;"></div>
      <button class="ct-btn-primary" onclick="ct_lanzarCamara()" style="margin-bottom:8px;">
        <i class="ti ti-qrcode"></i> Fotografiar QR
      </button>
      <button class="ct-btn-secondary" onclick="cerrarModalQR()">
        <i class="ti ti-x" style="font-size:14px;"></i> Cancelar
      </button>
    </div>

    <!-- PASO 2: Foto de confirmación (selfie) -->
    <div id="ct-paso2" style="padding:16px;display:none;">
      <div style="background:#EAF3DE;border:0.5px solid #C0DD97;border-radius:10px;padding:12px;margin-bottom:14px;display:flex;align-items:center;gap:8px;">
        <span style="font-size:18px;">✅</span>
        <div>
          <div style="font-size:12px;font-weight:600;color:#3B6D11;">QR escaneado</div>
          <div style="font-size:11px;color:#3B6D11;">Ahora toma una foto de confirmación</div>
        </div>
      </div>
      <div style="background:#0A1521;border-radius:12px;padding:28px 16px;text-align:center;margin-bottom:14px;">
        <div style="font-size:48px;margin-bottom:8px;">🤳</div>
        <p style="color:rgba(255,255,255,0.8);font-size:13px;font-weight:500;">Toma una selfie como evidencia</p>
        <p style="color:rgba(255,255,255,0.4);font-size:11px;margin-top:4px;">Esta foto queda registrada en el sistema</p>
      </div>
      <button class="ct-btn-primary" onclick="ct_lanzarFotoConfirmacion()" style="margin-bottom:8px;">
        <i class="ti ti-camera-selfie"></i> Tomar foto de confirmación
      </button>
      <button class="ct-btn-secondary" onclick="cerrarModalQR()">
        <i class="ti ti-x" style="font-size:14px;"></i> Cancelar
      </button>
    </div>

    <!-- PASO 3: Preview + confirmar -->
    <div id="ct-paso3" style="padding:16px;display:none;">
      <img id="ct-preview-img" style="width:100%;border-radius:12px;margin-bottom:12px;display:none;max-height:220px;object-fit:cover;" alt="Foto de confirmación">
      <div style="background:#F7F6F2;border-radius:10px;padding:12px;margin-bottom:14px;font-size:12px;color:#555;">
        <div style="display:flex;justify-content:space-between;padding:4px 0;border-bottom:0.5px solid #e8e5dd;">
          <span style="color:#aaa;font-weight:600;text-transform:uppercase;font-size:10px;">GPS</span>
          <span id="ct-paso3-gps" style="font-family:monospace;">Obteniendo...</span>
        </div>
        <div style="display:flex;justify-content:space-between;padding:4px 0;margin-top:4px;">
          <span style="color:#aaa;font-weight:600;text-transform:uppercase;font-size:10px;">Tipo</span>
          <span id="ct-paso3-tipo" style="font-family:monospace;">entrada</span>
        </div>
      </div>
      <button id="ct-btn-confirmar" class="ct-btn-primary" onclick="ct_confirmarRegistro()" style="margin-bottom:8px;">
        ✅ Confirmar entrada
      </button>
      <button class="ct-btn-secondary" onclick="cerrarModalQR()">
        <i class="ti ti-x" style="font-size:14px;"></i> Cancelar
      </button>
    </div>
  </div>
</div>

<script>
(function () {
  // ── Helpers de tiempo ──────────────────────────────────────────────────────
  function horaHHMM() {
    const n = new Date();
    return n.getHours().toString().padStart(2,'0') + ':' + n.getMinutes().toString().padStart(2,'0');
  }

  function fechaLegible() {
    return new Date().toLocaleDateString('es-MX', {
      weekday:'long', day:'numeric', month:'short', year:'numeric'
    });
  }

  // ── Calcular retardo en minutos ────────────────────────────────────────────
  function retardoMin(horaEntrada, horaActual) {
    if (!horaEntrada || !horaActual) return 0;
    const [eh, em] = horaEntrada.split(':').map(Number);
    const [ah, am] = horaActual.split(':').map(Number);
    return Math.max(0, (ah * 60 + am) - (eh * 60 + em));
  }

  // ── Pintar cabecera ────────────────────────────────────────────────────────
  const elFecha = document.getElementById('ct-fecha');
  if (elFecha) elFecha.textContent = fechaLegible();

  const elHoraTag = document.getElementById('ct-hora-tag');
  if (elHoraTag) elHoraTag.textContent = horaHHMM();
  setInterval(() => { if (elHoraTag) elHoraTag.textContent = horaHHMM(); }, 30000);

  // ── Cargar horario del día ─────────────────────────────────────────────────
  async function cargarHorario() {
    try {
      const hoy = new Date().toISOString().split('T')[0];
      const username = window.__ct_username || '';
      const res = await window.fetchAuth(
        '/api/horarios/hoy?username=' + encodeURIComponent(username) + '&fecha=' + hoy
      );
      const data = await res.json();
      const h = data && data.horario ? data.horario : null;

      const entrada = h ? (h.hora_entrada || '--:--') : '--:--';
      const salida  = h ? (h.hora_salida  || '--:--') : '--:--';

      ['p-hora-entrada','r-hora-entrada'].forEach(id => {
        const el = document.getElementById(id);
        if (el) el.textContent = entrada.slice(0,5);
      });
      ['p-hora-salida','r-hora-salida'].forEach(id => {
        const el = document.getElementById(id);
        if (el) el.textContent = salida.slice(0,5);
      });

      // Retardo
      const horaActual = horaHHMM();
      const elHoraActual = document.getElementById('p-hora-actual');
      if (elHoraActual) elHoraActual.textContent = horaActual;

      const mins = retardoMin(entrada.slice(0,5), horaActual);
      const alertRetardo = document.getElementById('p-retardo-alert');
      if (alertRetardo) {
        if (mins > 0) {
          alertRetardo.style.display = 'flex';
          const elMins = document.getElementById('p-retardo-min');
          if (elMins) elMins.textContent = mins;
        } else {
          alertRetardo.style.display = 'none';
        }
      }
    } catch (e) {
      console.warn('[ct-checkin] No se pudo cargar el horario:', e);
    }
  }

  // ── Cargar registros del día ───────────────────────────────────────────────
  async function cargarRegistros() {
    try {
      const hoy = new Date().toISOString().split('T')[0];
      const res  = await window.fetchAuth('/api/asistencia/registros?fecha=' + hoy);
      const data = await res.json();

      // Filtrar solo los del usuario actual
      const username = window.__ct_username || '';
      const registros = Array.isArray(data)
        ? data.filter(r => !username || r.username === username)
        : [];

      renderRegistros('p-registros-lista', 'p-empty', registros);
      renderRegistros('r-registros-lista', 'r-empty',  registros.filter(r => !r.aprobado));

      // Actualizar mensaje de distancia en vista rechazado
      const rechazados = registros.filter(r => !r.aprobado);
      if (rechazados.length) {
        const ultimo = rechazados[rechazados.length - 1];
        const dist   = ultimo.distancia_metros ? Math.round(ultimo.distancia_metros).toLocaleString('es-MX') : '?';
        const radio  = window.__ct_radio || 200;
        const elMsg  = document.getElementById('r-distancia-msg');
        if (elMsg) elMsg.textContent = 'Fuera del perímetro (' + dist + ' m · límite ' + radio + ' m)';
        const elInfo = document.getElementById('r-info-body');
        if (elInfo) {
          elInfo.textContent =
            'Tu GPS reportó ' + dist + ' m de distancia al punto fijo, superando el radio permitido de ' +
            radio + ' m. Verifica que estés físicamente en la sucursal y que el GPS tenga buena señal, luego intenta de nuevo.';
        }
      }
    } catch (e) {
      console.warn('[ct-checkin] No se pudieron cargar registros:', e);
    }
  }

  function renderRegistros(listaId, emptyId, registros) {
    const lista = document.getElementById(listaId);
    const empty = document.getElementById(emptyId);
    if (!lista) return;

    if (!registros.length) {
      lista.innerHTML = '';
      if (empty) empty.style.display = 'flex';
      return;
    }
    if (empty) empty.style.display = 'none';

    lista.innerHTML = registros.map(r => {
      const tipo      = r.tipo === 'salida' ? 'Salida' : 'Entrada';
      const icon      = r.tipo === 'salida' ? 'ti-logout' : 'ti-login';
      const dist      = r.distancia_metros ? Math.round(r.distancia_metros).toLocaleString('es-MX') + ' m del punto fijo' : '';
      const hora      = (r.hora_checkin || r.hora || '').slice(0,5);
      const badgeClass = r.aprobado ? 'approved' : 'rejected';
      const badgeText  = r.aprobado ? 'Aprobado'  : 'Rechazado';
      return '<div class="ct-record">' +
        '<div class="ct-record-icon"><i class="ti ' + icon + '"></i></div>' +
        '<div><div class="ct-record-title">' + tipo + '</div>' +
        (dist ? '<div class="ct-record-dist"><i class="ti ti-map-pin"></i>' + dist + '</div>' : '') +
        '</div>' +
        '<div class="ct-record-right">' +
          '<div class="ct-record-time">' + hora + '</div>' +
          '<span class="ct-badge ' + badgeClass + '">' + badgeText + '</span>' +
        '</div></div>';
    }).join('');
  }

  // ── GPS precision tag ──────────────────────────────────────────────────────
  function actualizarGPSTag(accuracy) {
    const tag = document.getElementById('ct-gps-tag');
    const el  = document.getElementById('ct-gps-precision');
    if (!tag || !el) return;
    el.textContent = '±' + Math.round(accuracy) + 'm';
    tag.className = 'ct-tag ' + (accuracy <= 50 ? 'gps-ok' : accuracy <= 100 ? 'gps-warn' : 'gps-bad');
  }

  if (navigator.geolocation) {
    navigator.geolocation.getCurrentPosition(
      pos => actualizarGPSTag(pos.coords.accuracy),
      ()  => {},
      { enableHighAccuracy: true, timeout: 8000 }
    );
  }

  // ── Modal QR ───────────────────────────────────────────────────────────────
  window.abrirModalQR  = function () { document.getElementById('ct-modal-overlay').classList.add('open'); };
  window.cerrarModalQR = function () { document.getElementById('ct-modal-overlay').classList.remove('open'); };

  // ── Tabs ───────────────────────────────────────────────────────────────────
  window.setTab = function (id, el) {
    document.querySelectorAll('.ct-view').forEach(v => v.classList.remove('active'));
    document.querySelectorAll('.ct-tab').forEach(t => {
      t.classList.remove('active','active-red');
      t.setAttribute('aria-selected','false');
    });
    const view = document.getElementById('view-' + id);
    if (view) view.classList.add('active');
    el.classList.add(id === 'rechazado' ? 'active-red' : 'active');
    el.setAttribute('aria-selected','true');
    if (id === 'modal') { abrirModalQR(); }
    else { cerrarModalQR(); }
  };

  // ── Init ───────────────────────────────────────────────────────────────────
  // La carga se dispara desde el init_script via DOMContentLoaded
  // para garantizar que window.__ct_username esté disponible primero.

})();
</script>
</body>
</html>"""
