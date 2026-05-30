"""
templates.py — Módulo de plantillas de asistencia
Flujo profesional: GPS → Selfie → Registro
"""

ASISTENCIA_STYLES = """
<style>
.asistencia-container { max-width: 520px; margin: 0 auto; }
.checkin-card {
    background: white;
    border-radius: 20px;
    padding: 28px 24px;
    box-shadow: 0 8px 32px rgba(0,43,91,0.12);
    margin-bottom: 20px;
    border: 1px solid #e2e8f0;
}
.checkin-status-bar {
    display: flex;
    align-items: center;
    gap: 12px;
    background: var(--color-bg, #f0f6ff);
    border-radius: 12px;
    padding: 14px 18px;
    margin-bottom: 20px;
    border-left: 5px solid var(--color-accent, #0057A8);
}
.status-dot {
    width: 12px; height: 12px; border-radius: 50%;
    background: #6b7280; flex-shrink: 0;
    box-shadow: 0 0 0 3px rgba(107,114,128,0.2);
}
.status-dot.green  { background: #16a34a; box-shadow: 0 0 0 3px rgba(22,163,74,0.2); }
.status-dot.orange { background: #d97706; box-shadow: 0 0 0 3px rgba(217,119,6,0.2); }
.status-dot.red    { background: #dc2626; box-shadow: 0 0 0 3px rgba(220,38,38,0.2); }
.schedule-info {
    background: #f8fafc;
    border-radius: 12px;
    padding: 14px 18px;
    margin-bottom: 20px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    border: 1px solid #e2e8f0;
}
.schedule-time { text-align: center; flex: 1; }
.schedule-time .label { font-size: 0.7rem; color: #6b7280; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; }
.schedule-time .time  { font-size: 1.4rem; font-weight: 800; color: #002B5B; line-height: 1.2; }
.schedule-divider { width: 1px; height: 40px; background: #e2e8f0; margin: 0 16px; }
.btn-checkin {
    width: 100%; padding: 18px; border: none; border-radius: 14px;
    font-size: 1.05rem; font-weight: 700; cursor: pointer;
    transition: transform 0.15s, box-shadow 0.15s;
    display: flex; align-items: center; justify-content: center; gap: 10px;
    letter-spacing: 0.3px;
}
.btn-checkin:active { transform: scale(0.97); }
.btn-entrada { background: linear-gradient(135deg, #002B5B 0%, #0057A8 100%); color: white; box-shadow: 0 4px 16px rgba(0,87,168,0.35); }
.btn-salida  { background: linear-gradient(135deg, #064e3b 0%, #16a34a 100%); color: white; box-shadow: 0 4px 16px rgba(22,163,74,0.35); }
.btn-disabled { background: #e5e7eb; color: #9ca3af; cursor: not-allowed; box-shadow: none; }
.btn-checkin:not(.btn-disabled):hover { transform: translateY(-2px); box-shadow: 0 8px 24px rgba(0,0,0,0.2); }
.registro-item {
    display: flex; justify-content: space-between; align-items: center;
    padding: 12px 0; border-bottom: 1px solid #f1f5f9;
}
.registro-item:last-child { border-bottom: none; }
.gps-bar {
    display: flex; align-items: center; gap: 8px;
    font-size: 0.8rem; color: #6b7280; margin-bottom: 16px;
    background: #fafafa; border-radius: 8px; padding: 8px 12px;
    border: 1px solid #f0f0f0;
}
.gps-dot { width: 8px; height: 8px; border-radius: 50%; background: #d97706; flex-shrink: 0; }
.gps-dot.ok { background: #16a34a; }
.alert-box {
    border-radius: 12px; padding: 14px 18px; margin-bottom: 16px;
    font-size: 0.875rem; font-weight: 500; display: flex; align-items: flex-start; gap: 10px;
}
.alert-warning { background: #fffbeb; border: 1px solid #fcd34d; color: #92400e; border-left: 4px solid #f59e0b; }
.alert-success { background: #f0fdf4; border: 1px solid #86efac; color: #166534; border-left: 4px solid #16a34a; }
.alert-error   { background: #fef2f2; border: 1px solid #fca5a5; color: #991b1b; border-left: 4px solid #dc2626; }
.alert-info    { background: #eff6ff; border: 1px solid #bfdbfe; color: #1e40af; border-left: 4px solid #3b82f6; }
.progress-track { height: 6px; background: #e5e7eb; border-radius: 99px; margin: 12px 0; overflow: hidden; }
.progress-fill  { height: 100%; border-radius: 99px; background: linear-gradient(90deg, #0057A8, #16a34a); transition: width 0.6s ease; }

/* ── MODAL SELFIE ── */
.selfie-overlay {
    position: fixed; top: 0; left: 0; width: 100%; height: 100%;
    background: rgba(0,0,0,0.92); z-index: 1000;
    display: flex; flex-direction: column; align-items: center; justify-content: center;
    padding: 16px;
}
.selfie-header {
    color: white; text-align: center; margin-bottom: 16px;
}
.selfie-header h2 { font-size: 1.2rem; font-weight: 700; margin: 0 0 4px; }
.selfie-header p  { font-size: 0.82rem; color: #94a3b8; margin: 0; }
.selfie-video-wrap {
    position: relative; width: 100%; max-width: 360px;
    border-radius: 20px; overflow: hidden;
    border: 3px solid #0057A8;
    box-shadow: 0 0 0 6px rgba(0,87,168,0.25);
}
#selfieVideo {
    width: 100%; display: block;
    transform: scaleX(-1); /* espejo natural */
    background: #000;
}
.selfie-guide {
    position: absolute; top: 50%; left: 50%; transform: translate(-50%,-50%);
    width: 170px; height: 210px;
    border: 2.5px dashed rgba(255,255,255,0.55);
    border-radius: 50% 50% 50% 50% / 42% 42% 58% 58%;
    pointer-events: none;
}
.selfie-actions {
    display: flex; gap: 14px; margin-top: 20px; width: 100%; max-width: 360px;
}
.btn-capture {
    flex: 1; padding: 16px; border: none; border-radius: 14px;
    font-size: 1rem; font-weight: 700; cursor: pointer;
    background: linear-gradient(135deg, #002B5B, #0057A8); color: white;
    box-shadow: 0 4px 14px rgba(0,87,168,0.4);
    transition: transform 0.15s;
}
.btn-capture:active { transform: scale(0.97); }
.btn-cancel-selfie {
    padding: 16px 20px; border: 1.5px solid rgba(255,255,255,0.25);
    border-radius: 14px; font-size: 0.9rem; font-weight: 600;
    cursor: pointer; background: transparent; color: white;
    transition: background 0.2s;
}
.btn-cancel-selfie:hover { background: rgba(255,255,255,0.08); }

/* Preview selfie capturada */
.selfie-preview-wrap {
    position: relative; width: 100%; max-width: 360px;
    border-radius: 20px; overflow: hidden;
    border: 3px solid #16a34a;
    box-shadow: 0 0 0 6px rgba(22,163,74,0.2);
    margin-top: 0;
}
#selfiePreview {
    width: 100%; display: block;
    transform: scaleX(-1);
}
.selfie-preview-badge {
    position: absolute; bottom: 10px; left: 50%; transform: translateX(-50%);
    background: rgba(22,163,74,0.92); color: white; padding: 5px 14px;
    border-radius: 20px; font-size: 0.78rem; font-weight: 600;
    white-space: nowrap;
}
.selfie-retake-bar {
    display: flex; gap: 12px; margin-top: 14px; width: 100%; max-width: 360px;
}
.btn-retake {
    flex: 1; padding: 13px; border: 1.5px solid rgba(255,255,255,0.3);
    border-radius: 12px; font-size: 0.9rem; font-weight: 600;
    cursor: pointer; background: transparent; color: white;
}
.btn-confirm-selfie {
    flex: 2; padding: 13px; border: none; border-radius: 12px;
    font-size: 1rem; font-weight: 700; cursor: pointer;
    background: linear-gradient(135deg, #064e3b, #16a34a); color: white;
    box-shadow: 0 4px 12px rgba(22,163,74,0.35);
}

/* Miniatura de selfie en registro */
.selfie-thumb {
    width: 44px; height: 44px; border-radius: 50%;
    object-fit: cover; border: 2px solid #e2e8f0;
    transform: scaleX(-1);
}
</style>
"""


