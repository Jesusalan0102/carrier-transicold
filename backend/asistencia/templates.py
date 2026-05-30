"""
templates.py — Módulo de plantillas de asistencia
Flujo profesional: Botón → Escanear QR → Selfie → Registro
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
    display: flex; align-items: center; gap: 12px;
    background: #f0f6ff; border-radius: 12px;
    padding: 14px 18px; margin-bottom: 20px;
    border-left: 5px solid #0057A8;
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
    background: #f8fafc; border-radius: 12px; padding: 14px 18px;
    margin-bottom: 20px; display: flex; justify-content: space-between;
    align-items: center; border: 1px solid #e2e8f0;
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
    display: flex; align-items: center; gap: 8px; font-size: 0.8rem;
    color: #6b7280; margin-bottom: 16px; background: #fafafa;
    border-radius: 8px; padding: 8px 12px; border: 1px solid #f0f0f0;
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

/* ══ MODAL BASE ══ */
.modal-overlay {
    position: fixed; top: 0; left: 0; width: 100%; height: 100%;
    background: rgba(0,0,0,0.92); z-index: 1000;
    display: flex; flex-direction: column; align-items: center; justify-content: center;
    padding: 20px;
}
.modal-header { color: white; text-align: center; margin-bottom: 18px; }
.modal-header h2 { font-size: 1.25rem; font-weight: 700; margin: 0 0 5px; }
.modal-header p  { font-size: 0.82rem; color: #94a3b8; margin: 0; }

/* ══ MODAL QR ══ */
.qr-video-wrap {
    position: relative; width: 100%; max-width: 340px;
    border-radius: 20px; overflow: hidden;
    border: 3px solid #0057A8;
    box-shadow: 0 0 0 6px rgba(0,87,168,0.25);
    background: #000;
}
#qrVideo { width: 100%; display: block; max-height: 340px; object-fit: cover; }
.qr-guide {
    position: absolute; inset: 0;
    display: flex; align-items: center; justify-content: center;
    pointer-events: none;
}
.qr-guide-inner {
    width: 200px; height: 200px;
    border: 3px solid rgba(255,255,255,0.8);
    border-radius: 16px;
    box-shadow: 0 0 0 9999px rgba(0,0,0,0.45);
}
.qr-corner {
    position: absolute; width: 28px; height: 28px; border-color: #0ef; border-style: solid;
}
.qr-corner.tl { top: 0;  left: 0;  border-width: 4px 0 0 4px; border-radius: 6px 0 0 0; }
.qr-corner.tr { top: 0;  right: 0; border-width: 4px 4px 0 0; border-radius: 0 6px 0 0; }
.qr-corner.bl { bottom: 0; left: 0;  border-width: 0 0 4px 4px; border-radius: 0 0 0 6px; }
.qr-corner.br { bottom: 0; right: 0; border-width: 0 4px 4px 0; border-radius: 0 0 6px 0; }
.qr-scan-line {
    position: absolute; left: 0; right: 0; height: 2px;
    background: linear-gradient(90deg, transparent, #0ef, transparent);
    animation: scanLine 2s linear infinite;
}
@keyframes scanLine { 0% { top: 0; } 100% { top: 100%; } }
.qr-status {
    margin-top: 14px; padding: 10px 18px; border-radius: 10px;
    font-size: 0.85rem; font-weight: 600; color: white; text-align: center;
    background: rgba(255,255,255,0.1); width: 100%; max-width: 340px;
    min-height: 42px; display: flex; align-items: center; justify-content: center;
}
.qr-status.ok  { background: rgba(22,163,74,0.35); border: 1px solid rgba(22,163,74,0.5); }
.qr-status.err { background: rgba(220,38,38,0.35); border: 1px solid rgba(220,38,38,0.5); }
.btn-cancel-modal {
    margin-top: 14px; padding: 13px 28px; border: 1.5px solid rgba(255,255,255,0.25);
    border-radius: 12px; font-size: 0.9rem; font-weight: 600;
    cursor: pointer; background: transparent; color: white;
}
.btn-cancel-modal:hover { background: rgba(255,255,255,0.08); }

/* ══ MODAL SELFIE ══ */
.selfie-video-wrap {
    position: relative; width: 100%; max-width: 340px;
    border-radius: 20px; overflow: hidden;
    border: 3px solid #0057A8;
    box-shadow: 0 0 0 6px rgba(0,87,168,0.25);
}
#selfieVideo { width: 100%; display: block; transform: scaleX(-1); background: #000; }
.selfie-guide {
    position: absolute; top: 50%; left: 50%; transform: translate(-50%,-50%);
    width: 160px; height: 200px;
    border: 2.5px dashed rgba(255,255,255,0.6);
    border-radius: 50% 50% 50% 50% / 42% 42% 58% 58%;
    pointer-events: none;
}
.selfie-actions { display: flex; gap: 14px; margin-top: 16px; width: 100%; max-width: 340px; }
.btn-capture {
    flex: 1; padding: 16px; border: none; border-radius: 14px;
    font-size: 1rem; font-weight: 700; cursor: pointer;
    background: linear-gradient(135deg, #002B5B, #0057A8); color: white;
    box-shadow: 0 4px 14px rgba(0,87,168,0.4); transition: transform 0.15s;
}
.btn-capture:active { transform: scale(0.97); }
.selfie-preview-wrap {
    position: relative; width: 100%; max-width: 340px;
    border-radius: 20px; overflow: hidden;
    border: 3px solid #16a34a;
    box-shadow: 0 0 0 6px rgba(22,163,74,0.2);
}
#selfiePreview { width: 100%; display: block; transform: scaleX(-1); }
.selfie-preview-badge {
    position: absolute; bottom: 10px; left: 50%; transform: translateX(-50%);
    background: rgba(22,163,74,0.92); color: white; padding: 5px 14px;
    border-radius: 20px; font-size: 0.78rem; font-weight: 600; white-space: nowrap;
}
.selfie-retake-bar { display: flex; gap: 12px; margin-top: 14px; width: 100%; max-width: 340px; }
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
.selfie-thumb {
    width: 44px; height: 44px; border-radius: 50%;
    object-fit: cover; border: 2px solid #e2e8f0;
    transform: scaleX(-1);
}

/* ══ PASOS DEL FLUJO ══ */
.steps-bar {
    display: flex; align-items: center; justify-content: center;
    gap: 6px; margin-bottom: 16px;
}
.step-dot {
    width: 8px; height: 8px; border-radius: 50%; background: rgba(255,255,255,0.25);
    transition: background 0.3s;
}
.step-dot.active { background: #0ef; width: 22px; border-radius: 4px; }
.step-dot.done   { background: #16a34a; }
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
        <div style="font-size:0.7rem;font-weight:700;color:#6b7280;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:10px;">Tu horario de hoy</div>
        <div class="schedule-info">
            <div class="schedule-time"><div class="label">Entrada</div><div class="time" id="schedEntrada">--:--</div></div>
            <div class="schedule-divider"></div>
            <div class="schedule-time"><div class="label">Salida</div><div class="time" id="schedSalida">--:--</div></div>
        </div>
        <div id="alertHorario"></div>
    </div>

    <!-- Estado actual -->
    <div class="checkin-card">
        <div class="checkin-status-bar">
            <span class="status-dot" id="statusDot"></span>
            <div>
                <div style="font-weight:700;font-size:0.9rem;color:#002B5B;" id="statusTitle">Cargando...</div>
                <div style="font-size:0.78rem;color:#6b7280;" id="statusSub"></div>
            </div>
        </div>
        <div id="progressSection" style="display:none;margin-bottom:16px;">
            <div style="display:flex;justify-content:space-between;font-size:0.75rem;color:#6b7280;margin-bottom:4px;">
                <span>Jornada laboral</span><span id="progressLabel">0%</span>
            </div>
            <div class="progress-track"><div class="progress-fill" id="progressFill" style="width:0%"></div></div>
        </div>
        <div id="alertMsg"></div>
        <button class="btn-checkin btn-disabled" id="btnAccion" disabled>
            <span id="btnIcon">⏳</span><span id="btnLabel">Cargando...</span>
        </button>
    </div>

    <!-- Registros de hoy -->
    <div class="checkin-card" id="cardRegistros" style="display:none;">
        <div style="font-size:0.7rem;font-weight:700;color:#6b7280;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:14px;">Registros de hoy</div>
        <div id="listaRegistros"></div>
    </div>
</div>

<!-- ══════════ MODAL QR ══════════ -->
<div class="modal-overlay" id="qrModal" style="display:none;">
    <div class="steps-bar">
        <div class="step-dot active" id="step1"></div>
        <div class="step-dot" id="step2"></div>
        <div class="step-dot" id="step3"></div>
    </div>
    <div class="modal-header">
        <h2>📱 Paso 1 — Escanear QR</h2>
        <p>Apunta la cámara al código QR del área de trabajo</p>
    </div>
    <div class="qr-video-wrap">
        <video id="qrVideo" autoplay playsinline muted></video>
        <div class="qr-guide">
            <div class="qr-guide-inner">
                <div class="qr-corner tl"></div>
                <div class="qr-corner tr"></div>
                <div class="qr-corner bl"></div>
                <div class="qr-corner br"></div>
                <div class="qr-scan-line"></div>
            </div>
        </div>
    </div>
    <div class="qr-status" id="qrStatus">🔍 Buscando código QR...</div>
    <button class="btn-cancel-modal" onclick="cancelarQR()">✕ Cancelar</button>
</div>

<!-- ══════════ MODAL SELFIE ══════════ -->
<div class="modal-overlay" id="selfieModal" style="display:none;">
    <div class="steps-bar">
        <div class="step-dot done" id="step1s"></div>
        <div class="step-dot active" id="step2s"></div>
        <div class="step-dot" id="step3s"></div>
    </div>

    <!-- Cámara -->
    <div id="selfieCaptura">
        <div class="modal-header">
            <h2 id="selfieModalTitle">📸 Paso 2 — Selfie de Entrada</h2>
            <p>Coloca tu rostro dentro del óvalo y presiona capturar</p>
        </div>
        <div class="selfie-video-wrap">
            <video id="selfieVideo" autoplay playsinline muted></video>
            <div class="selfie-guide"></div>
        </div>
        <div class="selfie-actions">
            <button class="btn-cancel-modal" style="flex:1;" onclick="cancelarSelfie()">✕ Cancelar</button>
            <button class="btn-capture" onclick="capturarFoto()">📸 Capturar</button>
        </div>
    </div>

    <!-- Preview -->
    <div id="selfiePreviewSection" style="display:none;">
        <div class="modal-header">
            <h2>✅ ¿Usar esta foto?</h2>
            <p>Confirma o repite la captura</p>
        </div>
        <div class="selfie-preview-wrap">
            <img id="selfiePreview" src="" alt="Selfie">
            <div class="selfie-preview-badge">📸 Foto lista</div>
        </div>
        <div class="selfie-retake-bar">
            <button class="btn-retake" onclick="repetirSelfie()">🔄 Repetir</button>
            <button class="btn-confirm-selfie" onclick="confirmarSelfie()">✅ Confirmar y Registrar</button>
        </div>
    </div>
</div>

<canvas id="selfieCanvas" style="display:none;"></canvas>

<script>
const fetchAuth  = window.fetchAuth;
const username   = window.username;
const QR_URL_ESPERADA = "https://app-83fd3b1b-5d1d-43fd-be37-63f56db0efe8.cleverapps.io/app/checkin";

// ── Estado ────────────────────────────────────────────────
let gpsCoords       = null;
let horarioHoy      = null;
let estadoHoy       = null;
let accionActual    = null;
let accionPendiente = null;
let selfieBlob      = null;
let selfieStream    = null;
let qrStream        = null;
let qrInterval      = null;
let _ejecutando     = false;

// ── Helpers ───────────────────────────────────────────────
const horaActualTJ = () => new Date().toLocaleTimeString('es-MX', { timeZone:'America/Tijuana', hour12:false, hour:'2-digit', minute:'2-digit' });
const fechaHoyTJ   = () => new Date().toLocaleDateString('sv-SE', { timeZone:'America/Tijuana' });
const minDesde0    = hhmm => { if(!hhmm) return null; const [h,m]=hhmm.split(':').map(Number); return h*60+m; };
const fmtHora      = hhmm => hhmm ? hhmm.slice(0,5) : '—';
const cerrarStream = s => { if(s) s.getTracks().forEach(t=>t.stop()); };

// ── GPS ───────────────────────────────────────────────────
function obtenerGPS() {
    if (!navigator.geolocation) { setGPSStatus(false,'GPS no soportado'); inicializarPagina(); return; }
    navigator.geolocation.getCurrentPosition(
        pos => {
            gpsCoords = { lat:pos.coords.latitude, lon:pos.coords.longitude, precision:pos.coords.accuracy };
            const p = pos.coords.accuracy.toFixed(0), ok = pos.coords.accuracy <= 200;
            setGPSStatus(ok, ok ? `GPS preciso (±${p}m)` : `GPS poco preciso (±${p}m) — Acércate a una ventana`);
            inicializarPagina();
        },
        () => { setGPSStatus(false,'GPS denegado — Activa el permiso de ubicación'); inicializarPagina(); },
        { enableHighAccuracy:true, timeout:15000, maximumAge:0 }
    );
}
function setGPSStatus(ok, msg) {
    document.getElementById('gpsDot').className = 'gps-dot'+(ok?' ok':'');
    document.getElementById('gpsText').textContent = (ok?'✓ ':'⚠ ')+msg;
}

// ── Carga inicial ─────────────────────────────────────────
async function inicializarPagina() {
    await Promise.all([cargarHorarioHoy(), cargarEstadoHoy()]);
    determinarAccion(); renderUI();
}
async function cargarHorarioHoy() {
    try { const r = await fetchAuth(`/api/horarios/hoy?username=${username}&fecha=${fechaHoyTJ()}`); if(r&&r.ok){const d=await r.json();horarioHoy=d.horario||null;} } catch(e){horarioHoy=null;}
}
async function cargarEstadoHoy() {
    try { const r = await fetchAuth(`/api/asistencia/estado-hoy?username=${username}&fecha=${fechaHoyTJ()}`); if(r&&r.ok){estadoHoy=await r.json();} } catch(e){estadoHoy=null;}
}

// ── Determinar acción ─────────────────────────────────────
function determinarAccion() {
    if (!horarioHoy || (!horarioHoy.hora_entrada && !horarioHoy.hora_salida)) { accionActual='sin_horario'; return; }
    const e=estadoHoy?.tiene_entrada, s=estadoHoy?.tiene_salida;
    if(e&&s) accionActual='completo';
    else if(e&&!s) accionActual='salida';
    else accionActual='entrada';
}

// ── Render UI ─────────────────────────────────────────────
function renderUI() {
    if (horarioHoy) {
        document.getElementById('cardHorario').style.display='block';
        document.getElementById('schedEntrada').textContent = fmtHora(horarioHoy.hora_entrada)||'Libre';
        document.getElementById('schedSalida').textContent  = fmtHora(horarioHoy.hora_salida)||'Libre';
        if (accionActual==='entrada' && horarioHoy.hora_entrada) {
            const diff = minDesde0(horaActualTJ()) - minDesde0(horarioHoy.hora_entrada);
            if (diff>15) document.getElementById('alertHorario').innerHTML =
                `<div class="alert-box alert-warning">⏱ Llegas con <b>${diff} min de retardo</b>.</div>`;
        }
        if (accionActual==='salida' && horarioHoy.hora_entrada && horarioHoy.hora_salida) {
            const ahoraMin=minDesde0(horaActualTJ()), eMin=minDesde0(horarioHoy.hora_entrada), sMin=minDesde0(horarioHoy.hora_salida);
            const jornada=sMin-eMin;
            if(jornada>0){
                const pct=Math.min(100,Math.round((Math.max(0,ahoraMin-eMin)/jornada)*100));
                document.getElementById('progressSection').style.display='block';
                document.getElementById('progressFill').style.width=pct+'%';
                document.getElementById('progressLabel').textContent=pct+'% de la jornada';
            }
        }
    }
    const btn=document.getElementById('btnAccion'), ic=document.getElementById('btnIcon'), lb=document.getElementById('btnLabel'), al=document.getElementById('alertMsg');
    btn.onclick = abrirQRModal;
    switch(accionActual){
        case 'sin_horario':
            document.getElementById('statusDot').className='status-dot orange';
            document.getElementById('statusTitle').textContent='Sin horario asignado hoy';
            document.getElementById('statusSub').textContent='Comunícate con el administrador';
            al.innerHTML='<div class="alert-box alert-warning">No tienes horario para hoy. No puedes registrar asistencia.</div>';
            btn.className='btn-checkin btn-disabled'; btn.disabled=true;
            ic.textContent='🚫'; lb.textContent='Sin horario para hoy'; break;
        case 'entrada':
            document.getElementById('statusDot').className='status-dot orange';
            document.getElementById('statusTitle').textContent='Pendiente de entrada';
            document.getElementById('statusSub').textContent=`Hora actual: ${horaActualTJ()}`;
            btn.className='btn-checkin btn-entrada'; btn.disabled=false;
            ic.textContent='📱'; lb.textContent='Escanear QR y Registrar Entrada'; break;
        case 'salida': {
            document.getElementById('statusDot').className='status-dot green';
            document.getElementById('statusTitle').textContent=`Entrada a las ${fmtHora(estadoHoy.hora_entrada_real)}`;
            document.getElementById('statusSub').textContent=`Hora actual: ${horaActualTJ()}`;
            let puedeRegistrar=true;
            if (horarioHoy?.hora_entrada && horarioHoy?.hora_salida) {
                const aMin=minDesde0(horaActualTJ()), eMin=minDesde0(horarioHoy.hora_entrada), sMin=minDesde0(horarioHoy.hora_salida);
                const mitad=eMin+Math.floor((sMin-eMin)*0.5);
                if(aMin<mitad){ puedeRegistrar=false; al.innerHTML=`<div class="alert-box alert-info">⏰ Podrás registrar salida en <b>${mitad-aMin} minutos</b>.</div>`; }
            }
            if(!puedeRegistrar){ btn.className='btn-checkin btn-disabled'; btn.disabled=true; ic.textContent='🔒'; lb.textContent='Salida no disponible aún'; }
            else { btn.className='btn-checkin btn-salida'; btn.disabled=false; ic.textContent='📱'; lb.textContent='Escanear QR y Registrar Salida'; }
            break;
        }
        case 'completo':
            document.getElementById('statusDot').className='status-dot green';
            document.getElementById('statusTitle').textContent='✅ Jornada completada';
            document.getElementById('statusSub').textContent=`Entrada: ${fmtHora(estadoHoy.hora_entrada_real)} · Salida: ${fmtHora(estadoHoy.hora_salida_real)}`;
            al.innerHTML='<div class="alert-box alert-success">🎉 Has completado tu registro del día. ¡Hasta mañana!</div>';
            btn.className='btn-checkin btn-disabled'; btn.disabled=true;
            ic.textContent='✅'; lb.textContent='Jornada completada'; break;
    }
    cargarRegistrosUI();
}

// ── Registros del día ─────────────────────────────────────
async function cargarRegistrosUI() {
    try {
        const r = await fetchAuth(`/api/asistencia/registros?fecha=${fechaHoyTJ()}&username=${username}`);
        if(!r||!r.ok) return;
        const registros = await r.json();
        if(!Array.isArray(registros)||!registros.length) return;
        let html='';
        registros.forEach(r=>{
            const tipo   = r.tipo==='entrada'?'🟢 Entrada':'🔴 Salida';
            const estado = r.aprobado
                ? '<span style="color:#16a34a;font-size:0.78rem;">✓ Aprobado</span>'
                : '<span style="color:#dc2626;font-size:0.78rem;">✗ Rechazado</span>';
            const dist = r.distancia_metros!=null?`${Math.round(r.distancia_metros)}m`:'Sin GPS';
            const foto = r.selfie_url
                ? `<img src="${r.selfie_url}" class="selfie-thumb" alt="selfie">`
                : '<div style="width:44px;height:44px;border-radius:50%;background:#f1f5f9;display:flex;align-items:center;justify-content:center;font-size:1.2rem;">👤</div>';
            html+=`<div class="registro-item">
                <div style="display:flex;align-items:center;gap:12px;">
                    ${foto}
                    <div><div style="font-weight:600;font-size:0.88rem;">${tipo}</div><div style="font-size:0.75rem;color:#6b7280;">📍 ${dist}</div></div>
                </div>
                <div style="text-align:right;">
                    <div style="font-weight:700;font-size:0.95rem;color:#002B5B;">${fmtHora(r.hora_checkin)}</div>
                    <div>${estado}</div>
                </div>
            </div>`;
        });
        document.getElementById('listaRegistros').innerHTML=html;
        document.getElementById('cardRegistros').style.display='block';
    } catch(e){}
}

// ══════════ PASO 1 — ESCANEAR QR ══════════

async function abrirQRModal() {
    if(accionActual!=='entrada'&&accionActual!=='salida') return;
    accionPendiente = accionActual;

    document.getElementById('qrStatus').className='qr-status';
    document.getElementById('qrStatus').textContent='🔍 Buscando código QR...';
    document.getElementById('qrModal').style.display='flex';

    try {
        // Preferir cámara trasera para escanear QR
        qrStream = await navigator.mediaDevices.getUserMedia({
            video: { facingMode: { ideal:'environment' }, width:{ideal:1280}, height:{ideal:720} },
            audio: false
        });
        document.getElementById('qrVideo').srcObject = qrStream;
        iniciarEscaneoQR();
    } catch(err) {
        document.getElementById('qrStatus').className='qr-status err';
        document.getElementById('qrStatus').textContent='❌ No se pudo acceder a la cámara. Verifica permisos.';
    }
}

function iniciarEscaneoQR() {
    // Usar BarcodeDetector si está disponible (Chrome Android, Edge)
    if ('BarcodeDetector' in window) {
        const detector = new BarcodeDetector({ formats:['qr_code'] });
        const video = document.getElementById('qrVideo');
        qrInterval = setInterval(async () => {
            if (video.readyState !== video.HAVE_ENOUGH_DATA) return;
            try {
                const barcodes = await detector.detect(video);
                if (barcodes.length > 0) {
                    clearInterval(qrInterval);
                    procesarQR(barcodes[0].rawValue);
                }
            } catch(e) {}
        }, 300);
    } else {
        // Fallback: usar jsQR via canvas
        const script = document.createElement('script');
        script.src = 'https://cdn.jsdelivr.net/npm/jsqr@1.4.0/dist/jsQR.min.js';
        script.onload = () => {
            const video  = document.getElementById('qrVideo');
            const canvas = document.createElement('canvas');
            const ctx    = canvas.getContext('2d');
            qrInterval = setInterval(() => {
                if (video.readyState !== video.HAVE_ENOUGH_DATA) return;
                canvas.width  = video.videoWidth;
                canvas.height = video.videoHeight;
                ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
                const img  = ctx.getImageData(0, 0, canvas.width, canvas.height);
                const code = jsQR(img.data, img.width, img.height, { inversionAttempts:'dontInvert' });
                if (code) {
                    clearInterval(qrInterval);
                    procesarQR(code.data);
                }
            }, 300);
        };
        script.onerror = () => {
            document.getElementById('qrStatus').className='qr-status err';
            document.getElementById('qrStatus').textContent='❌ No se pudo cargar el escáner QR.';
        };
        document.head.appendChild(script);
    }
}

function procesarQR(valor) {
    const st = document.getElementById('qrStatus');
    // Validar que el QR sea el correcto del sistema
    const esValido = valor && (
        valor === QR_URL_ESPERADA ||
        valor.includes('/app/checkin')
    );
    if (esValido) {
        st.className = 'qr-status ok';
        st.textContent = '✅ QR válido — Abriendo cámara...';
        // Pequeña pausa visual antes de pasar a selfie
        setTimeout(() => {
            cerrarStream(qrStream); qrStream=null;
            document.getElementById('qrModal').style.display='none';
            abrirSelfieModal();
        }, 800);
    } else {
        st.className = 'qr-status err';
        st.textContent = '❌ QR no válido — Usa el QR del sistema';
        // Reiniciar escaneo después de 2 segundos
        setTimeout(iniciarEscaneoQR, 2000);
    }
}

function cancelarQR() {
    clearInterval(qrInterval);
    cerrarStream(qrStream); qrStream=null;
    document.getElementById('qrModal').style.display='none';
    accionPendiente=null;
}

// ══════════ PASO 2 — SELFIE ══════════

async function abrirSelfieModal() {
    selfieBlob=null;
    document.getElementById('selfieCaptura').style.display='block';
    document.getElementById('selfiePreviewSection').style.display='none';
    document.getElementById('selfieModalTitle').textContent =
        accionPendiente==='entrada'?'📸 Paso 2 — Selfie de Entrada':'📸 Paso 2 — Selfie de Salida';
    document.getElementById('selfieModal').style.display='flex';
    try {
        selfieStream = await navigator.mediaDevices.getUserMedia({
            video:{ facingMode:'user', width:{ideal:640}, height:{ideal:480} }, audio:false
        });
        document.getElementById('selfieVideo').srcObject = selfieStream;
    } catch(err) {
        cancelarSelfie();
        document.getElementById('alertMsg').innerHTML =
            '<div class="alert-box alert-error">❌ No se pudo acceder a la cámara frontal.</div>';
    }
}

function capturarFoto() {
    const video=document.getElementById('selfieVideo'), canvas=document.getElementById('selfieCanvas');
    canvas.width=video.videoWidth||640; canvas.height=video.videoHeight||480;
    const ctx=canvas.getContext('2d');
    ctx.translate(canvas.width,0); ctx.scale(-1,1);
    ctx.drawImage(video,0,0,canvas.width,canvas.height);
    ctx.setTransform(1,0,0,1,0,0);
    document.getElementById('selfiePreview').src=canvas.toDataURL('image/jpeg',0.85);
    document.getElementById('selfieCaptura').style.display='none';
    document.getElementById('selfiePreviewSection').style.display='block';
}

function repetirSelfie() {
    document.getElementById('selfieCaptura').style.display='block';
    document.getElementById('selfiePreviewSection').style.display='none';
}

function confirmarSelfie() {
    const canvas=document.getElementById('selfieCanvas');
    canvas.toBlob(blob => {
        selfieBlob=blob;
        cerrarStream(selfieStream); selfieStream=null;
        document.getElementById('selfieVideo').srcObject=null;
        document.getElementById('selfieModal').style.display='none';
        ejecutarRegistro();
    }, 'image/jpeg', 0.85);
}

function cancelarSelfie() {
    cerrarStream(selfieStream); selfieStream=null;
    document.getElementById('selfieModal').style.display='none';
    selfieBlob=null; accionPendiente=null;
}

// ══════════ PASO 3 — REGISTRAR ══════════

async function ejecutarRegistro() {
    if(!accionPendiente||!selfieBlob) return;
    if(_ejecutando) return;
    _ejecutando=true;

    const btn=document.getElementById('btnAccion'), ic=document.getElementById('btnIcon'), lb=document.getElementById('btnLabel'), al=document.getElementById('alertMsg');
    const labelOrig = accionPendiente==='entrada'?'Escanear QR y Registrar Entrada':'Escanear QR y Registrar Salida';
    const claseOrig = accionPendiente==='entrada'?'btn-checkin btn-entrada':'btn-checkin btn-salida';

    btn.disabled=true; btn.className='btn-checkin btn-disabled';
    ic.textContent='⏳'; lb.textContent='Registrando...'; al.innerHTML='';

    try {
        // Subir selfie
        const fd=new FormData();
        fd.append('file', selfieBlob, `selfie_${username}_${fechaHoyTJ()}_${accionPendiente}.jpg`);
        fd.append('username',username); fd.append('tipo',accionPendiente); fd.append('fecha',fechaHoyTJ());
        let selfieUrl=null;
        const upRes = await fetchAuth('/api/asistencia/selfie', { method:'POST', body:fd });
        if(upRes&&upRes.ok){ const ud=await upRes.json(); selfieUrl=ud.url||null; }

        // Registrar checkin
        const res = await fetchAuth('/api/asistencia/checkin', {
            method:'POST', headers:{'Content-Type':'application/json'},
            body: JSON.stringify({
                username, tipo:accionPendiente, fecha:fechaHoyTJ(),
                lat:gpsCoords?.lat??null, lon:gpsCoords?.lon??null,
                precision_gps:gpsCoords?.precision??null, selfie_url:selfieUrl
            })
        });
        if(!res){ _ejecutando=false; return; }
        let data={};
        try{ data=await res.json(); }catch(_){ data={detail:'Respuesta inválida del servidor.'}; }

        if(res.ok){
            const extra = accionPendiente==='entrada'
                ? (data.retardo_min>0?` · Retardo: ${data.retardo_min} min`:'')
                : (data.horas_trabajadas?` · ${data.horas_trabajadas}h trabajadas`:'');
            al.innerHTML=`<div class="alert-box alert-success">✅ ${accionPendiente==='entrada'?'Entrada':'Salida'} registrada a las <b>${fmtHora(data.hora_registro)}</b>${extra}</div>`;
            selfieBlob=null; accionPendiente=null;
            await cargarEstadoHoy(); determinarAccion(); renderUI();
        } else {
            al.innerHTML=`<div class="alert-box alert-error">❌ ${data.detail||`Error ${res.status}. Intenta de nuevo.`}</div>`;
            btn.disabled=false; btn.className=claseOrig; ic.textContent='📱'; lb.textContent=labelOrig;
        }
    } catch(err){
        al.innerHTML='<div class="alert-box alert-error">❌ Sin conexión. Intenta de nuevo.</div>';
        btn.disabled=false; btn.className=claseOrig; ic.textContent='📱'; lb.textContent=labelOrig;
    } finally { _ejecutando=false; }
}

// ── Arranque ──────────────────────────────────────────────
obtenerGPS();
</script>
"""
