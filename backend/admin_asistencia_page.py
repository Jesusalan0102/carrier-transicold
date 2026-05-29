"""
FRAGMENTO para reemplazar la función asistencia_admin() en tu main.py
(o donde tengas definida la ruta /app/asistencia).

Reemplaza el bloque que define esa función y el contenido HTML
por este fragmento completo.
"""

# ─── Dentro de main.py ────────────────────────────────────────────────────────

ASISTENCIA_ADMIN_CONTENIDO = """
<script>if (window.role !== 'admin' && window.role !== 'visor') { window.location.href = '/app/mis-tareas'; }</script>

<style>
/* ── Tarjetas resumen ── */
.asis-kpi { background:white; border-radius:14px; padding:18px 20px; text-align:center; border-top:4px solid #0057A8; box-shadow:0 4px 16px rgba(0,43,91,0.08); }
.asis-kpi .num { font-size:2rem; font-weight:800; color:#002B5B; }
.asis-kpi .lbl { font-size:0.72rem; color:#6b7280; font-weight:600; text-transform:uppercase; letter-spacing:0.5px; margin-top:4px; }

/* ── Tabla de asistencia con entrada/salida ── */
.tabla-asis { width:100%; border-collapse:collapse; font-size:0.83rem; }
.tabla-asis th { background:linear-gradient(135deg,#002B5B,#0057A8); color:white; padding:10px 12px; text-align:left; white-space:nowrap; }
.tabla-asis td { padding:10px 12px; border-bottom:1px solid #f0f0f0; vertical-align:middle; }
.tabla-asis tbody tr:hover td { background:#f5f9ff; }
.chip { display:inline-flex; align-items:center; gap:5px; padding:4px 10px; border-radius:20px; font-size:0.75rem; font-weight:600; }
.chip.entrada { background:#dcfce7; color:#166534; }
.chip.salida  { background:#dbeafe; color:#1e40af; }
.chip.ausente { background:#fee2e2; color:#991b1b; }
.chip.retardo { background:#fef9c3; color:#854d0e; }
.chip.ok      { background:#f0fdf4; color:#16a34a; }
</style>

<!-- KPIs -->
<div id="kpiAsistencia" style="display:grid;grid-template-columns:repeat(4,1fr);gap:16px;margin-bottom:24px;"></div>

<!-- Configuración de ubicación -->
<div class="checkin-card" style="background:white;border-radius:16px;padding:22px;box-shadow:0 4px 16px rgba(0,43,91,0.08);margin-bottom:24px;">
    <div style="font-weight:700;color:#002B5B;margin-bottom:16px;font-size:0.95rem;">⚙️ Configuración de ubicación y QR</div>
    <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px;margin-bottom:14px;">
        <div><label style="font-size:0.78rem;color:#6b7280;font-weight:600;">Latitud</label><input type="number" id="latFija" step="0.000001" value="32.5027"></div>
        <div><label style="font-size:0.78rem;color:#6b7280;font-weight:600;">Longitud</label><input type="number" id="lonFija" step="0.000001" value="-117.0037"></div>
        <div><label style="font-size:0.78rem;color:#6b7280;font-weight:600;">Radio (m)</label><input type="number" id="radioMetros" value="200" min="10" max="5000"></div>
    </div>
    <div style="display:flex;gap:10px;flex-wrap:wrap;">
        <button class="btn-primary" style="width:auto;" onclick="guardarConfiguracion()">💾 Guardar</button>
        <button class="btn-primary" style="width:auto;background:#0057A8;" onclick="generarQR()">🔄 Generar QR</button>
        <button class="btn-warning" style="width:auto;" onclick="usarUbicacionActual()">📍 Mi ubicación</button>
    </div>
    <div id="qrSection" style="display:none;margin-top:20px;padding-top:20px;border-top:1px solid #e5e7eb;">
        <div style="display:flex;gap:28px;align-items:flex-start;flex-wrap:wrap;">
            <div style="background:#f8fafc;padding:20px;border-radius:14px;text-align:center;">
                <div id="qrCanvas"></div>
                <p style="color:#16a34a;font-weight:600;font-size:0.82rem;margin-top:10px;">✅ QR permanente</p>
                <button class="btn-primary" style="width:auto;font-size:0.82rem;padding:8px 16px;margin-top:6px;" onclick="generarQR()">🔄 Regenerar</button>
            </div>
            <div style="flex:1;">
                <p><b>Lat:</b> <span id="qrLatLabel"></span></p>
                <p><b>Lon:</b> <span id="qrLonLabel"></span></p>
                <p><b>Radio:</b> <span id="qrRadioLabel"></span> m</p>
                <div id="mapaLink" style="margin-top:8px;"></div>
            </div>
        </div>
    </div>
</div>

<!-- Filtros y tabla -->
<div style="display:flex;gap:12px;margin-bottom:16px;flex-wrap:wrap;align-items:flex-end;">
    <div><label style="font-size:0.78rem;color:#6b7280;font-weight:600;display:block;margin-bottom:4px;">Fecha</label><input type="date" id="fechaFiltro" onchange="cargarRegistros()"></div>
    <div><label style="font-size:0.78rem;color:#6b7280;font-weight:600;display:block;margin-bottom:4px;">Técnico</label><input type="text" id="filtroTecnico" placeholder="Todos" style="width:160px;" oninput="filtrarTabla()"></div>
    <button class="btn-primary" style="width:auto;" onclick="cargarRegistros()">🔄 Actualizar</button>
    <button class="btn-success" style="width:auto;" onclick="exportarCSV()">📥 Exportar CSV</button>
</div>

<div style="background:white;border-radius:16px;box-shadow:0 4px 16px rgba(0,43,91,0.08);overflow:hidden;">
    <div style="overflow-x:auto;" id="tablaAsistencia">
        <p style="padding:20px;color:#6b7280;">Selecciona una fecha para ver los registros.</p>
    </div>
</div>

<script src="https://cdn.jsdelivr.net/npm/qrcodejs@1.0.0/qrcode.min.js"></script>
<script>
const fetchAuth = window.fetchAuth;
let todosRegistros = [];

// ── Fecha de hoy por defecto ──────────────────────────────────────────────
document.getElementById('fechaFiltro').value = new Date().toLocaleDateString('sv-SE', {timeZone:'America/Tijuana'});
cargarConfiguracion();
cargarRegistros();

// ── Configuración ─────────────────────────────────────────────────────────
async function cargarConfiguracion() {
    const res = await fetchAuth('/api/asistencia/configuracion');
    if (res.ok) {
        const c = await res.json();
        document.getElementById('latFija').value     = c.lat_fija;
        document.getElementById('lonFija').value     = c.lon_fija;
        document.getElementById('radioMetros').value = c.radio_metros;
    }
}

async function guardarConfiguracion() {
    await fetchAuth('/api/asistencia/configuracion', {
        method: 'POST', headers: {'Content-Type':'application/json'},
        body: JSON.stringify({
            lat_fija:     parseFloat(document.getElementById('latFija').value),
            lon_fija:     parseFloat(document.getElementById('lonFija').value),
            radio_metros: parseInt(document.getElementById('radioMetros').value)
        })
    });
    const t = document.createElement('div');
    t.style.cssText='position:fixed;bottom:28px;left:50%;transform:translateX(-50%);background:#16a34a;color:white;padding:12px 24px;border-radius:50px;font-weight:600;z-index:999;';
    t.textContent = '✅ Configuración guardada';
    document.body.appendChild(t);
    setTimeout(()=>t.remove(), 2500);
}

function usarUbicacionActual() {
    navigator.geolocation.getCurrentPosition(pos => {
        document.getElementById('latFija').value = pos.coords.latitude.toFixed(6);
        document.getElementById('lonFija').value = pos.coords.longitude.toFixed(6);
    });
}

async function generarQR() {
    await guardarConfiguracion();
    const res = await fetchAuth('/api/asistencia/generar-qr');
    const data = await res.json();
    const canvas = document.getElementById('qrCanvas');
    canvas.innerHTML = '';
    new QRCode(canvas, {
        text: data.qr_url, width: 200, height: 200,
        colorDark: '#002B5B', colorLight: '#ffffff', correctLevel: QRCode.CorrectLevel.L
    });
    document.getElementById('qrLatLabel').textContent   = data.config.lat_fija;
    document.getElementById('qrLonLabel').textContent   = data.config.lon_fija;
    document.getElementById('qrRadioLabel').textContent = data.config.radio_metros;
    document.getElementById('mapaLink').innerHTML =
        `<a href="https://www.google.com/maps?q=${data.config.lat_fija},${data.config.lon_fija}" target="_blank" style="color:#0057A8;">🗺 Ver en Google Maps</a>`;
    document.getElementById('qrSection').style.display = 'block';
}

// ── Registros ─────────────────────────────────────────────────────────────
async function cargarRegistros() {
    const fecha = document.getElementById('fechaFiltro').value;
    document.getElementById('tablaAsistencia').innerHTML = '<p style="padding:20px;color:#6b7280;">Cargando...</p>';
    const res = await fetchAuth('/api/asistencia/registros' + (fecha ? '?fecha=' + fecha : ''));
    if (!res.ok) { document.getElementById('tablaAsistencia').innerHTML='<p style="padding:20px;color:red;">Error al cargar.</p>'; return; }
    todosRegistros = await res.json();
    renderTabla(todosRegistros);
    calcularKPIs(todosRegistros);
}

function filtrarTabla() {
    const filtro = document.getElementById('filtroTecnico').value.toLowerCase();
    const filtrados = todosRegistros.filter(r => r.username.toLowerCase().includes(filtro));
    renderTabla(filtrados);
}

function renderTabla(registros) {
    if (!registros.length) {
        document.getElementById('tablaAsistencia').innerHTML = '<p style="padding:20px;color:#6b7280;">Sin registros para esta fecha.</p>';
        return;
    }

    // Agrupar por técnico
    const porTecnico = {};
    registros.forEach(r => {
        if (!porTecnico[r.username]) porTecnico[r.username] = { entrada: null, salida: null };
        if (r.tipo === 'entrada') porTecnico[r.username].entrada = r;
        else if (r.tipo === 'salida') porTecnico[r.username].salida = r;
    });

    let html = `<table class="tabla-asis">
        <thead><tr>
            <th>Técnico</th>
            <th>Entrada</th>
            <th>Retardo</th>
            <th>Salida</th>
            <th>Horas trabajadas</th>
            <th>GPS Entrada</th>
            <th>GPS Salida</th>
        </tr></thead><tbody>`;

    Object.entries(porTecnico).sort((a,b)=>a[0].localeCompare(b[0])).forEach(([username, {entrada, salida}]) => {
        // Calcular horas trabajadas
        let horasTrabajadas = '—';
        if (entrada && salida) {
            const eMin = hhmm2min(entrada.hora_checkin);
            const sMin = hhmm2min(salida.hora_checkin);
            const total = Math.max(0, sMin - eMin);
            horasTrabajadas = `${Math.floor(total/60)}h ${total%60}m`;
        }

        const retardoChip = entrada && entrada.retardo_min > 0
            ? `<span class="chip retardo">+${entrada.retardo_min} min</span>`
            : (entrada ? '<span class="chip ok">A tiempo</span>' : '—');

        const gpsEntrada = entrada
            ? (entrada.aprobado
                ? `<span class="chip ok">✓ ${entrada.distancia_metros ? Math.round(entrada.distancia_metros)+'m' : 'OK'}</span>`
                : `<span class="chip ausente">✗ ${entrada.distancia_metros ? Math.round(entrada.distancia_metros)+'m' : 'Fuera'}</span>`)
            : '—';

        const gpsSalida = salida
            ? (salida.aprobado
                ? `<span class="chip ok">✓ ${salida.distancia_metros ? Math.round(salida.distancia_metros)+'m' : 'OK'}</span>`
                : `<span class="chip ausente">✗ ${salida.distancia_metros ? Math.round(salida.distancia_metros)+'m' : 'Fuera'}</span>`)
            : '—';

        html += `<tr>
            <td><b style="color:#002B5B;">${username}</b></td>
            <td>${entrada ? `<span class="chip entrada">🟢 ${entrada.hora_checkin.slice(0,5)}</span>` : '<span class="chip ausente">Sin entrada</span>'}</td>
            <td>${retardoChip}</td>
            <td>${salida ? `<span class="chip salida">🔴 ${salida.hora_checkin.slice(0,5)}</span>` : '<span style="color:#9ca3af;font-size:0.8rem;">Pendiente</span>'}</td>
            <td style="font-weight:600;color:#002B5B;">${horasTrabajadas}</td>
            <td>${gpsEntrada}</td>
            <td>${gpsSalida}</td>
        </tr>`;
    });

    html += '</tbody></table>';
    document.getElementById('tablaAsistencia').innerHTML = html;
}

function hhmm2min(hhmm) {
    if (!hhmm) return 0;
    const [h, m] = hhmm.slice(0,5).split(':').map(Number);
    return h * 60 + m;
}

function calcularKPIs(registros) {
    const tecnicos = new Set(registros.map(r => r.username));
    let conEntrada = 0, conSalida = 0, retardos = 0;
    tecnicos.forEach(u => {
        const e = registros.find(r => r.username === u && r.tipo === 'entrada');
        const s = registros.find(r => r.username === u && r.tipo === 'salida');
        if (e) conEntrada++;
        if (s) conSalida++;
        if (e && e.retardo_min > 0) retardos++;
    });

    document.getElementById('kpiAsistencia').innerHTML = `
        <div class="asis-kpi"><div class="num">${tecnicos.size}</div><div class="lbl">Técnicos registrados</div></div>
        <div class="asis-kpi" style="border-top-color:#16a34a;"><div class="num" style="color:#16a34a;">${conEntrada}</div><div class="lbl">Con entrada</div></div>
        <div class="asis-kpi" style="border-top-color:#0057A8;"><div class="num" style="color:#0057A8;">${conSalida}</div><div class="lbl">Con salida</div></div>
        <div class="asis-kpi" style="border-top-color:#d97706;"><div class="num" style="color:#d97706;">${retardos}</div><div class="lbl">Con retardo</div></div>
    `;
}

function exportarCSV() {
    const fecha = document.getElementById('fechaFiltro').value;
    const porTecnico = {};
    todosRegistros.forEach(r => {
        if (!porTecnico[r.username]) porTecnico[r.username] = { entrada: null, salida: null };
        porTecnico[r.username][r.tipo] = r;
    });

    const headers = ['Técnico','Fecha','Hora Entrada','Retardo (min)','Hora Salida','Horas Trabajadas','GPS Entrada (m)','GPS Salida (m)','Aprobado'];
    const rows = Object.entries(porTecnico).map(([u, {entrada, salida}]) => {
        let horasTrabajadas = '';
        if (entrada && salida) {
            const total = Math.max(0, hhmm2min(salida.hora_checkin) - hhmm2min(entrada.hora_checkin));
            horasTrabajadas = (total / 60).toFixed(2);
        }
        return [
            u,
            fecha,
            entrada ? entrada.hora_checkin.slice(0,5) : '',
            entrada ? entrada.retardo_min : '',
            salida  ? salida.hora_checkin.slice(0,5)  : '',
            horasTrabajadas,
            entrada && entrada.distancia_metros != null ? Math.round(entrada.distancia_metros) : '',
            salida  && salida.distancia_metros  != null ? Math.round(salida.distancia_metros)  : '',
            entrada ? (entrada.aprobado ? 'Sí' : 'No') : '',
        ];
    });

    const csv = [headers, ...rows].map(r => r.join(',')).join('\\n');
    const blob = new Blob([csv], { type: 'text/csv' });
    const url  = URL.createObjectURL(blob);
    const a = document.createElement('a'); a.href = url; a.download = `asistencia_${fecha}.csv`; a.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
}
</script>
"""

# ─── En tu main.py reemplaza asistencia_admin() por esto: ─────────────────────
ASISTENCIA_ADMIN_RUTA = """
@router.get("/app/asistencia", response_class=HTMLResponse)
async def asistencia_admin():
    contenido = ASISTENCIA_ADMIN_CONTENIDO  # importa el string de arriba
    return HTMLResponse(content=pagina_con_menu(
        "📍 Control de Asistencia",
        ASISTENCIA_STYLES + contenido,
        "asistencia"
    ))
"""