def get_checkin_template() -> str:
    return """
<div class="asistencia-container">

    <!-- GPS Status -->
    <div class="gps-bar" id="gpsBar">
        <span class="gps-dot" id="gpsDot"></span>
        <span id="gpsText">Obteniendo ubicación GPS...</span>
    </div>

    <!-- Horario del día -->
    <div class="checkin-card" id="cardHorario" style="display:none;">
        <div style="font-size:0.7rem; font-weight:700; color:#6b7280; text-transform:uppercase; letter-spacing:0.5px; margin-bottom:10px;">Tu horario de hoy</div>
        <div class="schedule-info" id="scheduleInfo">
            <div class="schedule-time">
                <div class="label">Entrada</div>
                <div class="time" id="schedEntrada">--:--</div>
            </div>
            <div class="schedule-divider"></div>
            <div class="schedule-time">
                <div class="label">Salida</div>
                <div class="time" id="schedSalida">--:--</div>
            </div>
        </div>
        <div id="alertHorario"></div>
    </div>

    <!-- Estado actual -->
    <div class="checkin-card">
        <div class="checkin-status-bar" id="statusBar">
            <span class="status-dot" id="statusDot"></span>
            <div>
                <div style="font-weight:700; font-size:0.9rem; color:#002B5B;" id="statusTitle">Cargando...</div>
                <div style="font-size:0.78rem; color:#6b7280;" id="statusSub"></div>
            </div>
        </div>

        <!-- Barra de progreso jornada -->
        <div id="progressSection" style="display:none; margin-bottom:16px;">
            <div style="display:flex; justify-content:space-between; font-size:0.75rem; color:#6b7280; margin-bottom:4px;">
                <span>Jornada laboral</span>
                <span id="progressLabel">0%</span>
            </div>
            <div class="progress-track"><div class="progress-fill" id="progressFill" style="width:0%"></div></div>
        </div>

        <!-- Botón principal -->
        <div id="alertMsg"></div>
        <button class="btn-checkin btn-disabled" id="btnAccion" disabled>
            <span id="btnIcon">⏳</span>
            <span id="btnLabel">Cargando...</span>
        </button>
    </div>

    <!-- Registros de hoy -->
    <div class="checkin-card" id="cardRegistros" style="display:none;">
        <div style="font-size:0.7rem; font-weight:700; color:#6b7280; text-transform:uppercase; letter-spacing:0.5px; margin-bottom:14px;">Registros de hoy</div>
        <div id="listaRegistros"></div>
    </div>

</div>

<!-- ══════════ MODAL CÁMARA SELFIE ══════════ -->
<div class="selfie-overlay" id="selfieModal" style="display:none;">

    <!-- Vista cámara -->
    <div id="selfieCaptura">
        <div class="selfie-header">
            <h2 id="selfieModalTitle">📸 Selfie de Entrada</h2>
            <p>Coloca tu rostro dentro del óvalo y presiona capturar</p>
        </div>
        <div class="selfie-video-wrap">
            <video id="selfieVideo" autoplay playsinline muted></video>
            <div class="selfie-guide"></div>
        </div>
        <div class="selfie-actions">
            <button class="btn-cancel-selfie" onclick="cancelarSelfie()">✕ Cancelar</button>
            <button class="btn-capture" onclick="capturarFoto()">📸 Capturar</button>
        </div>
    </div>

    <!-- Preview de foto capturada -->
    <div id="selfiePreviewSection" style="display:none;">
        <div class="selfie-header">
            <h2>✅ Foto capturada</h2>
            <p>¿Deseas usar esta foto o repetir?</p>
        </div>
        <div class="selfie-preview-wrap">
            <img id="selfiePreview" src="" alt="Selfie">
            <div class="selfie-preview-badge">📸 Selfie lista</div>
        </div>
        <div class="selfie-retake-bar">
            <button class="btn-retake" onclick="repetirSelfie()">🔄 Repetir</button>
            <button class="btn-confirm-selfie" onclick="confirmarSelfie()">✅ Usar esta foto</button>
        </div>
    </div>

</div>

<canvas id="selfieCanvas" style="display:none;"></canvas>

<script>
const fetchAuth = window.fetchAuth;
const username  = window.username;

// ── Estado local ───────────────────────────────────────────
let gpsCoords     = null;
let horarioHoy    = null;
let estadoHoy     = null;
let accionActual  = null;
let _ejecutando   = false;
let selfieBlob    = null;   // foto capturada lista para subir
let selfieStream  = null;   // stream de cámara activo
let accionPendiente = null; // 'entrada' | 'salida' — guardada mientras toma selfie

// ── Helpers ────────────────────────────────────────────────
function horaActualTJ() {
    return new Date().toLocaleTimeString('es-MX', {
        timeZone: 'America/Tijuana', hour12: false, hour: '2-digit', minute: '2-digit'
    });
}
function fechaHoyTJ() {
    return new Date().toLocaleDateString('sv-SE', { timeZone: 'America/Tijuana' });
}
function minutosDesdeMedianoche(hhmm) {
    if (!hhmm) return null;
    const [h, m] = hhmm.split(':').map(Number);
    return h * 60 + m;
}
function formatHora(hhmm) {
    if (!hhmm) return '—';
    return hhmm.slice(0, 5);
}

// ── 1. GPS ─────────────────────────────────────────────────
function obtenerGPS() {
    if (!navigator.geolocation) {
        setGPSStatus(false, 'GPS no soportado en este dispositivo');
        inicializarPagina();
        return;
    }
    navigator.geolocation.getCurrentPosition(
        pos => {
            gpsCoords = { lat: pos.coords.latitude, lon: pos.coords.longitude, precision: pos.coords.accuracy };
            const prec = pos.coords.accuracy.toFixed(0);
            const ok   = pos.coords.accuracy <= 200;
            setGPSStatus(ok, ok ? `GPS preciso (±${prec}m)` : `GPS poco preciso (±${prec}m) — Acércate a una ventana`);
            inicializarPagina();
        },
        () => {
            setGPSStatus(false, 'GPS denegado — Activa el permiso de ubicación');
            inicializarPagina();
        },
        { enableHighAccuracy: true, timeout: 15000, maximumAge: 0 }
    );
}
function setGPSStatus(ok, msg) {
    document.getElementById('gpsDot').className = 'gps-dot' + (ok ? ' ok' : '');
    document.getElementById('gpsText').textContent = (ok ? '✓ ' : '⚠ ') + msg;
}

// ── 2. Cargar horario y estado ─────────────────────────────
async function inicializarPagina() {
    await Promise.all([cargarHorarioHoy(), cargarEstadoHoy()]);
    determinarAccion();
    renderUI();
}
async function cargarHorarioHoy() {
    try {
        const res = await fetchAuth(`/api/horarios/hoy?username=${username}&fecha=${fechaHoyTJ()}`);
        if (res && res.ok) { const d = await res.json(); horarioHoy = d.horario || null; }
    } catch(e) { horarioHoy = null; }
}
async function cargarEstadoHoy() {
    try {
        const res = await fetchAuth(`/api/asistencia/estado-hoy?username=${username}&fecha=${fechaHoyTJ()}`);
        if (res && res.ok) { estadoHoy = await res.json(); }
    } catch(e) { estadoHoy = null; }
}

// ── 3. Determinar acción ──────────────────────────────────
function determinarAccion() {
    if (!horarioHoy || (!horarioHoy.hora_entrada && !horarioHoy.hora_salida)) { accionActual = 'sin_horario'; return; }
    const tieneEntrada = estadoHoy?.tiene_entrada;
    const tieneSalida  = estadoHoy?.tiene_salida;
    if (tieneEntrada && tieneSalida)       accionActual = 'completo';
    else if (tieneEntrada && !tieneSalida) accionActual = 'salida';
    else                                   accionActual = 'entrada';
}

// ── 4. Render UI ───────────────────────────────────────────
function renderUI() {
    if (horarioHoy) {
        document.getElementById('cardHorario').style.display = 'block';
        document.getElementById('schedEntrada').textContent = formatHora(horarioHoy.hora_entrada) || 'Libre';
        document.getElementById('schedSalida').textContent  = formatHora(horarioHoy.hora_salida)  || 'Libre';

        if (accionActual === 'entrada' && horarioHoy.hora_entrada) {
            const diff = minutosDesdeMedianoche(horaActualTJ()) - minutosDesdeMedianoche(horarioHoy.hora_entrada);
            if (diff > 15) document.getElementById('alertHorario').innerHTML =
                `<div class="alert-box alert-warning">⏱ Llegas con <b>${diff} min de retardo</b> sobre tu horario de entrada.</div>`;
        }

        if (accionActual === 'salida' && horarioHoy.hora_entrada && horarioHoy.hora_salida) {
            const ahoraMin   = minutosDesdeMedianoche(horaActualTJ());
            const entradaMin = minutosDesdeMedianoche(horarioHoy.hora_entrada);
            const salidaMin  = minutosDesdeMedianoche(horarioHoy.hora_salida);
            const jornada    = salidaMin - entradaMin;
            if (jornada > 0) {
                const pct = Math.min(100, Math.round((Math.max(0, ahoraMin - entradaMin) / jornada) * 100));
                document.getElementById('progressSection').style.display = 'block';
                document.getElementById('progressFill').style.width = pct + '%';
                document.getElementById('progressLabel').textContent = pct + '% de la jornada';
            }
        }
    }

    const btn      = document.getElementById('btnAccion');
    const btnIcon  = document.getElementById('btnIcon');
    const btnLabel = document.getElementById('btnLabel');
    const alertMsg = document.getElementById('alertMsg');

    // NUEVO: el botón ahora abre la cámara para selfie
    btn.onclick = abrirSelfieModal;

    switch (accionActual) {
        case 'sin_horario':
            document.getElementById('statusDot').className   = 'status-dot orange';
            document.getElementById('statusTitle').textContent = 'Sin horario asignado hoy';
            document.getElementById('statusSub').textContent   = 'Comunícate con el administrador';
            alertMsg.innerHTML = '<div class="alert-box alert-warning">No tienes horario registrado para hoy.</div>';
            btn.className = 'btn-checkin btn-disabled'; btn.disabled = true;
            btnIcon.textContent = '🚫'; btnLabel.textContent = 'Sin horario para hoy';
            break;

        case 'entrada':
            document.getElementById('statusDot').className    = 'status-dot orange';
            document.getElementById('statusTitle').textContent = 'Pendiente de entrada';
            document.getElementById('statusSub').textContent   = `Hora actual: ${horaActualTJ()}`;
            btn.className = 'btn-checkin btn-entrada'; btn.disabled = false;
            btnIcon.textContent = '📸'; btnLabel.textContent = 'Tomar Selfie y Registrar Entrada';
            break;

        case 'salida': {
            document.getElementById('statusDot').className    = 'status-dot green';
            document.getElementById('statusTitle').textContent = `Entrada registrada a las ${formatHora(estadoHoy.hora_entrada_real)}`;
            document.getElementById('statusSub').textContent   = `Hora actual: ${horaActualTJ()}`;

            let puedeRegistrarSalida = true;
            if (horarioHoy?.hora_entrada && horarioHoy?.hora_salida) {
                const ahoraMin     = minutosDesdeMedianoche(horaActualTJ());
                const entradaMin   = minutosDesdeMedianoche(horarioHoy.hora_entrada);
                const salidaMin    = minutosDesdeMedianoche(horarioHoy.hora_salida);
                const mitad = entradaMin + Math.floor((salidaMin - entradaMin) * 0.5);
                if (ahoraMin < mitad) {
                    puedeRegistrarSalida = false;
                    alertMsg.innerHTML = `<div class="alert-box alert-info">⏰ Podrás registrar salida en <b>${mitad - ahoraMin} minutos</b> (al 50% de tu jornada).</div>`;
                }
            }

            if (!puedeRegistrarSalida) {
                btn.className = 'btn-checkin btn-disabled'; btn.disabled = true;
                btnIcon.textContent = '🔒'; btnLabel.textContent = 'Salida no disponible aún';
            } else {
                btn.className = 'btn-checkin btn-salida'; btn.disabled = false;
                btnIcon.textContent = '📸'; btnLabel.textContent = 'Tomar Selfie y Registrar Salida';
            }
            break;
        }

        case 'completo':
            document.getElementById('statusDot').className    = 'status-dot green';
            document.getElementById('statusTitle').textContent = '✅ Jornada completada';
            document.getElementById('statusSub').textContent   = `Entrada: ${formatHora(estadoHoy.hora_entrada_real)} · Salida: ${formatHora(estadoHoy.hora_salida_real)}`;
            alertMsg.innerHTML = '<div class="alert-box alert-success">🎉 Has completado tu registro del día. ¡Hasta mañana!</div>';
            btn.className = 'btn-checkin btn-disabled'; btn.disabled = true;
            btnIcon.textContent = '✅'; btnLabel.textContent = 'Jornada completada';
            break;
    }
    cargarRegistrosUI();
}

// ── 5. Registros de hoy ────────────────────────────────────
async function cargarRegistrosUI() {
    try {
        const res = await fetchAuth(`/api/asistencia/registros?fecha=${fechaHoyTJ()}&username=${username}`);
        if (!res || !res.ok) return;
        const registros = await res.json();
        if (!Array.isArray(registros) || !registros.length) return;
        let html = '';
        registros.forEach(r => {
            const tipo   = r.tipo === 'entrada' ? '🟢 Entrada' : '🔴 Salida';
            const estado = r.aprobado
                ? '<span style="color:#16a34a;font-size:0.78rem;">✓ Aprobado</span>'
                : '<span style="color:#dc2626;font-size:0.78rem;">✗ Rechazado</span>';
            const dist   = r.distancia_metros != null ? `${Math.round(r.distancia_metros)}m` : 'Sin GPS';
            const foto   = r.selfie_url
                ? `<img src="${r.selfie_url}" class="selfie-thumb" alt="selfie">`
                : '<div style="width:44px;height:44px;border-radius:50%;background:#f1f5f9;display:flex;align-items:center;justify-content:center;font-size:1.2rem;">👤</div>';
            html += `<div class="registro-item">
                <div style="display:flex;align-items:center;gap:12px;">
                    ${foto}
                    <div>
                        <div style="font-weight:600;font-size:0.88rem;">${tipo}</div>
                        <div style="font-size:0.75rem;color:#6b7280;">📍 ${dist}</div>
                    </div>
                </div>
                <div style="text-align:right;">
                    <div style="font-weight:700;font-size:0.95rem;color:#002B5B;">${formatHora(r.hora_checkin)}</div>
                    <div>${estado}</div>
                </div>
            </div>`;
        });
        document.getElementById('listaRegistros').innerHTML = html;
        document.getElementById('cardRegistros').style.display = 'block';
    } catch(e) {}
}

// ══════════ FLUJO SELFIE ══════════

async function abrirSelfieModal() {
    if (accionActual !== 'entrada' && accionActual !== 'salida') return;
    accionPendiente = accionActual;
    selfieBlob = null;

    // Resetear modal
    document.getElementById('selfieCaptura').style.display = 'block';
    document.getElementById('selfiePreviewSection').style.display = 'none';
    document.getElementById('selfieModalTitle').textContent =
        accionActual === 'entrada' ? '📸 Selfie de Entrada' : '📸 Selfie de Salida';
    document.getElementById('selfieModal').style.display = 'flex';

    // Iniciar cámara frontal
    try {
        selfieStream = await navigator.mediaDevices.getUserMedia({
            video: { facingMode: 'user', width: { ideal: 640 }, height: { ideal: 480 } },
            audio: false
        });
        document.getElementById('selfieVideo').srcObject = selfieStream;
    } catch(err) {
        cancelarSelfie();
        document.getElementById('alertMsg').innerHTML =
            '<div class="alert-box alert-error">❌ No se pudo acceder a la cámara. Verifica los permisos.</div>';
    }
}

function capturarFoto() {
    const video  = document.getElementById('selfieVideo');
    const canvas = document.getElementById('selfieCanvas');
    canvas.width  = video.videoWidth  || 640;
    canvas.height = video.videoHeight || 480;
    const ctx = canvas.getContext('2d');
    // Capturar espejo (igual que se ve en pantalla)
    ctx.translate(canvas.width, 0);
    ctx.scale(-1, 1);
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
    ctx.setTransform(1,0,0,1,0,0);

    // Mostrar preview
    const dataUrl = canvas.toDataURL('image/jpeg', 0.85);
    document.getElementById('selfiePreview').src = dataUrl;
    document.getElementById('selfieCaptura').style.display = 'none';
    document.getElementById('selfiePreviewSection').style.display = 'block';
}

function repetirSelfie() {
    document.getElementById('selfieCaptura').style.display = 'block';
    document.getElementById('selfiePreviewSection').style.display = 'none';
}

function confirmarSelfie() {
    // Convertir canvas a Blob
    const canvas = document.getElementById('selfieCanvas');
    canvas.toBlob(blob => {
        selfieBlob = blob;
        cerrarCamara();
        document.getElementById('selfieModal').style.display = 'none';
        ejecutarAccion();
    }, 'image/jpeg', 0.85);
}

function cancelarSelfie() {
    cerrarCamara();
    document.getElementById('selfieModal').style.display = 'none';
    selfieBlob = null;
    accionPendiente = null;
}

function cerrarCamara() {
    if (selfieStream) {
        selfieStream.getTracks().forEach(t => t.stop());
        selfieStream = null;
    }
    const video = document.getElementById('selfieVideo');
    if (video) video.srcObject = null;
}

// ── 6. Ejecutar registro con selfie ────────────────────────
async function ejecutarAccion() {
    if (!accionPendiente || !selfieBlob) return;
    if (_ejecutando) return;
    _ejecutando = true;

    const btn      = document.getElementById('btnAccion');
    const btnIcon  = document.getElementById('btnIcon');
    const btnLabel = document.getElementById('btnLabel');
    const alertMsg = document.getElementById('alertMsg');

    const labelOriginal = accionPendiente === 'entrada' ? 'Tomar Selfie y Registrar Entrada' : 'Tomar Selfie y Registrar Salida';
    const iconOriginal  = '📸';
    const claseOriginal = accionPendiente === 'entrada' ? 'btn-checkin btn-entrada' : 'btn-checkin btn-salida';

    btn.disabled = true; btn.className = 'btn-checkin btn-disabled';
    btnIcon.textContent = '⏳'; btnLabel.textContent = 'Registrando...';
    alertMsg.innerHTML = '';

    try {
        // ── Subir selfie primero ──
        const formData = new FormData();
        formData.append('file', selfieBlob, `selfie_${username}_${fechaHoyTJ()}_${accionPendiente}.jpg`);
        formData.append('username', username);
        formData.append('tipo', accionPendiente);
        formData.append('fecha', fechaHoyTJ());

        let selfieUrl = null;
        const uploadRes = await fetchAuth('/api/asistencia/selfie', {
            method: 'POST',
            body: formData
        });
        if (uploadRes && uploadRes.ok) {
            const uploadData = await uploadRes.json();
            selfieUrl = uploadData.url || null;
        }

        // ── Luego registrar checkin ──
        const payload = {
            username:      username,
            tipo:          accionPendiente,
            fecha:         fechaHoyTJ(),
            lat:           gpsCoords?.lat       ?? null,
            lon:           gpsCoords?.lon       ?? null,
            precision_gps: gpsCoords?.precision ?? null,
            selfie_url:    selfieUrl,
        };

        const res = await fetchAuth('/api/asistencia/checkin', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload),
        });

        if (!res) { _ejecutando = false; return; }

        let data = {};
        try { data = await res.json(); } catch(_) { data = { detail: 'Respuesta inválida del servidor.' }; }

        if (res.ok) {
            const tipoLabel = accionPendiente === 'entrada' ? 'Entrada' : 'Salida';
            const extra = accionPendiente === 'entrada'
                ? (data.retardo_min > 0 ? ` · Retardo: ${data.retardo_min} min` : '')
                : (data.horas_trabajadas ? ` · ${data.horas_trabajadas}h trabajadas` : '');
            alertMsg.innerHTML = `<div class="alert-box alert-success">✅ ${tipoLabel} registrada a las <b>${formatHora(data.hora_registro)}</b>${extra}</div>`;
            selfieBlob = null;
            accionPendiente = null;
            await cargarEstadoHoy();
            determinarAccion();
            renderUI();
        } else {
            const msg = data.detail || `Error ${res.status}. Intenta de nuevo.`;
            alertMsg.innerHTML = `<div class="alert-box alert-error">❌ ${msg}</div>`;
            btn.disabled = false; btn.className = claseOriginal;
            btnIcon.textContent = iconOriginal; btnLabel.textContent = labelOriginal;
        }

    } catch(err) {
        alertMsg.innerHTML = '<div class="alert-box alert-error">❌ Sin conexión. Revisa tu internet e intenta de nuevo.</div>';
        btn.disabled = false; btn.className = claseOriginal;
        btnIcon.textContent = iconOriginal; btnLabel.textContent = labelOriginal;
    } finally {
        _ejecutando = false;
    }
}

// ── Inicio ─────────────────────────────────────────────────
obtenerGPS();
</script>
"""
