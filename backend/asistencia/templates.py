"""
templates.py — Módulo de plantillas de asistencia
Contiene el HTML del checkin para técnicos con soporte de ENTRADA y SALIDA
basado en el horario importado semanalmente.
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
.schedule-time {
    text-align: center;
    flex: 1;
}
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
.btn-entrada {
    background: linear-gradient(135deg, #002B5B 0%, #0057A8 100%);
    color: white;
    box-shadow: 0 4px 16px rgba(0,87,168,0.35);
}
.btn-salida {
    background: linear-gradient(135deg, #064e3b 0%, #16a34a 100%);
    color: white;
    box-shadow: 0 4px 16px rgba(22,163,74,0.35);
}
.btn-disabled {
    background: #e5e7eb; color: #9ca3af;
    cursor: not-allowed; box-shadow: none;
}
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
.progress-track {
    height: 6px; background: #e5e7eb; border-radius: 99px; margin: 12px 0; overflow: hidden;
}
.progress-fill { height: 100%; border-radius: 99px; background: linear-gradient(90deg, #0057A8, #16a34a); transition: width 0.6s ease; }
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
        <button class="btn-checkin btn-disabled" id="btnAccion" onclick="ejecutarAccion()" disabled>
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

<script>
const fetchAuth = window.fetchAuth;
const username  = window.username;

// ── Estado local ───────────────────────────────────────────
let gpsCoords  = null;
let horarioHoy = null;   // { hora_entrada, hora_salida }
let estadoHoy  = null;   // { tiene_entrada, hora_entrada_real, tiene_salida, hora_salida_real }
let accionActual = null; // 'entrada' | 'salida' | 'completo' | 'sin_horario' | 'fuera_rango'

// ── Helpers ────────────────────────────────────────────────
function horaActualTJ() {
    return new Date().toLocaleTimeString('es-MX', { timeZone:'America/Tijuana', hour12:false, hour:'2-digit', minute:'2-digit' });
}
function fechaHoyTJ() {
    return new Date().toLocaleDateString('sv-SE', { timeZone:'America/Tijuana' });
}
function minutosDesdeMedianoche(hhmm) {
    if (!hhmm) return null;
    const [h, m] = hhmm.split(':').map(Number);
    return h * 60 + m;
}
function diffMinutos(horaA, horaB) {
    // horaA - horaB en minutos (positivo = tarde, negativo = adelantado)
    return minutosDesdeMedianoche(horaA) - minutosDesdeMedianoche(horaB);
}
function formatHora(hhmm) {
    if (!hhmm) return '—';
    return hhmm.slice(0,5);
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
            const ok = pos.coords.accuracy <= 200;
            setGPSStatus(ok, ok ? `GPS preciso (±${prec}m)` : `GPS poco preciso (±${prec}m) — Acércate a una ventana`);
            inicializarPagina();
        },
        err => {
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
        const fecha = fechaHoyTJ();
        const res = await fetchAuth(`/api/horarios/hoy?username=${username}&fecha=${fecha}`);
        if (res.ok) {
            const data = await res.json();
            horarioHoy = data.horario || null;
        }
    } catch(e) { horarioHoy = null; }
}

async function cargarEstadoHoy() {
    try {
        const fecha = fechaHoyTJ();
        const res = await fetchAuth(`/api/asistencia/estado-hoy?username=${username}&fecha=${fecha}`);
        if (res.ok) {
            estadoHoy = await res.json();
        }
    } catch(e) { estadoHoy = null; }
}

// ── 3. Determinar qué acción está disponible ───────────────
function determinarAccion() {
    if (!horarioHoy || (!horarioHoy.hora_entrada && !horarioHoy.hora_salida)) {
        accionActual = 'sin_horario';
        return;
    }
    const tieneEntrada = estadoHoy?.tiene_entrada;
    const tieneSalida  = estadoHoy?.tiene_salida;

    if (tieneEntrada && tieneSalida) {
        accionActual = 'completo';
    } else if (tieneEntrada && !tieneSalida) {
        accionActual = 'salida';
    } else {
        accionActual = 'entrada';
    }
}

// ── 4. Renderizar UI según el estado ──────────────────────
function renderUI() {
    // Horario
    if (horarioHoy) {
        document.getElementById('cardHorario').style.display = 'block';
        document.getElementById('schedEntrada').textContent = formatHora(horarioHoy.hora_entrada) || 'Libre';
        document.getElementById('schedSalida').textContent  = formatHora(horarioHoy.hora_salida)  || 'Libre';

        // Alerta de retardo (solo si aún no registró entrada)
        if (accionActual === 'entrada' && horarioHoy.hora_entrada) {
            const ahoraMin = minutosDesdeMedianoche(horaActualTJ());
            const entradaMin = minutosDesdeMedianoche(horarioHoy.hora_entrada);
            const TOLERANCIA = 15;
            if (ahoraMin > entradaMin + TOLERANCIA) {
                const retardo = ahoraMin - entradaMin;
                document.getElementById('alertHorario').innerHTML =
                    `<div class="alert-box alert-warning">⏱ Llegas con <b>${retardo} min de retardo</b> sobre tu horario de entrada.</div>`;
            }
        }

        // Barra de progreso si ya tiene entrada y hay horario completo
        if (accionActual === 'salida' && horarioHoy.hora_entrada && horarioHoy.hora_salida) {
            const ahoraMin     = minutosDesdeMedianoche(horaActualTJ());
            const entradaMin   = minutosDesdeMedianoche(horarioHoy.hora_entrada);
            const salidaMin    = minutosDesdeMedianoche(horarioHoy.hora_salida);
            const jornada      = salidaMin - entradaMin;
            const transcurrido = Math.max(0, ahoraMin - entradaMin);
            const pct          = Math.min(100, Math.round((transcurrido / jornada) * 100));
            document.getElementById('progressSection').style.display = 'block';
            document.getElementById('progressFill').style.width = pct + '%';
            document.getElementById('progressLabel').textContent = pct + '% de la jornada';
        }
    }

    // StatusBar
    const statusBar  = document.getElementById('statusBar');
    const statusDot  = document.getElementById('statusDot');
    const statusTitle= document.getElementById('statusTitle');
    const statusSub  = document.getElementById('statusSub');
    const btn        = document.getElementById('btnAccion');
    const btnIcon    = document.getElementById('btnIcon');
    const btnLabel   = document.getElementById('btnLabel');
    const alertMsg   = document.getElementById('alertMsg');

    btn.onclick = ejecutarAccion;

    switch (accionActual) {

        case 'sin_horario':
            statusDot.className = 'status-dot orange';
            statusTitle.textContent = 'Sin horario asignado hoy';
            statusSub.textContent   = 'Comunícate con el administrador';
            alertMsg.innerHTML = '<div class="alert-box alert-warning">No tienes horario registrado para hoy. No puedes registrar asistencia.</div>';
            btn.className = 'btn-checkin btn-disabled';
            btn.disabled  = true;
            btnIcon.textContent  = '🚫';
            btnLabel.textContent = 'Sin horario para hoy';
            break;

        case 'entrada':
            statusDot.className = 'status-dot orange';
            statusTitle.textContent = 'Pendiente de entrada';
            statusSub.textContent   = `Hora actual: ${horaActualTJ()}`;
            btn.className = 'btn-checkin btn-entrada';
            btn.disabled  = false;
            btnIcon.textContent  = '🟢';
            btnLabel.textContent = 'Registrar Entrada';
            break;

        case 'salida':
            statusDot.className = 'status-dot green';
            statusTitle.textContent = `Entrada registrada a las ${formatHora(estadoHoy.hora_entrada_real)}`;
            statusSub.textContent   = `Hora actual: ${horaActualTJ()}`;

            // Validar si puede registrar salida (al menos 50% de la jornada transcurrida, o sin horario de salida)
            let puedeRegistrarSalida = true;
            let msgSalida = '';
            if (horarioHoy?.hora_entrada && horarioHoy?.hora_salida) {
                const ahoraMin   = minutosDesdeMedianoche(horaActualTJ());
                const entradaMin = minutosDesdeMedianoche(horarioHoy.hora_entrada);
                const salidaMin  = minutosDesdeMedianoche(horarioHoy.hora_salida);
                const mitadJornada = entradaMin + Math.floor((salidaMin - entradaMin) * 0.5);
                if (ahoraMin < mitadJornada) {
                    puedeRegistrarSalida = false;
                    const faltanMin = mitadJornada - ahoraMin;
                    msgSalida = `Podrás registrar tu salida en <b>${faltanMin} minutos</b> (al 50% de tu jornada).`;
                }
            }

            if (!puedeRegistrarSalida) {
                alertMsg.innerHTML = `<div class="alert-box alert-info">⏰ ${msgSalida}</div>`;
                btn.className = 'btn-checkin btn-disabled';
                btn.disabled  = true;
                btnIcon.textContent  = '🔒';
                btnLabel.textContent = 'Salida no disponible aún';
            } else {
                btn.className = 'btn-checkin btn-salida';
                btn.disabled  = false;
                btnIcon.textContent  = '🔴';
                btnLabel.textContent = 'Registrar Salida';
            }
            break;

        case 'completo':
            statusDot.className = 'status-dot green';
            statusTitle.textContent = '✅ Jornada completada';
            statusSub.textContent   = `Entrada: ${formatHora(estadoHoy.hora_entrada_real)} · Salida: ${formatHora(estadoHoy.hora_salida_real)}`;
            alertMsg.innerHTML = '<div class="alert-box alert-success">🎉 Has completado tu registro del día. ¡Hasta mañana!</div>';
            btn.className = 'btn-checkin btn-disabled';
            btn.disabled  = true;
            btnIcon.textContent  = '✅';
            btnLabel.textContent = 'Jornada completada';
            break;
    }

    // Registros
    cargarRegistrosUI();
}

// ── 5. Registros de hoy ────────────────────────────────────
async function cargarRegistrosUI() {
    try {
        const fecha = fechaHoyTJ();
        const res = await fetchAuth(`/api/asistencia/registros?fecha=${fecha}&username=${username}`);
        if (!res.ok) return;
        const registros = await res.json();
        if (!registros.length) return;

        let html = '';
        registros.forEach(r => {
            const tipo   = r.tipo === 'entrada' ? '🟢 Entrada' : '🔴 Salida';
            const estado = r.aprobado ? '<span style="color:#16a34a;font-size:0.78rem;">✓ Aprobado</span>' : '<span style="color:#dc2626;font-size:0.78rem;">✗ Rechazado</span>';
            const dist   = r.distancia_metros != null ? `${Math.round(r.distancia_metros)}m` : 'Sin GPS';
            html += `<div class="registro-item">
                <div>
                    <div style="font-weight:600;font-size:0.88rem;">${tipo}</div>
                    <div style="font-size:0.75rem;color:#6b7280;">📍 ${dist}</div>
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

// ── 6. Ejecutar acción (entrada o salida) ─────────────────
async function ejecutarAccion() {
    if (accionActual !== 'entrada' && accionActual !== 'salida') return;

    const btn = document.getElementById('btnAccion');
    btn.disabled = true;
    btn.innerHTML = '<span>⏳</span><span>Registrando...</span>';

    try {
        const payload = {
            username: username,
            tipo: accionActual,
            fecha: fechaHoyTJ(),
            lat: gpsCoords?.lat  ?? null,
            lon: gpsCoords?.lon  ?? null,
            precision_gps: gpsCoords?.precision ?? null
        };

        const res = await fetchAuth('/api/asistencia/checkin', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        const data = await res.json();

        if (res.ok) {
            // Éxito
            const msgEl = document.getElementById('alertMsg');
            if (accionActual === 'entrada') {
                const retardo = data.retardo_min > 0 ? ` (retardo: ${data.retardo_min} min)` : '';
                msgEl.innerHTML = `<div class="alert-box alert-success">✅ Entrada registrada a las <b>${formatHora(data.hora_registro)}</b>${retardo}</div>`;
            } else {
                const horasTrabajadas = data.horas_trabajadas ? ` · ${data.horas_trabajadas}h trabajadas` : '';
                msgEl.innerHTML = `<div class="alert-box alert-success">✅ Salida registrada a las <b>${formatHora(data.hora_registro)}</b>${horasTrabajadas}</div>`;
            }
            // Recargar estado
            await cargarEstadoHoy();
            determinarAccion();
            renderUI();
        } else {
            document.getElementById('alertMsg').innerHTML =
                `<div class="alert-box alert-error">❌ ${data.detail || 'Error al registrar'}</div>`;
            btn.disabled = false;
            document.getElementById('btnIcon').textContent  = accionActual === 'entrada' ? '🟢' : '🔴';
            document.getElementById('btnLabel').textContent = accionActual === 'entrada' ? 'Registrar Entrada' : 'Registrar Salida';
        }
    } catch(e) {
        document.getElementById('alertMsg').innerHTML =
            '<div class="alert-box alert-error">❌ Error de conexión. Intenta de nuevo.</div>';
        btn.disabled = false;
    }
}

// ── Inicio ─────────────────────────────────────────────────
obtenerGPS();
</script>
"""
