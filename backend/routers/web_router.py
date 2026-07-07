from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter()

# ------------------------------------------------------------
# ESTILOS GLOBALES PREMIUM (botones grandes y modales con scroll)
# ------------------------------------------------------------
BASE_STYLE = """
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<style>
    :root {
        --carrier-blue: #002B5B;
        --carrier-accent: #0057A8;
        --carrier-light: #E8F0FB;
        --carrier-success: #16a34a;
        --carrier-warn: #d97706;
        --carrier-danger: #dc2626;
        --bg-page: #EEF2F9;
        --bg-page-2: #F5F7FB;
        --bg-page-3: #EAF0FB;
        --bg-surface: #ffffff;
        --bg-surface-2: #f8fafc;
        --text-primary: #1f2937;
        --text-secondary: #6b7280;
        --border-color: #e5e7eb;
        --border-color-soft: #f0f0f0;
        --shadow-soft: rgba(0,43,91,0.08);
    }
    body.theme-dark {
        --bg-page: #0b1220;
        --bg-page-2: #0e1626;
        --bg-page-3: #0c1424;
        --bg-surface: #141d2e;
        --bg-surface-2: #182338;
        --text-primary: #e5e9f0;
        --text-secondary: #9aa6b8;
        --border-color: #283854;
        --border-color-soft: #1f2c42;
        --shadow-soft: rgba(0,0,0,0.4);
        --carrier-light: #1a2b45;
    }
    * { box-sizing: border-box; font-family: 'Inter', sans-serif; }
    body {
        background: linear-gradient(135deg, var(--bg-page) 0%, var(--bg-page-2) 60%, var(--bg-page-3) 100%);
        margin: 0; padding: 0; transition: background 0.25s ease;
    }
    .sidebar {
        background: linear-gradient(180deg, var(--carrier-blue) 0%, #01418a 60%, #0056b3 100%);
        color: white; width: 21rem; height: 100vh; position: fixed;
        top: 0; left: 0; padding: 1.5rem 1rem; box-shadow: 4px 0 20px rgba(0,0,0,0.1);
        z-index: 100; overflow-y: auto; display: flex; flex-direction: column;
    }
    body.theme-dark .sidebar {
        background: linear-gradient(180deg, #060d1a 0%, #0a1830 60%, #0c2040 100%);
    }
    .main-content { margin-left: 21rem; padding: 2rem; padding-left: calc(2rem + 58px); min-height: 100vh; transition: margin-left 0.3s ease, padding-left 0.3s ease; }
    body.sidebar-hidden .main-content { padding-left: 2rem; }
    .main-header {
        font-size: 1.75rem; font-weight: 800; color: var(--carrier-blue);
        border-bottom: 3px solid var(--carrier-accent); padding-bottom: 12px; margin-bottom: 24px;
        display: flex; align-items: center; gap: 12px;
    }
    body.theme-dark .main-header { color: #cfe0ff; }
    .section-title {
        font-size: 0.92rem; font-weight: 700; color: var(--carrier-blue);
        border-left: 4px solid var(--carrier-accent); padding: 9px 14px;
        margin: 22px 0 14px 0; background: var(--bg-surface); border-radius: 0 8px 8px 0;
        box-shadow: 0 2px 8px var(--shadow-soft);
    }
    body.theme-dark .section-title { color: #cfe0ff; }
    .time-badge {
        background: var(--carrier-blue); color: white; padding: 6px 16px;
        border-radius: 24px; font-size: 0.82rem; font-weight: 600;
        box-shadow: 0 2px 8px rgba(0,43,91,0.25); display: inline-block;
    }
    .kpi-wrap { background: var(--bg-surface); border-radius: 16px; padding: 20px 22px 18px; text-align: center; box-shadow: 0 4px 20px var(--shadow-soft); border-top: 5px solid var(--carrier-accent); transition: transform 0.2s, background 0.25s; position: relative; overflow: hidden; }
    .kpi-wrap::after { content: ''; position: absolute; top: 0; right: 0; width: 60px; height: 60px; background: rgba(0,87,168,0.04); border-radius: 0 0 0 60px; }
    .kpi-wrap:hover { transform: translateY(-3px); box-shadow: 0 8px 28px var(--shadow-soft); }
    .kpi-wrap.green  { border-top-color: var(--carrier-success); }
    .kpi-wrap.amber  { border-top-color: var(--carrier-warn); }
    .kpi-wrap.red    { border-top-color: var(--carrier-danger); }
    .kpi-wrap.purple { border-top-color: #7c3aed; }
    .kpi-num { font-size: 2.4rem; font-weight: 800; line-height: 1.1; color: var(--text-primary); }
    .kpi-wrap.green  .kpi-num { color: var(--carrier-success); }
    .kpi-wrap.amber  .kpi-num { color: var(--carrier-warn); }
    .kpi-wrap.red    .kpi-num { color: var(--carrier-danger); }
    .kpi-wrap.purple .kpi-num { color: #7c3aed; }
    .kpi-lbl { font-size: 0.73rem; color: var(--text-secondary); font-weight: 600; text-transform: uppercase; letter-spacing: 0.6px; margin-top: 6px; }
    .nav-item { display: block; padding: 12px 16px; border-radius: 8px; color: #e0eaff; font-weight: 600; margin-bottom: 6px; text-decoration: none; transition: background 0.2s; }
    .nav-item:hover, .nav-item.active { background: rgba(255,255,255,0.15); color: white; }
    .btn-primary { background: linear-gradient(135deg, var(--carrier-blue) 0%, var(--carrier-accent) 100%); color: white; border: none; border-radius: 10px; padding: 14px 20px; font-weight: 600; font-size: 1rem; cursor: pointer; transition: transform 0.2s, box-shadow 0.2s; width: 100%; text-align: center; }
    .btn-primary:hover { transform: translateY(-2px); box-shadow: 0 6px 16px rgba(0,43,91,0.3); }
    .btn-danger { background: var(--carrier-danger); color: white; border: none; border-radius: 10px; padding: 14px 20px; font-weight: 600; font-size: 1rem; cursor: pointer; width: 100%; text-align: center; }
    .btn-success { background: var(--carrier-success); color: white; border: none; border-radius: 10px; padding: 14px 20px; font-weight: 600; font-size: 1rem; cursor: pointer; width: 100%; text-align: center; }
    .btn-warning { background: var(--carrier-warn); color: white; border: none; border-radius: 10px; padding: 14px 20px; font-weight: 600; font-size: 1rem; cursor: pointer; width: 100%; text-align: center; }
    input, textarea, select { border: 1px solid var(--border-color); border-radius: 10px; padding: 12px; font-size: 16px; transition: border-color 0.2s; width: 100%; margin-bottom: 12px; background: var(--bg-surface); color: var(--text-primary); }
    input:focus, textarea:focus, select:focus { outline: none; border-color: var(--carrier-accent); box-shadow: 0 0 0 3px rgba(0,87,168,0.1); }
    table { width: 100%; border-collapse: collapse; background: var(--bg-surface); border-radius: 12px; overflow: hidden; box-shadow: 0 4px 12px var(--shadow-soft); }
    th { background: var(--bg-surface-2); padding: 12px; text-align: left; font-weight: 600; color: var(--carrier-blue); border-bottom: 2px solid var(--border-color); }
    body.theme-dark th { color: #cfe0ff; }
    td { padding: 12px; border-bottom: 1px solid var(--border-color-soft); color: var(--text-primary); }
    .badge { display: inline-block; padding: 4px 12px; border-radius: 20px; font-size: 0.75rem; font-weight: 600; }
    .bloqueo-card { background: #fef2f2; border: 1.5px solid #fca5a5; border-left: 5px solid var(--carrier-danger); border-radius: 10px; padding: 14px 18px; margin: 8px 0; }
    .evidencia-info { background: #eff6ff; border: 1px solid #bfdbfe; border-left: 5px solid #3b82f6; border-radius: 10px; padding: 12px 18px; margin-bottom: 14px; }
    .inv-info-bar { background: linear-gradient(90deg, var(--carrier-blue) 0%, var(--carrier-accent) 100%); color: white; padding: 14px 20px; border-radius: 12px; font-weight: 600; margin-bottom: 16px; display: flex; align-items: center; gap: 10px; }
    .tv-field-badge { background: var(--carrier-light); border: 1px solid #c3d4f0; border-radius: 8px; padding: 6px 12px; font-size: 0.82rem; color: var(--carrier-blue); font-weight: 600; display: inline-block; margin-bottom: 8px; }
    body.theme-dark .tv-field-badge { color: #cfe0ff; border-color: #2c4570; }
    /* Visor: ocultar botones de acción */
    body.visor-mode .btn-primary,
    body.visor-mode .btn-danger,
    body.visor-mode .btn-success,
    body.visor-mode .btn-warning,
    body.visor-mode button:not(.logout-btn):not(.hamburger):not(.theme-toggle) { display: none !important; }
    body.visor-mode input, body.visor-mode select, body.visor-mode textarea { pointer-events: none; background: var(--bg-surface-2); }
    body.visor-mode .admin-only { display: none !important; }
    .visor-banner { background: #fef3c7; border: 1px solid #f59e0b; color: #92400e; padding: 8px 16px; border-radius: 8px; font-size: 0.82rem; font-weight: 600; text-align: center; margin-bottom: 16px; }
    .login-card { background: white; padding: 36px 40px; border-radius: 20px; box-shadow: 0 12px 40px rgba(0,43,91,0.18); border: 1px solid #e2e8f2; }
    .user-chip { background: rgba(255,255,255,0.12); border: 1px solid rgba(255,255,255,0.22); border-radius: 50px; padding: 6px 14px; color: white; font-size: 0.82rem; font-weight: 500; display: inline-block; margin-top: 4px; }
    .logout-btn { background: rgba(220,38,38,0.25); border: 1px solid rgba(220,38,38,0.5); padding: 14px 20px; border-radius: 10px; color: white; font-weight: 600; font-size: 1rem; cursor: pointer; display: flex; align-items: center; justify-content: center; gap: 8px; width: 100%; transition: background 0.2s; flex-shrink: 0; }
    .logout-btn:hover { background: rgba(220,38,38,0.45); }
    .modal { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.5); display: none; justify-content: center; align-items: center; z-index: 200; }
    .modal-content { background: var(--bg-surface); color: var(--text-primary); padding: 24px; border-radius: 16px; width: 90%; max-width: 500px; max-height: 80vh; overflow-y: auto; box-shadow: 0 12px 40px rgba(0,0,0,0.2); }
    .modal-content input { margin-bottom: 10px; }
    .modal-content .btn-primary, .modal-content .btn-danger, .modal-content .btn-success { margin-top: 8px; }
    .hamburger {
        display: flex; position: fixed; top: 14px; left: 14px; z-index: 300;
        background: var(--carrier-blue); color: white; border: none; border-radius: 10px;
        width: 44px; height: 44px; font-size: 1.3rem; cursor: pointer;
        box-shadow: 0 4px 12px rgba(0,43,91,0.35); align-items: center; justify-content: center;
        transition: left 0.3s ease;
    }
    .hamburger.sidebar-open { left: calc(21rem + 14px); }
    .overlay { display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.45); z-index: 99; }
    .sidebar { transition: transform 0.3s ease; }
    body.sidebar-hidden .sidebar { transform: translateX(-100%); }
    body.sidebar-hidden .main-content { margin-left: 0; padding-top: 4rem; }
    body.sidebar-hidden .hamburger { left: 14px; }

    /* ── Toggle de tema (sol/luna) ─────────────────────────────────────── */
    .theme-toggle {
        background: rgba(255,255,255,0.12); border: 1px solid rgba(255,255,255,0.22);
        color: white; border-radius: 10px; padding: 10px 14px; font-size: 0.85rem;
        font-weight: 600; cursor: pointer; width: 100%; display: flex; align-items: center;
        justify-content: center; gap: 8px; margin-bottom: 10px; transition: background 0.2s;
    }
    .theme-toggle:hover { background: rgba(255,255,255,0.2); }

    @media (max-width: 900px) {
        .main-header { font-size: 1.2rem; }
        .kpi-num { font-size: 1.6rem; }
        .sidebar { width: 80vw; max-width: 300px; transform: translateX(-100%); }
        .sidebar.open { transform: translateX(0); }
        .main-content { margin-left: 0; padding: 1rem; padding-top: 4rem; }
        .overlay.open { display: block; }
        .hamburger { left: 14px !important; }
        body.sidebar-hidden .main-content { padding-top: 4rem; }
    }
</style>
"""

# ------------------------------------------------------------
# FUNCIÓN AUXILIAR CON SIDEBAR, MENÚ Y CIERRE DE SESIÓN SIEMPRE VISIBLE
# ------------------------------------------------------------
def pagina_con_menu(titulo: str, contenido: str, pagina_activa: str = "", extra_scripts: str = "") -> str:
    return f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{titulo} – Carrier Transicold</title>
        <!-- PWA / iOS meta tags -->
        <link rel="manifest" href="/static/manifest.json">
        <meta name="theme-color" content="#002B5B">
        <meta name="mobile-web-app-capable" content="yes">
        <meta name="apple-mobile-web-app-capable" content="yes">
        <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
        <meta name="apple-mobile-web-app-title" content="Carrier">
        <link rel="apple-touch-icon" href="/static/icons/icon-192.png">
        <link rel="apple-touch-icon" sizes="152x152" href="/static/icons/icon-152.png">
        <link rel="apple-touch-icon" sizes="192x192" href="/static/icons/icon-192.png">
        {BASE_STYLE}
        <script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>
        <script>
            window.token = localStorage.getItem('access_token');
            window.role = localStorage.getItem('role');
            window.username = localStorage.getItem('username');
            if (!window.token) {{
                window.location.href = '/app';
            }}

            window.fetchAuth = async (url, options) => {{
                options = options || {{}};
                const headers = options.headers || {{}};
                headers['Authorization'] = 'Bearer ' + window.token;
                const res = await fetch(url, {{ ...options, headers }});
                if (res.status === 401) {{
                    localStorage.clear();
                    window.location.href = '/app';
                }}
                return res;
            }};
        </script>
    </head>
    <body>
        <button class="hamburger" id="hambBtn" onclick="toggleSidebar()">☰</button>
        <div class="overlay" id="overlay" onclick="toggleSidebar()"></div>
        <div class="sidebar" id="sidebar">
            <div style="text-align:center; margin-bottom:24px;">
                <img src="https://raw.githubusercontent.com/Jesusalan0102/app-escaneo-series/main/carrierlogo.jpg" style="width:150px; border-radius:8px;">
                <p style="color:#c3d4f0; font-size:0.8rem; margin-top:4px;">Sistema Operativo</p>
            </div>
            <div style="margin-bottom:20px;padding:14px 12px;background:rgba(255,255,255,0.07);border-radius:14px;">
                <!-- Foto de perfil -->
                <div style="display:flex;align-items:center;gap:12px;">
                    <div style="position:relative;flex-shrink:0;">
                        <img id="sidebarFoto"
                            src=""
                            style="width:52px;height:52px;border-radius:50%;object-fit:cover;border:2px solid rgba(255,255,255,0.35);display:none;">
                        <div id="sidebarFotoPlaceholder"
                            style="width:52px;height:52px;border-radius:50%;background:rgba(255,255,255,0.15);display:flex;align-items:center;justify-content:center;font-size:1.5rem;border:2px solid rgba(255,255,255,0.25);">👤</div>
                    </div>
                    <div style="min-width:0;">
                        <p style="font-weight:700;margin:0;font-size:0.95rem;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;" id="sidebarUser"></p>
                        <span id="sidebarPuesto" style="font-size:0.72rem;color:#a8c4e8;font-weight:500;display:block;margin-top:2px;"></span>
                        <span id="sidebarRole" class="user-chip" style="margin-top:5px;display:inline-block;"></span>
                    </div>
                </div>
            </div>
            <hr style="border-color:rgba(255,255,255,0.2);">
            <nav style="margin-top:12px; flex:1;" id="navMenu"></nav>
            <div style="margin-top:auto; padding-top:16px; border-top:1px solid rgba(255,255,255,0.2);">
                <button class="theme-toggle" id="themeToggleBtn" onclick="toggleTheme()">
                    <span id="themeToggleIcon">🌙</span> <span id="themeToggleLabel">Modo oscuro</span>
                </button>
                <button onclick="logout()" class="logout-btn">🚪 Cerrar Sesión</button>
            </div>
        </div>

        <div class="main-content">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:24px; flex-wrap:wrap; gap:12px;">
                <h1 class="main-header">{titulo}</h1>
                <div id="liveClock" class="time-badge"></div>
            </div>
            <div id="visorBanner" style="display:none" class="visor-banner">👁 Modo solo lectura — No tienes permisos para editar</div>
            <script>if(window.role==='visor') document.getElementById('visorBanner').style.display='block';</script>
            {contenido}
        </div>


        <script>
            document.addEventListener('DOMContentLoaded', function() {{
                if (window.role === 'visor') {{ document.body.classList.add('visor-mode'); }}
                document.getElementById('sidebarUser').textContent = window.username;
                const roleLabels = {{ admin: '🛡 Administrador', tecnico: '🔧 Técnico', visor: '👁 Visor' }};
                document.getElementById('sidebarRole').textContent = roleLabels[window.role] || window.role;

                // Cargar foto y puesto del usuario en sesión (funciona para cualquier rol)
                (async () => {{
                    try {{
                        const res = await window.fetchAuth('/api/usuarios/me');
                        if (!res.ok) return;
                        const yo = await res.json();
                        if (yo.puesto) {{
                            document.getElementById('sidebarPuesto').textContent = yo.puesto;
                        }}
                        if (yo.foto_url) {{
                            const img = document.getElementById('sidebarFoto');
                            const ph  = document.getElementById('sidebarFotoPlaceholder');
                            img.src = yo.foto_url;
                            img.style.display = 'block';
                            if (ph) ph.style.display = 'none';
                        }}
                    }} catch(e) {{}}
                }})();

                const adminMenu = [
                    {{ href: '/app/dashboard', label: '📊 Dashboard Ejecutivo' }},
                    {{ href: '/app/asignaciones', label: '🎯 Control de Asignaciones' }},
                    {{ href: '/app/tickets', label: '🎫 Tickets' }},
                    {{ href: '/app/inventario', label: '📦 Inventarios' }},
                    {{ href: '/app/unidades', label: '📸 Registro de Unidades' }},
                    {{ href: '/app/usuarios', label: '👥 Gestión de Usuarios' }},
                    {{ href: '/app/cluster', label: '⚡ Asignación por Cluster' }},
                    {{ href: '/app/asistencia', label: '📍 Control de Asistencia' }},
                    {{ href: '/app/checkin', label: '🕐 Registrar Mi Asistencia' }},
                    {{ href: '/app/alarmas', label: '🔔 Alarm Troubleshooting' }},
                    {{ href: '/app/admin', label: '🛠 Panel de Administración' }},
                ];
                const visorMenu = [
                    {{ href: '/app/dashboard', label: '📊 Dashboard Ejecutivo' }},
                    {{ href: '/app/asignaciones', label: '🎯 Control de Asignaciones' }},
                    {{ href: '/app/tickets', label: '🎫 Tickets' }},
                    {{ href: '/app/inventario', label: '📦 Inventarios' }},
                    {{ href: '/app/unidades', label: '📸 Registro de Unidades' }},
                    {{ href: '/app/usuarios', label: '👥 Gestión de Usuarios' }},
                    {{ href: '/app/asistencia', label: '📍 Control de Asistencia' }},
                    {{ href: '/app/alarmas', label: '🔔 Alarm Troubleshooting' }},
                ];
                const techMenu = [
                    {{ href: '/app/mis-tareas', label: '🎯 Mis Tareas' }},
                    {{ href: '/app/solicitud', label: '🔔 Nueva Solicitud' }},
                    {{ href: '/app/mis-tickets', label: '🎫 Mis Tickets' }},
                    {{ href: '/app/checkin', label: '📍 Registrar Asistencia' }},
                ];
                const menu = window.role === 'admin' ? adminMenu : (window.role === 'visor' ? visorMenu : techMenu);
                let navHtml = '';
                menu.forEach(item => {{
                    const active = item.href === '/app/{pagina_activa}' ? ' active' : '';
                    navHtml += `<a href="${{item.href}}" class="nav-item${{active}}" onclick="if(window.innerWidth<=900)toggleSidebar()">${{item.label}}</a>`;
                }});
                document.getElementById('navMenu').innerHTML = navHtml;
            }});

            // ── Modo oscuro persistente ─────────────────────────────────────
            function applyTheme(mode) {{
                document.body.classList.toggle('theme-dark', mode === 'dark');
                const icon  = document.getElementById('themeToggleIcon');
                const label = document.getElementById('themeToggleLabel');
                if (icon)  icon.textContent  = mode === 'dark' ? '☀️' : '🌙';
                if (label) label.textContent = mode === 'dark' ? 'Modo claro' : 'Modo oscuro';
            }}
            function toggleTheme() {{
                const next = document.body.classList.contains('theme-dark') ? 'light' : 'dark';
                localStorage.setItem('theme', next);
                applyTheme(next);
            }}
            applyTheme(localStorage.getItem('theme') === 'dark' ? 'dark' : 'light');

            function toggleSidebar() {{
                const sidebar = document.getElementById('sidebar');
                const overlay = document.getElementById('overlay');
                const btn = document.getElementById('hambBtn');
                if (window.innerWidth <= 900) {{
                    // Mobile: toggle clase open en el sidebar
                    sidebar.classList.toggle('open');
                    overlay.classList.toggle('open');
                }} else {{
                    // Desktop: toggle clase sidebar-hidden en body
                    document.body.classList.toggle('sidebar-hidden');
                    btn.classList.toggle('sidebar-open');
                    localStorage.setItem('sidebarHidden', document.body.classList.contains('sidebar-hidden') ? '1' : '0');
                }}
            }}

            // Restaurar estado del sidebar en desktop al cargar
            if (window.innerWidth > 900) {{
                if (localStorage.getItem('sidebarHidden') === '1') {{
                    document.body.classList.add('sidebar-hidden');
                }} else {{
                    document.getElementById('hambBtn').classList.add('sidebar-open');
                }}
            }}

            function logout() {{
                localStorage.clear();
                window.location.href = '/app';
            }}

            function actualizarReloj() {{
                const ahora = new Date();
                const opciones = {{ timeZone: 'America/Tijuana', hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' }};
                document.getElementById('liveClock').textContent = '🕒 Tijuana ' + ahora.toLocaleTimeString('es-MX', opciones);
            }}
            actualizarReloj();
            setInterval(actualizarReloj, 1000);

            // ── Renovación automática de token (refresh) ──────────────────
            async function _refreshToken() {{
                try {{
                    const t = window.token || localStorage.getItem('access_token');
                    if (!t) return null;
                    const res = await fetch('/api/auth/refresh', {{
                        method: 'POST',
                        headers: {{ 'Authorization': 'Bearer ' + t }}
                    }});
                    if (res.ok) {{
                        const data = await res.json();
                        window.token = data.access_token;
                        localStorage.setItem('access_token', data.access_token);
                        return data.access_token;
                    }}
                }} catch(e) {{ console.error("Error renovando token:", e); }}
                return null;
            }}
            // Renovar cada 25 minutos
            setInterval(_refreshToken, 25 * 60 * 1000);

            // ── Sistema de sonidos via Web Audio API ───────────────────
            const AudioCtx = window.AudioContext || window.webkitAudioContext;
            let _actx = null;
            function _getCtx() {{ if (!_actx) _actx = new AudioCtx(); return _actx; }}

            function _playTone(freqs, dur, waveType, vol) {{
                dur = dur||0.18; waveType = waveType||'sine'; vol = vol||0.35;
                try {{
                    const ctx = _getCtx();
                    freqs.forEach(function(f, i) {{
                        const osc = ctx.createOscillator();
                        const gain = ctx.createGain();
                        osc.connect(gain); gain.connect(ctx.destination);
                        osc.type = waveType;
                        osc.frequency.setValueAtTime(f, ctx.currentTime + i*dur);
                        gain.gain.setValueAtTime(vol, ctx.currentTime + i*dur);
                        gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + i*dur + dur);
                        osc.start(ctx.currentTime + i*dur);
                        osc.stop(ctx.currentTime + (i+1)*dur);
                    }});
                }} catch(e) {{}}
            }}

            const _SOUNDS = {{
                solicitud_nueva:      function(){{ _playTone([660,880],0.15,'sine',0.4); }},
                asignacion_nueva:     function(){{ _playTone([523,659,784],0.14,'triangle',0.35); }},
                solicitud_aprobada:   function(){{ _playTone([784,988,1047],0.13,'sine',0.3); }},
                actividad_iniciada:   function(){{ _playTone([440,554],0.16,'triangle',0.3); }},
                actividad_completada: function(){{ _playTone([523,659,784,1047],0.12,'sine',0.4); }},
                ticket_nuevo:         function(){{ _playTone([330,262,220],0.2,'sawtooth',0.25); }},
            }};
            const _LABELS = {{
                solicitud_nueva:      'Solicitud de actividad',
                asignacion_nueva:     'Actividad asignada',
                solicitud_aprobada:   'Solicitud aprobada',
                actividad_iniciada:   'Actividad iniciada',
                actividad_completada: 'Actividad completada',
                ticket_nuevo:         'Nuevo ticket creado',
            }};
            const _ICONS = {{
                solicitud_nueva:'&#x1F4CB;', asignacion_nueva:'&#x2705;',
                solicitud_aprobada:'&#x1F44D;', actividad_iniciada:'&#x25B6;&#xFE0F;',
                actividad_completada:'&#x1F3C1;', ticket_nuevo:'&#x1F3AB;',
            }};

            function _showToast(evType, payload) {{
                const label = _LABELS[evType] || evType;
                const icon  = _ICONS[evType]  || '';
                const t = document.createElement('div');
                t.style.cssText = 'position:fixed;bottom:24px;right:24px;background:#1F4E78;color:#fff;'
                    + 'padding:12px 18px;border-radius:10px;font-size:13px;font-family:Arial,sans-serif;'
                    + 'z-index:9999;box-shadow:0 4px 16px rgba(0,0,0,.35);max-width:280px;'
                    + 'line-height:1.4;opacity:0;transition:opacity .25s';
                var extra = (payload && (payload.unidad || payload.unit_number || payload.tecnico))
                    ? '<br><span style="opacity:.75;font-size:11px">'
                        + (payload.unidad || payload.unit_number || '')
                        + (payload.tecnico ? ' &middot; ' + payload.tecnico : '')
                        + '</span>'
                    : '';
                t.innerHTML = icon + ' <strong>' + label + '</strong>' + extra;
                document.body.appendChild(t);
                requestAnimationFrame(function(){{ t.style.opacity = '1'; }});
                setTimeout(function(){{ t.style.opacity = '0'; setTimeout(function(){{ t.remove(); }}, 300); }}, 4500);
            }}

            // Desbloquear AudioContext al primer click del usuario
            document.addEventListener('click', function(){{ try{{ _getCtx().resume(); }}catch(e){{}} }}, {{once:true}});

            // ── Conexión WebSocket con reconexión y token siempre actualizado ──
            function _connectWS() {{
                try {{
                    const tokenValido = window.token || localStorage.getItem('access_token');
                    if (!tokenValido || tokenValido === 'null' || tokenValido === 'undefined') {{
                        console.warn("WebSocket pausado de forma segura: Esperando inicio de sesión.");
                        return;
                    }}
                    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
                    const wsUrl = protocol + '//' + window.location.host + '/ws?token=' + encodeURIComponent(tokenValido);
                    const socket = new WebSocket(wsUrl);

                    socket.onmessage = function(ev) {{
                        try {{
                            const d = JSON.parse(ev.data);
                            if (d.type && d.type !== 'status' && _SOUNDS[d.type]) {{
                                _SOUNDS[d.type]();
                                _showToast(d.type, d.payload || {{}});
                            }}
                        }} catch(e) {{}}
                    }};
                    socket.onerror = function(err) {{ console.error("WS Error detectado:", err); }};
                    socket.onclose = async function(ev) {{
                        // Si el cierre fue por token inválido/expirado, intenta renovarlo primero
                        if (ev.code === 1008) {{
                            await _refreshToken();
                        }}
                        setTimeout(_connectWS, 10000);
                    }};
                }} catch(e) {{ console.error("Error en inicialización del WS:", e); }}
            }}
            _connectWS();

            // ── FUNCIÓN ADICIONAL PARA LAS IMÁGENES ROTAS (401) ──
            window.cargarImagenAutenticada = async (urlElemento, imgElementId) => {{
                try {{
                    let token = window.token || localStorage.getItem('access_token');
                    let res = await fetch(urlElemento, {{
                        headers: {{ 'Authorization': 'Bearer ' + token }}
                    }});
                    if (res.status === 401) {{
                        token = await _refreshToken();
                        if (token) {{
                            res = await fetch(urlElemento, {{
                                headers: {{ 'Authorization': 'Bearer ' + token }}
                            }});
                        }}
                    }}
                    if(res.ok) {{
                        const blob = await res.blob();
                        document.getElementById(imgElementId).src = URL.createObjectURL(blob);
                    }}
                }} catch(e) {{ console.error("Error al transferir imagen:", e); }}
            }};


            // ── Push Notifications (segundo plano) ────────────────────────
            function _b64ToUint8(b64) {{
                var b = b64.replace(/-/g,'+').replace(/_/g,'/');
                var raw = atob(b);
                var arr = new Uint8Array(raw.length);
                for (var i=0; i<raw.length; i++) arr[i] = raw.charCodeAt(i);
                return arr;
            }}

            var _pushReady = false;
            var _vapidKey  = null;
            var _swReg     = null;

            async function _registerPushSub() {{
                if (_pushReady || !_swReg || !_vapidKey) return;
                try {{
                    var sub = await _swReg.pushManager.getSubscription();
                    if (!sub) {{
                        sub = await _swReg.pushManager.subscribe({{
                            userVisibleOnly: true,
                            applicationServerKey: _b64ToUint8(_vapidKey),
                        }});
                    }}
                    var sj = sub.toJSON();
                    var res = await window.fetchAuth('/api/push/subscribe', {{
                        method: 'POST',
                        headers: {{'Content-Type':'application/json'}},
                        body: JSON.stringify({{endpoint: sj.endpoint, keys: sj.keys}}),
                    }});
                    if (res && res.ok) _pushReady = true;
                }} catch(e) {{ console.warn('Push subscribe error:', e); }}
            }}

            async function _setupPush() {{
                if (!('serviceWorker' in navigator) || !('PushManager' in window)) return;
                try {{
                    var r = await fetch('/api/push/vapid-public-key');
                    if (!r.ok) return;
                    var d = await r.json();
                    _vapidKey = d.publicKey;
                    if (!_vapidKey) return;

                    _swReg = await navigator.serviceWorker.ready;

                    // Si ya tenemos permiso, suscribir de inmediato
                    if (Notification.permission === 'granted') {{
                        await _registerPushSub();
                        return;
                    }}
                    // Si está bloqueado, no hacer nada
                    if (Notification.permission === 'denied') return;

                    // Pedir permiso (requiere gesto del usuario)
                    var perm = await Notification.requestPermission();
                    if (perm === 'granted') await _registerPushSub();
                }} catch(e) {{ console.warn('Push setup error:', e); }}
            }}

            // Registrar SW
            if ('serviceWorker' in navigator) {{
                navigator.serviceWorker.register('/sw.js')
                    .then(function(reg) {{
                        _swReg = reg;
                        // Si ya tienen permiso concedido, suscribir sin pedir nada
                        if (Notification.permission === 'granted') {{
                            _setupPush();
                        }}
                    }})
                    .catch(function(e) {{ console.warn('SW register error:', e); }});
            }}

            // Al primer click pedir permiso si aún no está concedido/denegado
            document.addEventListener('click', function() {{
                if (Notification.permission !== 'denied') _setupPush();
            }}, {{once: true}});

            // ── Banner de instalación PWA para iOS ────────────────────────
            (function() {{
                var isIos = /iphone|ipad|ipod/i.test(navigator.userAgent);
                var isStandalone = ('standalone' in navigator) && navigator.standalone;
                var dismissed = localStorage.getItem('pwa_install_dismissed');
                if (!isIos || isStandalone || dismissed) return;

                // Mostrar banner después de 2 segundos
                setTimeout(function() {{
                    var banner = document.createElement('div');
                    banner.id = 'ios-install-banner';
                    banner.style.cssText = 'position:fixed;bottom:0;left:0;right:0;background:#002B5B;color:#fff;padding:14px 16px 20px;font-family:Arial,sans-serif;font-size:13px;z-index:99999;box-shadow:0 -4px 20px rgba(0,0,0,.4);line-height:1.5';
                    banner.innerHTML = '<div style="display:flex;justify-content:space-between;align-items:flex-start">'
                        + '<div><strong style="font-size:14px">&#x1F4F2; Instala la app para recibir notificaciones</strong>'
                        + '<br>Toca <strong>&#x1F4E4; Compartir</strong> y luego <strong>&quot;Agregar a pantalla de inicio&quot;</strong>'
                        + '<br><span style="opacity:.75;font-size:11px">Requerido en iPhone para notificaciones en segundo plano</span></div>'
                        + '<button onclick="document.getElementById(&quot;ios-install-banner&quot;).remove();localStorage.setItem(&quot;pwa_install_dismissed&quot;,&quot;1&quot;)" '
                        + 'style="background:none;border:none;color:#fff;font-size:22px;cursor:pointer;padding:0 0 0 12px;line-height:1">&times;</button>'
                        + '</div>';
                    document.body.appendChild(banner);
                }}, 2000);
            }})();
        </script>
        {extra_scripts}
    </body>
    </html>
    """

# ------------------------------------------------------------
# LOGIN
# ------------------------------------------------------------
@router.get("/app", response_class=HTMLResponse)
async def login():
    return """
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Carrier Transicold – Login</title>
        <style>
            * { box-sizing: border-box; font-family: 'Inter', system-ui, sans-serif; }
            body { background: linear-gradient(135deg, #EEF2F9 0%, #F5F7FB 60%, #EAF0FB 100%); min-height: 100vh; display: flex; align-items: center; justify-content: center; margin: 0; padding: 20px; }
            .login-card { background: white; padding: 40px 32px; border-radius: 20px; box-shadow: 0 12px 40px rgba(0,43,91,0.18); max-width: 400px; width: 100%; text-align: center; }
            .login-card img { width: 280px; max-width: 100%; border-radius: 12px; margin-bottom: 20px; }
            .login-card h2 { color: #002B5B; font-weight: 800; font-size: 1.5rem; margin-bottom: 4px; }
            .login-card p { color: #6b7280; font-size: 0.9rem; margin-bottom: 24px; }
            input { border: 1px solid #d1d5db; border-radius: 10px; padding: 12px; width: 100%; margin-bottom: 16px; font-size: 16px; transition: border-color 0.2s; }
            input:focus { outline: none; border-color: #0057A8; box-shadow: 0 0 0 3px rgba(0,87,168,0.1); }
            .btn-primary { background: linear-gradient(135deg, #002B5B 0%, #0057A8 100%); color: white; border: none; border-radius: 10px; padding: 14px; width: 100%; font-weight: 700; font-size: 1rem; cursor: pointer; transition: transform 0.2s; }
            .btn-primary:hover { transform: translateY(-2px); }
            #errorMsg { color: #dc2626; font-size: 0.85rem; min-height: 20px; }
        </style>
    </head>
    <body>
        <div class="login-card">
            <img src="https://raw.githubusercontent.com/Jesusalan0102/app-escaneo-series/main/carrierlogo.jpg">
            <h2>Sistema Operativo</h2>
            <p>Panel de Acceso</p>
            <form id="loginForm">
                <input type="text" id="username" placeholder="Usuario" required autocomplete="off">
                <input type="password" id="password" placeholder="Contraseña" required>
                <p id="errorMsg"></p>
                <button type="submit" class="btn-primary">Ingresar al Sistema</button>
            </form>
            <p style="text-align:center; font-size:0.75rem; color:#9ca3af; margin-top:16px;">© 2026 Carrier Transicold</p>
        </div>
        <script>
            document.getElementById('loginForm').addEventListener('submit', async (e) => {
                e.preventDefault();
                const username = document.getElementById('username').value.trim();
                const password = document.getElementById('password').value.trim();
                const errorEl = document.getElementById('errorMsg');
                errorEl.textContent = '';
                try {
                    const res = await fetch('/api/auth/login', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ username, password }) });
                    if (!res.ok) throw new Error('Credenciales incorrectas');
                    const data = await res.json();
                    localStorage.setItem('access_token', data.access_token);
                    localStorage.setItem('role', data.role);
                    localStorage.setItem('username', data.username);
                    window.location.href = data.role === 'tecnico' ? '/app/mis-tareas' : '/app/dashboard';
                } catch (err) { errorEl.textContent = err.message; }
            });
        </script>
    </body>
    </html>
    """

# ------------------------------------------------------------
# DASHBOARD (solo admin/visor) - TABLA DE ESTADÍSTICAS MEJORADA
# ------------------------------------------------------------
@router.get("/app/dashboard", response_class=HTMLResponse)
async def dashboard():
    contenido = """
    <script> if (window.role !== 'admin' && window.role !== 'visor') { window.location.href = '/app/mis-tareas'; } </script>
    <style>
        .status-tbl { width:100%; border-collapse:collapse; background:white; border-radius:12px; overflow:hidden; box-shadow:0 4px 12px rgba(0,43,91,0.08); font-size:0.78rem; }
        .status-tbl th { background:#002B5B; color:white; padding:8px 10px; text-align:center; font-weight:600; white-space:nowrap; border-right:1px solid #1a4a8a; }
        .status-tbl th:first-child, .status-tbl th:nth-child(2) { text-align:left; }
        .status-tbl td { padding:7px 10px; border-bottom:1px solid #f0f2f5; border-right:1px solid #f0f2f5; text-align:center; }
        .status-tbl td:first-child { font-weight:700; color:#002B5B; background:#f8fafc; text-align:left; }
        .status-tbl td:nth-child(2) { font-family:monospace; font-weight:600; text-align:left; }
        .status-tbl tbody tr:hover td { background:#eef4ff; }
        .status-tbl .check { color:#16a34a; font-size:1rem; }
        .status-tbl .dash { color:#d1d5db; }
        .status-tbl .badge-proceso {
            display:inline-flex; align-items:center; gap:3px;
            background:#fff7ed; color:#c2410c; border:1px solid #fed7aa;
            border-radius:999px; padding:2px 8px; font-size:0.68rem;
            font-weight:600; white-space:nowrap; animation:pulse-badge 2s infinite;
        }
        .status-tbl .badge-pendiente {
            display:inline-block; font-size:0.85rem; opacity:0.7;
        }
        @keyframes pulse-badge {
            0%,100% { opacity:1; } 50% { opacity:0.55; }
        }
        .lotes-wrap { border:1px solid #e5e7eb; border-radius:12px; overflow:hidden; margin-bottom:12px; }
        .lote-hdr { background:linear-gradient(90deg,#002B5B,#0057A8); color:white; padding:14px 20px; font-weight:600; cursor:pointer; display:flex; align-items:center; justify-content:space-between; }
        .lote-body { display:none; padding:16px; overflow-x:auto; background:white; }
        .kpi-grid { display:grid; grid-template-columns:repeat(5,1fr); gap:16px; margin-bottom:20px; }
        @media(max-width:900px){ .kpi-grid{grid-template-columns:repeat(2,1fr);} }
        .kpi-icon { position:absolute; top:14px; right:16px; font-size:1.3rem; opacity:0.35; }
        .alert-strip { display:flex; gap:12px; flex-wrap:wrap; margin-bottom:28px; }
        .alert-chip { display:flex; align-items:center; gap:8px; background:var(--bg-surface); border-radius:10px; padding:10px 16px; font-size:0.82rem; font-weight:600; color:var(--text-secondary); box-shadow:0 2px 8px var(--shadow-soft); border-left:4px solid #d1d5db; }
        .alert-chip.hot { border-left-color:var(--carrier-danger); color:var(--carrier-danger); }
        .alert-chip .n { font-size:1rem; font-weight:800; }
        .chart-card { background:var(--bg-surface); border-radius:16px; padding:20px; box-shadow:0 4px 12px var(--shadow-soft); min-height:380px; display:flex; flex-direction:column; }
        .chart-card-hdr { font-size:0.95rem; font-weight:700; color:var(--carrier-blue); margin-bottom:8px; }
        body.theme-dark .chart-card-hdr { color:#cfe0ff; }
        .chart-empty { flex:1; display:flex; flex-direction:column; align-items:center; justify-content:center; color:var(--text-secondary); text-align:center; gap:8px; }
        .chart-empty .ico { font-size:2rem; opacity:0.4; }
        .chart-empty .msg { font-size:0.85rem; max-width:220px; }
    </style>

    <div class="kpi-grid" id="kpiContainer"></div>
    <div class="alert-strip" id="alertStrip"></div>

    <div style="display:grid; grid-template-columns:2fr 1fr; gap:24px; margin-bottom:32px;">
        <div class="chart-card">
            <div class="chart-card-hdr">📈 Carga por técnico</div>
            <div id="barChart" style="flex:1; min-height:320px;"></div>
        </div>
        <div class="chart-card">
            <div class="chart-card-hdr">🥧 Distribución global</div>
            <div id="pieChart" style="flex:1; min-height:320px;"></div>
        </div>
    </div>

    <div class="section-title">📋 Estatus de Proceso por Unidad</div>
    <div id="statusTable" style="overflow-x:auto; margin-bottom:32px; border-radius:12px;"></div>

    <div class="section-title">📦 Lotes y Series por Unidad</div>
    <div id="lotesContainer" style="margin-bottom:32px;"></div>

    <div class="section-title admin-only">📂 Descarga de Evidencias</div>
    <div class="admin-only" style="display:flex; gap:16px; align-items:center; margin-bottom:16px; flex-wrap:wrap;">
        <select id="unidadEv" style="width:auto; flex:1; margin-bottom:0;"><option value="">Selecciona unidad</option></select>
        <button class="btn-primary" style="width:auto; padding:12px 24px;" onclick="descargarEvidencias()">📥 Descargar ZIP</button>
    </div>

    <div class="section-title admin-only">📥 Reportes</div>
    <button class="btn-primary admin-only" style="width:auto; padding:12px 28px;" onclick="descargarReporte()">📊 Descargar Reporte Maestro Excel</button>

    <script>
        const actividades = ['Cableado','Programación','Soldadura','Check de fugas','Vacío','Cerrado','Pre-viaje','Horas Corridas','Standby','GPS','Corriendo','Inspección','Accesorios','Toma de Valores','Evidencia','Toma de Series'];
        const camposSeries = {vin_number:'VIN Number',reefer_serial:'Serie Reefer',reefer_model:'Modelo Reefer',evaporator_serial_mjs11:'Evap. MJS11',evaporator_serial_mjd22:'Evap. MJD22',engine_serial:'Motor',compressor_serial:'Compresor',generator_serial:'Generador',battery_charger_serial:'Cargador Bat.'};

        async function cargarDashboard() {
            try {
                const kpisRes = await fetchAuth('/api/dashboard/kpis');
                const kpis = await kpisRes.json();
                const kpiData = [
                    {value: kpis.total_unidades, label: 'Total Unidades', cls: '',       icon:'🚚'},
                    {value: kpis.completadas,    label: 'Completadas',    cls: 'green',  icon:'✅'},
                    {value: kpis.en_proceso,     label: 'En Proceso',     cls: 'amber',  icon:'⚙️'},
                    {value: kpis.pendientes,     label: 'Pendientes',     cls: 'red',    icon:'⏳'},
                    {value: (kpis.avance||0)+'%',label: 'Avance Global',  cls: 'purple', icon:'📊'},
                ];
                document.getElementById('kpiContainer').innerHTML = kpiData.map(k =>
                    `<div class="kpi-wrap ${k.cls}"><span class="kpi-icon">${k.icon}</span><div class="kpi-num">${k.value ?? '—'}</div><div class="kpi-lbl">${k.label}</div></div>`
                ).join('');

                const alerts = [];
                if (kpis.tickets_sin_atender > 0) alerts.push({n:kpis.tickets_sin_atender, txt:'Tickets sin atender', hot:true});
                if (kpis.solicitudes_pendientes > 0) alerts.push({n:kpis.solicitudes_pendientes, txt:'Solicitudes pendientes', hot:true});
                document.getElementById('alertStrip').innerHTML = alerts.length
                    ? alerts.map(a => `<div class="alert-chip ${a.hot?'hot':''}"><span class="n">${a.n}</span> ${a.txt}</div>`).join('')
                    : `<div class="alert-chip">✔ Sin alertas pendientes</div>`;

                const [statsRes, usuariosRes] = await Promise.all([
                    fetchAuth('/api/dashboard/stats_tecnicos'),
                    fetchAuth('/api/usuarios/')
                ]);
                const statsRaw = await statsRes.json();
                const usuariosAll = await usuariosRes.json();
                const tecSet = new Set(usuariosAll.filter(u => u.role === 'tecnico').map(u => u.username));
                const stats = statsRaw.filter(s => tecSet.has(s.tecnico));

                if (stats.length > 0) {
                    Plotly.newPlot('barChart', [
                        {x: stats.map(s=>s.tecnico), y: stats.map(s=>s.completadas), type:'bar', name:'Completadas', marker:{color:'#16a34a'}},
                        {x: stats.map(s=>s.tecnico), y: stats.map(s=>s.en_curso),    type:'bar', name:'En Curso',    marker:{color:'#d97706'}},
                        {x: stats.map(s=>s.tecnico), y: stats.map(s=>s.pendientes),  type:'bar', name:'Pendientes',  marker:{color:'#dc2626'}},
                    ], {barmode:'group', paper_bgcolor:'transparent', plot_bgcolor:'transparent', font:{family:'Inter,sans-serif'}, margin:{t:10,b:80}}, {responsive:true, displaylogo:false});
                } else {
                    document.getElementById('barChart').innerHTML = '<div class="chart-empty"><div class="ico">📈</div><div class="msg">Aún no hay actividades asignadas a técnicos. Esta gráfica se llenará en cuanto empiecen a registrarse asignaciones.</div></div>';
                }

                const asigRes = await fetchAuth('/api/asignaciones/');
                const asignaciones = await asigRes.json();

                const distRes = await fetchAuth('/api/dashboard/distribucion_global');
                const cnt = await distRes.json();
                if (cnt.completada + cnt.en_proceso + cnt.pendiente > 0) {
                    Plotly.newPlot('pieChart', [{
                        values:[cnt.completada,cnt.en_proceso,cnt.pendiente],
                        labels:['Completadas','En Proceso','Pendientes'],
                        marker:{colors:['#16a34a','#d97706','#dc2626']},
                        hole:0.55, type:'pie', textinfo:'percent'
                    }], {showlegend:true, paper_bgcolor:'transparent', font:{family:'Inter,sans-serif'}, margin:{t:10,b:10,l:10,r:10}}, {responsive:true, displaylogo:false});
                } else {
                    document.getElementById('pieChart').innerHTML = '<div class="chart-empty"><div class="ico">🥧</div><div class="msg">Sin unidades procesadas todavía. En cuanto haya avance verás aquí el reparto entre completadas, en proceso y pendientes.</div></div>';
                }
                if (asignaciones.length) {
                    const unidadesRes = await fetchAuth('/api/unidades/');
                    const unidades = await unidadesRes.json();
                    if (unidades.length) {
                        // Tabla de estatus – CSS correcta
                        const compSet    = new Set(asignaciones.filter(a=>a.estado==='completada').map(a=>a.unidad+'||'+a.actividad_id));
                        const procesoSet = new Set(asignaciones.filter(a=>a.estado==='en_proceso').map(a=>a.unidad+'||'+a.actividad_id));
                        const pendSet    = new Set(asignaciones.filter(a=>a.estado==='pendiente').map(a=>a.unidad+'||'+a.actividad_id));
                        let tbl = '<table class="status-tbl"><thead><tr><th>LOTE</th><th>#Económico</th>';
                        actividades.forEach(a => { tbl += `<th>${a}</th>`; });
                        tbl += '</tr></thead><tbody>';
                        unidades.forEach(u => {
                            tbl += `<tr><td>${u.id_lote||''}</td><td>${u.unit_number}</td>`;
                            actividades.forEach(act => {
                                const key = u.unit_number+'||'+act;
                                if (compSet.has(key)) {
                                    tbl += '<td><span class="check">✔</span></td>';
                                } else if (procesoSet.has(key)) {
                                    tbl += '<td><span class="badge-proceso" title="En proceso">⚙ En proceso</span></td>';
                                } else if (pendSet.has(key)) {
                                    tbl += '<td><span class="badge-pendiente" title="Pendiente">⏳</span></td>';
                                } else {
                                    tbl += '<td><span class="dash">—</span></td>';
                                }
                            });
                            tbl += '</tr>';
                        });
                        tbl += '</tbody></table>';
                        document.getElementById('statusTable').innerHTML = tbl;

                        // Lotes y series
                        const lotesMap = {};
                        unidades.forEach(u => { const l=u.id_lote||'Sin lote'; if(!lotesMap[l]) lotesMap[l]=[]; lotesMap[l].push(u); });
                        let lotesHtml = '';
                        for (const [lote, units] of Object.entries(lotesMap)) {
                            const bodyId = 'lote_'+lote.replace(/[^a-zA-Z0-9]/g,'_');
                            lotesHtml += `<div class="lotes-wrap">
                                <div class="lote-hdr" onclick="var d=document.getElementById('${bodyId}');d.style.display=d.style.display==='block'?'none':'block';">
                                    📦 Lote: ${lote} &nbsp;<span style="opacity:.7;font-size:.8rem;">${units.length} unidades</span><span>▼</span>
                                </div>
                                <div id="${bodyId}" class="lote-body">
                                    <table style="width:100%;border-collapse:collapse;font-size:.8rem;">
                                        <thead><tr><th style="background:#002B5B;color:white;padding:8px 10px;text-align:left;">#Económico</th>
                                        ${Object.values(camposSeries).map(s=>`<th style="background:#002B5B;color:white;padding:8px 10px;text-align:left;">${s}</th>`).join('')}</tr></thead>
                                        <tbody>${units.map(u=>`<tr style="border-bottom:1px solid #f0f0f0;"><td style="padding:7px 10px;font-weight:600;">${u.unit_number}</td>${Object.keys(camposSeries).map(k=>`<td style="padding:7px 10px;">${u[k]||'—'}</td>`).join('')}</tr>`).join('')}</tbody>
                                    </table>
                                </div>
                            </div>`;
                        }
                        document.getElementById('lotesContainer').innerHTML = lotesHtml;

                        const sel = document.getElementById('unidadEv');
                        if (sel) sel.innerHTML = '<option value="">Selecciona unidad</option>' + unidades.map(u=>`<option value="${u.unit_number}">${u.unit_number} – ${u.id_lote||''}</option>`).join('');
                    }
                }
                if (!asignaciones.length) {
                    document.getElementById('statusTable').innerHTML = '<div class="chart-card" style="min-height:120px;"><div class="chart-empty"><div class="ico">📋</div><div class="msg">No hay asignaciones registradas aún. La tabla de estatus por unidad aparecerá aquí.</div></div></div>';
                    document.getElementById('lotesContainer').innerHTML = '<div class="chart-card" style="min-height:120px;"><div class="chart-empty"><div class="ico">📦</div><div class="msg">No hay lotes con unidades registradas todavía.</div></div></div>';
                }
            } catch(err) {
                console.error('Dashboard error:', err);
                document.getElementById('kpiContainer').innerHTML = '<p style="color:red;grid-column:1/-1;">Error al conectar con el servidor.</p>';
            }
        }

        async function descargarEvidencias() {
            const unit = document.getElementById('unidadEv').value;
            if (!unit) return alert('Selecciona una unidad');
            const res = await fetchAuth(`/api/evidencias/download/${unit}`);
            if (!res.ok) return alert('Error al descargar evidencias');
            const blob = await res.blob(); const url = URL.createObjectURL(blob);
            const a = document.createElement('a'); a.href=url; a.download=`evidencias_${unit}.zip`; a.click();
            setTimeout(()=>URL.revokeObjectURL(url),1000);
        }

        async function descargarReporte() {
            const res = await fetchAuth('/api/reportes/exportar-maestro');
            if (!res.ok) return alert('Error al generar reporte');
            const blob = await res.blob(); const url = URL.createObjectURL(blob);
            const a = document.createElement('a'); a.href=url; a.download='reporte_maestro.xlsx'; a.click();
            setTimeout(()=>URL.revokeObjectURL(url),1000);
        }

        cargarDashboard();
    </script>
    """
    return HTMLResponse(content=pagina_con_menu("📊 Panel de Rendimiento Operativo", contenido, "dashboard"))

@router.get("/app/asignaciones", response_class=HTMLResponse)
async def asignaciones():
    contenido = """
    <script> if (window.role !== 'admin' && window.role !== 'visor') { window.location.href = '/app/mis-tareas'; } </script>
    <div id="solicitudesPendientes">
        <div style="display:flex; justify-content:space-between; align-items:center;">
            <div class="section-title" style="margin:0;">🔔 Solicitudes Pendientes</div>
            <button class="btn-primary" onclick="cargarSolicitudes()" style="margin-bottom:16px; width:auto;">🔄 Recargar</button>
        </div>
        <div id="listaSolicitudes" style="margin-top:16px;"></div>
    </div>
    <div class="section-title admin-only">➕ Asignación Directa</div>
    <form id="asignacionForm" class="admin-only" style="display:grid; grid-template-columns: 1fr 1fr 1fr; gap:12px;">
        <select id="unidad" required><option value="">Unidad</option></select>
        <select id="tecnico" required><option value="">Técnico</option></select>
        <select id="actividad" required><option value="">Actividad</option></select>
        <button type="submit" class="btn-primary" style="grid-column: span 3;">📋 Crear Orden</button>
        <div id="msgAsignacion" style="grid-column: span 3; font-size:0.85rem;"></div>
    </form>
    <script>
        const fetchAuth = window.fetchAuth;
        const actividades = ['Cableado','Programación','Soldadura','Check de fugas','Vacío','Cerrado','Pre-viaje','Horas Corridas','Standby','GPS','Corriendo','Inspección','Accesorios','Toma de Valores','Evidencia','Toma de Series'];
        document.getElementById('unidad').addEventListener('change', () => document.getElementById('msgAsignacion').innerHTML = '');
        document.getElementById('tecnico').addEventListener('change', () => document.getElementById('msgAsignacion').innerHTML = '');
        document.getElementById('actividad').addEventListener('change', () => document.getElementById('msgAsignacion').innerHTML = '');

        async function cargarSolicitudes() {
            const lista = document.getElementById('listaSolicitudes');
            lista.innerHTML = '<p style="color:var(--carrier-warn);">Cargando solicitudes...</p>';
            try {
                const res = await fetchAuth('/api/asignaciones/?estado=solicitado');
                if (!res.ok) throw new Error('Error ' + res.status);
                const solicitudes = await res.json();
                let html = '';
                if (!Array.isArray(solicitudes) || solicitudes.length === 0) {
                    html = '<p>✅ Sin solicitudes pendientes.</p>';
                } else {
                    solicitudes.forEach(s => {
                        html += `<div style="background:white; border-radius:12px; padding:16px; margin-bottom:12px; box-shadow:0 2px 8px rgba(0,0,0,0.05); display:flex; justify-content:space-between; align-items:center;">
                            <div><b>${s.tecnico}</b> solicita <b>${s.actividad_id}</b> — Unidad: <b>${s.unidad}</b></div>
                            <div>
                                <button class="btn-success" onclick="aprobar(${s.id})">✅ Aprobar</button>
                                <button class="btn-danger" onclick="rechazar(${s.id})">❌ Rechazar</button>
                            </div>
                        </div>`;
                    });
                }
                lista.innerHTML = html;
            } catch (err) {
                console.error(err);
                lista.innerHTML = '<p style="color:var(--carrier-danger);">Error al cargar solicitudes. Intenta recargar.</p>';
            }

            const [unidadesRes, tecnicosRes] = await Promise.all([fetchAuth('/api/unidades/'), fetchAuth('/api/usuarios/')]);
            const unidades = await unidadesRes.json(); const tecnicos = await tecnicosRes.json();
            document.getElementById('unidad').innerHTML = '<option value="">Unidad</option>' + (Array.isArray(unidades) ? unidades.map(u => `<option value="${u.unit_number}">${u.id_lote} - ${u.unit_number}</option>`).join('') : '');
            document.getElementById('tecnico').innerHTML = '<option value="">Técnico</option>' + (Array.isArray(tecnicos) ? tecnicos.filter(u => u.role === 'tecnico').map(u => `<option value="${u.username}">${u.username}</option>`).join('') : '');
            document.getElementById('actividad').innerHTML = '<option value="">Actividad</option>' + actividades.map(a => `<option value="${a}">${a}</option>`).join('');
        }

        async function aprobar(id) { await fetchAuth('/api/asignaciones/' + id, { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ estado: 'pendiente' }) }); cargarSolicitudes(); }
        async function rechazar(id) { if (confirm('¿Eliminar solicitud?')) { await fetchAuth('/api/asignaciones/' + id, { method: 'DELETE' }); cargarSolicitudes(); } }

        document.getElementById('asignacionForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            const unidad = document.getElementById('unidad').value, tecnico = document.getElementById('tecnico').value, actividad = document.getElementById('actividad').value;
            const msgDiv = document.getElementById('msgAsignacion');
            if (!unidad || !tecnico || !actividad) return alert('Completa los campos');
            msgDiv.innerHTML = '<p style="color:var(--carrier-warn);">Verificando...</p>';
            try {
                const res = await fetchAuth('/api/asignaciones/');
                if (!res.ok) throw new Error('Error al verificar');
                const todas = await res.json();
                const activas = todas.filter(a => a.unidad === unidad && a.actividad_id === actividad && a.estado !== 'completada' && a.estado !== 'rechazada');
                const completadas = todas.filter(a => a.unidad === unidad && a.actividad_id === actividad && a.estado === 'completada');
                if (activas.length > 0) {
                    if (!confirm(`Ya existe una tarea activa (${activas.map(a => a.tecnico).join(', ')}) para esta combinación. ¿Deseas crear la orden de todos modos?`)) {
                        msgDiv.innerHTML = '';
                        return;
                    }
                }
                if (completadas.length > 0 && !confirm('Esta actividad ya fue completada anteriormente. ¿Deseas crear una nueva orden?')) { msgDiv.innerHTML = ''; return; }
                await fetchAuth('/api/asignaciones/', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ unidad, tecnico, actividad_id: actividad, estado: 'pendiente' }) });
                msgDiv.innerHTML = '<p style="color:var(--carrier-success);">✅ Orden creada correctamente.</p>';
                cargarSolicitudes();
            } catch (err) { msgDiv.innerHTML = `<p style="color:var(--carrier-danger);">Error: ${err.message}</p>`; }
        });
        cargarSolicitudes();
    </script>
    """
    return HTMLResponse(content=pagina_con_menu("🎯 Control de Asignaciones", contenido, "asignaciones"))

# ------------------------------------------------------------
# TICKETS (admin)
# ------------------------------------------------------------
@router.get("/app/tickets", response_class=HTMLResponse)
async def tickets():
    contenido = """
    <script> if (window.role !== 'admin' && window.role !== 'visor') { window.location.href = '/app/mis-tareas'; } </script>
    <div id="ticketsList"></div>
    <div class="section-title admin-only">➕ Nuevo Ticket</div>
    <form id="ticketForm" class="admin-only">
        <select id="unidad" required><option value="">Unidad</option></select>
        <input type="text" id="vin" placeholder="VIN (opcional)">
        <textarea id="descripcion" placeholder="Descripción del problema" rows="3" required></textarea>
        <select id="tecnico" required><option value="">Asignar a técnico</option></select>
        <button type="submit" class="btn-primary">🎫 Crear Ticket</button>
    </form>
    <script>
        const fetchAuth = window.fetchAuth;
        async function cargarTickets() {
            const res = await fetchAuth('/api/tickets/'); const tickets = await res.json();
            let html = '';
            if (tickets.length) tickets.forEach(t => {
                const estado = t.atendido ? (t.reporte_enviado ? '🟢 Completado' : '🟡 Atendido (sin reporte)') : '🔴 No atendido';
                const color = t.atendido ? (t.reporte_enviado ? 'var(--carrier-success)' : 'var(--carrier-warn)') : 'var(--carrier-danger)';
                html += `<div style="border-left:6px solid ${color}; background:white; padding:16px; margin-bottom:12px; border-radius:0 12px 12px 0; box-shadow:0 2px 8px rgba(0,0,0,0.05);"><span style="font-size:1.5rem; font-weight:800; color:var(--carrier-blue);">#${t.ticket_num}</span><span class="badge" style="background:${color}; color:white;">${estado}</span><p><b>Unidad:</b> ${t.unit_number} | <b>VIN:</b> ${t.vin_number || 'N/D'}</p><p><b>Descripción:</b> ${t.descripcion}</p><small>Creado por: ${t.creado_por} · ${t.fecha_creacion}</small>${!t.atendido ? `<button class="btn-danger" onclick="eliminarTicket(${t.id})">🗑️</button>` : ''}${t.atendido && !t.reporte_enviado ? `<button class="btn-primary" onclick="marcarReporte(${t.id})">📤 Marcar reporte enviado</button>` : ''}</div>`;
            });
            if (!html) html = '<p>📋 No hay tickets.</p>'; document.getElementById('ticketsList').innerHTML = html;
            const [unidadesRes, tecnicosRes] = await Promise.all([fetchAuth('/api/unidades/'), fetchAuth('/api/usuarios/')]);
            const unidades = await unidadesRes.json(); const tecnicos = await tecnicosRes.json();
            document.getElementById('unidad').innerHTML = '<option value="">Unidad</option>' + (Array.isArray(unidades) ? unidades.map(u => `<option value="${u.unit_number}">${u.unit_number} (${u.id_lote})</option>`).join('') : '');
            document.getElementById('tecnico').innerHTML = '<option value="">Asignar a técnico</option>' + (Array.isArray(tecnicos) ? tecnicos.filter(u => u.role === 'tecnico').map(u => `<option value="${u.username}">${u.username}</option>`).join('') : '');
        }
        async function eliminarTicket(id) { if (confirm('¿Eliminar ticket?')) { await fetchAuth('/api/tickets/' + id, { method: 'DELETE' }); cargarTickets(); } }
        async function marcarReporte(id) { await fetchAuth('/api/tickets/' + id + '/report', { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ reporte: 'Reporte enviado' }) }); cargarTickets(); }
        document.getElementById('ticketForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            const unidad      = document.getElementById('unidad').value;
            const vin         = document.getElementById('vin').value;
            const descripcion = document.getElementById('descripcion').value;
            const tecnico     = document.getElementById('tecnico').value;
            if (!unidad || !descripcion || !tecnico) return alert('Completa los campos obligatorios');
            await fetchAuth('/api/tickets/', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ unit_number: unidad, vin_number: vin, descripcion, tecnico }) });
            alert('Ticket creado'); cargarTickets();
        });
        cargarTickets();
    </script>
    """
    return HTMLResponse(content=pagina_con_menu("🎫 Gestión de Tickets", contenido, "tickets"))

# ------------------------------------------------------------
# INVENTARIO (admin)
# ------------------------------------------------------------
@router.get("/app/inventario", response_class=HTMLResponse)
async def inventario():
    contenido = """
    <script> if (window.role !== 'admin' && window.role !== 'visor') { window.location.href = '/app/mis-tareas'; } </script>
    <div class="inv-info-bar" id="infoBar"></div>
    <div style="display:flex; gap:12px; margin-bottom:16px;">
        <button class="btn-primary" onclick="agregarFila()">➕ Agregar Fila</button>
        <button class="btn-warning" onclick="guardarInventario()">💾 Guardar Cambios</button>
        <button class="btn-primary" onclick="mostrarConfigColumnas()">⚙️ Configurar Columnas</button>
    </div>
    <div id="inventarioTable" style="overflow-x:auto;"></div>
    <div id="modalColumnas" class="modal" style="display:none;">
        <div class="modal-content"><h3>⚙️ Configurar Columnas</h3><input type="text" id="nuevaColumna" placeholder="Nuevo nombre de columna"><button class="btn-primary" onclick="agregarColumna()">➕ Agregar</button><div id="columnasList" style="margin-top:12px;"></div><button class="btn-danger" onclick="cerrarModal()">Cerrar</button></div>
    </div>
    <script>
        const fetchAuth = window.fetchAuth; let columnas = [], datos = [];
        async function cargarInventario() {
            const colRes = await fetchAuth('/api/inventario/columnas'); columnas = await colRes.json();
            if (!Array.isArray(columnas) || columnas.length === 0) { columnas = ["Código","Descripción","Cantidad","Unidad","Ubicación","Estado"]; await fetchAuth('/api/inventario/columnas', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(columnas) }); }
            const datRes = await fetchAuth('/api/inventario/datos'); datos = await datRes.json();
            if (!Array.isArray(datos) || datos.length === 0) datos = [Object.fromEntries(columnas.map(c => [c, '']))];
            document.getElementById('infoBar').innerHTML = `🗄 Inventario Principal &nbsp;·&nbsp; ${datos.length} registros &nbsp;·&nbsp; ${columnas.length} columnas`;
            renderTabla();
        }
        function renderTabla() { let html = '<table><thead><tr><th>#</th>'; columnas.forEach(c => html += `<th>${c}</th>`); html += '<th>Acción</th></tr></thead><tbody>'; datos.forEach((fila, idx) => { html += `<tr><td style="text-align:center;">${idx+1}</td>`; columnas.forEach(c => html += `<td><input type="text" value="${fila[c] || ''}" onchange="datos[${idx}]['${c}'] = this.value" style="margin:0;"></td>`); html += `<td><button class="btn-danger" onclick="eliminarFila(${idx})">🗑</button></td>`; }); html += '</tbody></table>'; document.getElementById('inventarioTable').innerHTML = html; }
        function agregarFila() { datos.push(Object.fromEntries(columnas.map(c => [c, '']))); renderTabla(); }
        function eliminarFila(idx) { if (confirm('¿Eliminar fila?')) { datos.splice(idx,1); renderTabla(); } }
        async function guardarInventario() { await fetchAuth('/api/inventario/datos', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(datos) }); alert('Inventario guardado'); }
        async function agregarColumna() { const nombre = document.getElementById('nuevaColumna').value.trim(); if (!nombre) return; if (!columnas.includes(nombre)) { columnas.push(nombre); await fetchAuth('/api/inventario/columnas', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(columnas) }); datos = datos.map(fila => { fila[nombre] = ''; return fila; }); renderTabla(); } }
        function mostrarConfigColumnas() { document.getElementById('modalColumnas').style.display = 'flex'; renderColumnasList(); }
        function cerrarModal() { document.getElementById('modalColumnas').style.display = 'none'; }
        function renderColumnasList() { let html = ''; columnas.forEach((c, i) => { html += `<div style="display:flex; justify-content:space-between; margin-bottom:4px;"><input type="text" value="${c}" onchange="renombrarColumna(${i}, this.value)"><button class="btn-danger" onclick="eliminarColumna(${i})">🗑</button></div>`; }); document.getElementById('columnasList').innerHTML = html; }
        async function renombrarColumna(idx, nuevoNombre) { columnas[idx] = nuevoNombre; await fetchAuth('/api/inventario/columnas', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(columnas) }); renderTabla(); }
        async function eliminarColumna(idx) { columnas.splice(idx, 1); await fetchAuth('/api/inventario/columnas', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(columnas) }); datos = datos.map(fila => { const newFila = {}; columnas.forEach(c => newFila[c] = fila[c] || ''); return newFila; }); renderTabla(); }
        cargarInventario();
    </script>
    """
    return HTMLResponse(content=pagina_con_menu("📦 Gestión de Inventarios", contenido, "inventario"))

# ------------------------------------------------------------
# REGISTRO DE UNIDADES (admin)
# ------------------------------------------------------------
@router.get("/app/unidades", response_class=HTMLResponse)
async def unidades():
    contenido = """
    <script> if (window.role !== 'admin' && window.role !== 'visor') { window.location.href = '/app/mis-tareas'; } </script>
    <form id="unidadForm" class="admin-only" style="display:grid; grid-template-columns: 1fr 1fr; gap:12px;">
        <input type="text" id="unit_number" placeholder="Número Económico" required><input type="text" id="id_lote" placeholder="Número de Lote">
        <input type="text" id="vin_number" placeholder="VIN Number"><input type="text" id="reefer_serial" placeholder="Serie del Reefer">
        <input type="text" id="reefer_model" placeholder="Modelo del Reefer"><input type="text" id="evaporator_serial_mjs11" placeholder="Evaporador MJS11">
        <input type="text" id="evaporator_serial_mjd22" placeholder="Evaporador MJD22"><input type="text" id="engine_serial" placeholder="Motor">
        <input type="text" id="compressor_serial" placeholder="Compresor"><input type="text" id="generator_serial" placeholder="Generador">
        <input type="text" id="battery_charger_serial" placeholder="Cargador de Batería">
        <button type="submit" class="btn-primary" style="grid-column: span 2;">💾 Guardar Registro</button>
    </form>
    <div class="section-title">📸 Unidades Registradas</div>
    <div id="unidadesList"></div>
    <script>
        const fetchAuth = window.fetchAuth;
        async function cargarUnidades() { const res = await fetchAuth('/api/unidades/'); const unidades = await res.json(); let html = '<table><thead><tr><th>#Económico</th><th>Lote</th><th>VIN</th><th>Reefer Serial</th><th>Modelo</th><th>Motor</th><th>Compresor</th></tr></thead><tbody>'; if (Array.isArray(unidades)) unidades.forEach(u => html += `<tr><td>${u.unit_number}</td><td>${u.id_lote||''}</td><td style="font-family:monospace;">${u.vin_number||''}</td><td>${u.reefer_serial||''}</td><td>${u.reefer_model||''}</td><td style="font-family:monospace;">${u.engine_serial||''}</td><td>${u.compressor_serial||''}</td>`); html += '</tbody></table>'; document.getElementById('unidadesList').innerHTML = html; }
        document.getElementById('unidadForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            const data = {
                unit_number: document.getElementById('unit_number').value,
                id_lote: document.getElementById('id_lote').value,
                vin_number: document.getElementById('vin_number').value,
                reefer_serial: document.getElementById('reefer_serial').value,
                reefer_model: document.getElementById('reefer_model').value,
                evaporator_serial_mjs11: document.getElementById('evaporator_serial_mjs11').value,
                evaporator_serial_mjd22: document.getElementById('evaporator_serial_mjd22').value,
                engine_serial: document.getElementById('engine_serial').value,
                compressor_serial: document.getElementById('compressor_serial').value,
                generator_serial: document.getElementById('generator_serial').value,
                battery_charger_serial: document.getElementById('battery_charger_serial').value
            };
            if (!data.unit_number) return alert('El Número Económico es obligatorio');
            await fetchAuth('/api/unidades/', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data) });
            alert('Unidad registrada'); cargarUnidades();
        });
        cargarUnidades();
    </script>
    """
    return HTMLResponse(content=pagina_con_menu("📸 Registro de Unidades", contenido, "unidades"))

# ------------------------------------------------------------
# GESTIÓN DE USUARIOS (admin) - se añadió opción "visor"
# ------------------------------------------------------------
@router.get("/app/usuarios", response_class=HTMLResponse)
async def usuarios():
    contenido = """
    <script> if (window.role !== 'admin' && window.role !== 'visor') { window.location.href = '/app/mis-tareas'; } </script>

    <style>
        .team-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 28px;
        }
        .perfil-card {
            background: var(--bg-surface);
            border-radius: 14px;
            overflow: hidden;
            box-shadow: 0 4px 16px var(--shadow-soft);
            border-top: 5px solid var(--carrier-accent);
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }
        .perfil-card:hover { transform: translateY(-4px); box-shadow: 0 10px 28px var(--shadow-soft); }
        .perfil-card.role-admin  { border-top-color: var(--carrier-blue); }
        .perfil-card.role-tecnico { border-top-color: var(--carrier-success); }
        .perfil-card.role-visor  { border-top-color: var(--carrier-warn); }
        .perfil-foto {
            width: 100%; aspect-ratio: 1/1; object-fit: cover;
            background: var(--bg-surface-2); display: block;
        }
        .perfil-foto-placeholder {
            width: 100%; aspect-ratio: 1/1;
            background: linear-gradient(135deg, var(--bg-surface-2), var(--carrier-light));
            display: flex; align-items: center; justify-content: center;
            font-size: 3.5rem;
        }
        .perfil-body { padding: 13px 13px 15px; }
        .perfil-nombre { font-weight: 700; font-size: 0.95rem; color: var(--text-primary); margin-bottom: 4px; }
        .perfil-puesto {
            display: inline-block; font-size: 0.72rem; font-weight: 700;
            letter-spacing: 0.5px; text-transform: uppercase;
            color: white; background: var(--carrier-accent);
            padding: 3px 10px; border-radius: 20px; margin-bottom: 10px;
        }
        .perfil-card.role-admin  .perfil-puesto { background: var(--carrier-blue); }
        .perfil-card.role-tecnico .perfil-puesto { background: var(--carrier-success); }
        .perfil-card.role-visor  .perfil-puesto { background: var(--carrier-warn); }
        .perfil-acciones { display: flex; gap: 6px; flex-wrap: wrap; }
        .btn-sm {
            padding: 5px 10px; font-size: 0.75rem; font-weight: 600;
            border: none; border-radius: 8px; cursor: pointer; transition: opacity 0.15s;
        }
        .btn-sm:hover { opacity: 0.82; }
        .btn-sm-blue   { background: var(--carrier-accent); color: white; }
        .btn-sm-amber  { background: var(--carrier-warn);   color: white; }
        .btn-sm-red    { background: var(--carrier-danger);  color: white; }
    </style>

    <div class="section-title">👥 Equipo Operativo</div>
    <div id="teamGrid" class="team-grid"></div>

    <div class="section-title admin-only" style="margin-top:28px;">➕ Crear Nuevo Usuario</div>
    <div class="admin-only" style="display:grid; grid-template-columns: 1fr 1fr 1fr; gap:12px;">
        <input type="text" id="username" placeholder="Nombre de usuario" required>
        <input type="password" id="newUserPassword" placeholder="Contraseña" required>
        <select id="role" required>
            <option value="tecnico">Técnico</option>
            <option value="admin">Administrador</option>
            <option value="visor">Visor (solo lectura)</option>
        </select>
        <button onclick="crearUsuario()" class="btn-primary" style="grid-column: span 3;">👤 Crear Usuario</button>
    </div>

    <script>
        const fetchAuth = window.fetchAuth;

        const ROLE_EMOJI = { admin: '🛡', tecnico: '🔧', visor: '👁' };
        const ROLE_LABEL = { admin: 'Administrador', tecnico: 'Técnico', visor: 'Visor' };

        async function cargarUsuarios() {
            try {
                const res = await fetchAuth('/api/usuarios/');
                const usuarios = await res.json();
                if (!Array.isArray(usuarios)) throw new Error('respuesta inválida');

                let html = '';
                usuarios.forEach(u => {
                    const puesto = u.puesto || ROLE_LABEL[u.role] || u.role;
                    const fotoHtml = u.foto_url
                        ? `<img class="perfil-foto" src="${u.foto_url}" alt="${u.username}" onerror="this.style.display='none';this.nextElementSibling.style.display='flex';">
                           <div class="perfil-foto-placeholder" style="display:none;">👤</div>`
                        : `<div class="perfil-foto-placeholder">👤</div>`;

                    const accionesAdmin = window.role === 'admin' ? `
                        <button class="btn-sm btn-sm-blue" onclick="abrirModalPerfil(${u.id}, '${u.username}', '${u.foto_url || ''}', '${(u.puesto || '').replace(/'/g,"\\'")}')">🖼 Perfil</button>
                        <button class="btn-sm btn-sm-amber" onclick="abrirModalPassword(${u.id}, '${u.username}')">🔑 Pwd</button>
                        <button class="btn-sm btn-sm-red" onclick="eliminarUsuario(${u.id}, '${u.username}')">🗑</button>
                    ` : '';

                    html += `
                    <div class="perfil-card role-${u.role}">
                        ${fotoHtml}
                        <div class="perfil-body">
                            <div class="perfil-nombre">${ROLE_EMOJI[u.role] || ''} ${u.username}</div>
                            <div class="perfil-puesto">${puesto}</div>
                            <div class="perfil-acciones">${accionesAdmin}</div>
                        </div>
                    </div>`;
                });

                document.getElementById('teamGrid').innerHTML = html || '<p style="color:var(--text-secondary);">No hay usuarios registrados.</p>';
            } catch (err) {
                document.getElementById('teamGrid').innerHTML = '<p style="color:var(--carrier-danger);">Error al cargar usuarios.</p>';
            }
        }

        /* ── Modal: editar foto y puesto ── */
        function abrirModalPerfil(userId, username, fotoActual, puestoActual) {
            const prev = document.getElementById('modalPerfil');
            if (prev) prev.remove();
            const modal = document.createElement('div');
            modal.id = 'modalPerfil';
            modal.style.cssText = 'position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.55);display:flex;justify-content:center;align-items:center;z-index:500;padding:16px;';
            modal.innerHTML = `
                <div style="background:var(--bg-surface);border-radius:20px;padding:28px;width:100%;max-width:460px;box-shadow:0 20px 60px rgba(0,43,91,0.25);animation:fadeInP 0.2s ease;">
                    <div style="display:flex;align-items:center;gap:12px;margin-bottom:8px;">
                        <div style="background:var(--carrier-light);border-radius:12px;width:48px;height:48px;display:flex;align-items:center;justify-content:center;font-size:1.5rem;">🖼</div>
                        <div>
                            <h3 style="margin:0;color:var(--carrier-blue);font-size:1.1rem;font-weight:800;">Editar Perfil</h3>
                            <p style="margin:2px 0 0;font-size:0.82rem;color:var(--text-secondary);">Usuario: <b>${username}</b></p>
                        </div>
                    </div>
                    <hr style="border:none;border-top:1px solid var(--border-color);margin:16px 0;">

                    <!-- Preview foto -->
                    <div style="text-align:center;margin-bottom:18px;">
                        <div style="position:relative;display:inline-block;">
                            <img id="fotoPreview"
                                src="${fotoActual || ''}"
                                style="width:100px;height:100px;border-radius:50%;object-fit:cover;border:3px solid var(--carrier-accent);display:${fotoActual ? 'block' : 'none'};">
                            <div id="fotoPlaceholder"
                                style="width:100px;height:100px;border-radius:50%;background:var(--carrier-light);display:${fotoActual ? 'none' : 'inline-flex'};align-items:center;justify-content:center;font-size:2.6rem;border:3px solid var(--border-color);">👤</div>
                            <!-- Botón cámara encima de la foto -->
                            <label for="inputArchivoFoto" style="position:absolute;bottom:2px;right:2px;background:var(--carrier-blue);color:white;border-radius:50%;width:30px;height:30px;display:flex;align-items:center;justify-content:center;cursor:pointer;font-size:0.9rem;box-shadow:0 2px 6px rgba(0,0,0,0.25);" title="Cambiar foto">📷</label>
                        </div>
                        <p style="font-size:0.75rem;color:var(--text-secondary);margin:8px 0 0;">Toca 📷 para subir foto desde tu dispositivo</p>
                    </div>

                    <!-- Input archivo oculto -->
                    <input id="inputArchivoFoto" type="file" accept="image/*" style="display:none;" onchange="cargarFotoArchivo(this)">

                    <!-- Puesto -->
                    <label style="font-size:0.82rem;font-weight:700;color:var(--carrier-blue);display:block;margin-bottom:4px;">Puesto / Cargo</label>
                    <input id="inputPuesto" type="text" placeholder="Ej: Jefe de Operaciones, Técnico..." value="${puestoActual}" style="margin-bottom:4px;">

                    <p id="perfilError" style="color:var(--carrier-danger);font-size:0.82rem;min-height:18px;margin:6px 0 14px;"></p>

                    <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;">
                        <button onclick="document.getElementById('modalPerfil').remove()" style="background:var(--bg-surface-2);color:var(--text-primary);border:1px solid var(--border-color);border-radius:10px;padding:13px;font-weight:600;font-size:0.9rem;cursor:pointer;">✖ Cancelar</button>
                        <button id="btnGuardarPerfil" onclick="guardarPerfil(${userId})" style="background:linear-gradient(135deg,var(--carrier-blue),var(--carrier-accent));color:white;border:none;border-radius:10px;padding:13px;font-weight:700;font-size:0.9rem;cursor:pointer;">💾 Guardar</button>
                    </div>
                </div>
                <style>@keyframes fadeInP{from{opacity:0;transform:scale(0.95)}to{opacity:1;transform:scale(1)}}</style>`;
            document.body.appendChild(modal);
            // guardar base64 en variable temporal
            window._fotoBase64 = fotoActual || '';
        }

        function cargarFotoArchivo(input) {
            const file = input.files[0];
            if (!file) return;
            if (file.size > 8 * 1024 * 1024) {
                document.getElementById('perfilError').textContent = 'La imagen no debe superar 8MB.';
                return;
            }
            const reader = new FileReader();
            reader.onload = function(e) {
                const img = new Image();
                img.onload = function() {
                    // Redimensionar a max 300x300 con canvas
                    const MAX = 300;
                    let w = img.width, h = img.height;
                    if (w > h) { if (w > MAX) { h = h * MAX / w; w = MAX; } }
                    else       { if (h > MAX) { w = w * MAX / h; h = MAX; } }
                    const canvas = document.createElement('canvas');
                    canvas.width = w; canvas.height = h;
                    canvas.getContext('2d').drawImage(img, 0, 0, w, h);
                    const base64 = canvas.toDataURL('image/jpeg', 0.82);
                    window._fotoBase64 = base64;
                    // Mostrar preview
                    const preview = document.getElementById('fotoPreview');
                    const placeholder = document.getElementById('fotoPlaceholder');
                    preview.src = base64;
                    preview.style.display = 'block';
                    if (placeholder) placeholder.style.display = 'none';
                    document.getElementById('perfilError').textContent = '';
                };
                img.src = e.target.result;
            };
            reader.readAsDataURL(file);
        }

        async function guardarPerfil(userId) {
            const foto_url = window._fotoBase64 || '';
            const puesto   = document.getElementById('inputPuesto').value.trim();
            const btn = document.getElementById('btnGuardarPerfil');
            btn.textContent = 'Guardando...'; btn.disabled = true;
            const res = await fetchAuth('/api/usuarios/' + userId + '/perfil', {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ foto_url, puesto })
            });
            if (res.ok) {
                document.getElementById('modalPerfil').remove();
                mostrarToast('✅ Perfil actualizado correctamente.', '#1F4E79');
                cargarUsuarios();
            } else {
                const err = await res.json();
                document.getElementById('perfilError').textContent = err.detail || 'Error al guardar.';
                btn.textContent = '💾 Guardar'; btn.disabled = false;
            }
        }

        /* ── Modal: cambiar contraseña (igual que antes) ── */
        function abrirModalPassword(userId, username) {
            const prev = document.getElementById('modalPassword');
            if (prev) prev.remove();
            const modal = document.createElement('div');
            modal.id = 'modalPassword';
            modal.style.cssText = 'position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.55);display:flex;justify-content:center;align-items:center;z-index:500;padding:16px;';
            modal.innerHTML = `
                <div style="background:var(--bg-surface);border-radius:20px;padding:32px;width:100%;max-width:460px;box-shadow:0 20px 60px rgba(0,43,91,0.25);animation:fadeInP 0.2s ease;">
                    <div style="display:flex;align-items:center;gap:12px;margin-bottom:8px;">
                        <div style="background:#fef3c7;border-radius:12px;width:48px;height:48px;display:flex;align-items:center;justify-content:center;font-size:1.5rem;">🔑</div>
                        <div>
                            <h3 style="margin:0;color:var(--carrier-blue);font-size:1.1rem;font-weight:800;">Cambiar Contraseña</h3>
                            <p style="margin:2px 0 0;font-size:0.82rem;color:var(--text-secondary);">Usuario: <b>${username}</b></p>
                        </div>
                    </div>
                    <hr style="border:none;border-top:1px solid var(--border-color);margin:18px 0;">
                    <label style="font-size:0.85rem;font-weight:700;color:var(--carrier-blue);display:block;margin-bottom:6px;">Nueva contraseña</label>
                    <div style="position:relative;">
                        <input id="inputNuevaPwd" type="password" placeholder="Escribe la nueva contraseña" style="width:100%;">
                        <span onclick="togglePwd()" style="position:absolute;right:14px;top:50%;transform:translateY(-50%);cursor:pointer;font-size:1.1rem;">👁</span>
                    </div>
                    <p id="pwdError" style="color:var(--carrier-danger);font-size:0.82rem;min-height:18px;margin:4px 0 12px;"></p>
                    <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;">
                        <button onclick="document.getElementById('modalPassword').remove()" style="background:var(--bg-surface-2);color:var(--text-primary);border:1px solid var(--border-color);border-radius:10px;padding:13px;font-weight:600;font-size:0.95rem;cursor:pointer;">✖ Cancelar</button>
                        <button id="btnGuardarPwd" onclick="guardarPassword(${userId})" style="background:linear-gradient(135deg,var(--carrier-blue),var(--carrier-accent));color:white;border:none;border-radius:10px;padding:13px;font-weight:700;font-size:0.95rem;cursor:pointer;">💾 Guardar</button>
                    </div>
                </div>
                <style>@keyframes fadeInP{from{opacity:0;transform:scale(0.95)}to{opacity:1;transform:scale(1)}}</style>`;
            document.body.appendChild(modal);
            setTimeout(() => document.getElementById('inputNuevaPwd').focus(), 100);
        }

        function togglePwd() {
            const input = document.getElementById('inputNuevaPwd');
            input.type = input.type === 'password' ? 'text' : 'password';
        }

        async function guardarPassword(userId) {
            const pwd = document.getElementById('inputNuevaPwd').value.trim();
            const errorEl = document.getElementById('pwdError');
            if (!pwd || pwd.length < 4) { errorEl.textContent = 'Mínimo 4 caracteres.'; return; }
            const btn = document.getElementById('btnGuardarPwd');
            btn.textContent = 'Guardando...'; btn.disabled = true;
            const res = await fetchAuth('/api/usuarios/' + userId + '/password', {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ new_password: pwd })
            });
            if (res.ok) {
                document.getElementById('modalPassword').remove();
                mostrarToast('✅ Contraseña actualizada correctamente.', '#1F4E79');
            } else {
                const err = await res.json();
                errorEl.textContent = err.detail || 'Error al guardar.';
                btn.textContent = '💾 Guardar'; btn.disabled = false;
            }
        }

        async function crearUsuario() {
            const username = document.getElementById('username').value.trim();
            const password = document.getElementById('newUserPassword').value;
            const role     = document.getElementById('role').value;
            if (!username || !password) return alert('Completa todos los campos');
            const res = await fetchAuth('/api/usuarios/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username, password, role })
            });
            if (res.ok) {
                document.getElementById('username').value = '';
                document.getElementById('newUserPassword').value = '';
                cargarUsuarios();
                mostrarToast('✅ Usuario creado exitosamente.', '#16a34a');
            } else {
                const err = await res.json();
                alert('Error: ' + (err.detail || 'No se pudo crear el usuario'));
            }
        }

        async function eliminarUsuario(id, nombre) {
            if (!confirm(`¿Eliminar al usuario "${nombre}"? Esta acción no se puede deshacer.`)) return;
            const res = await fetchAuth('/api/usuarios/' + id, { method: 'DELETE' });
            if (res.ok) { mostrarToast('🗑 Usuario eliminado.', '#dc2626'); cargarUsuarios(); }
            else alert('Error al eliminar usuario');
        }

        function mostrarToast(msg, color) {
            const t = document.createElement('div');
            t.style.cssText = `position:fixed;bottom:28px;left:50%;transform:translateX(-50%);background:${color};color:white;padding:14px 28px;border-radius:50px;font-weight:700;font-size:0.95rem;box-shadow:0 4px 20px rgba(0,0,0,0.2);z-index:600;white-space:nowrap;`;
            t.textContent = msg;
            document.body.appendChild(t);
            setTimeout(() => t.remove(), 3000);
        }

        cargarUsuarios();
    </script>
    """
    return HTMLResponse(content=pagina_con_menu("👥 Gestión de Usuarios", contenido, "usuarios"))

# ------------------------------------------------------------
# PANEL DE ADMINISTRACIÓN (admin) — CRUD interactivo
# ------------------------------------------------------------
@router.get("/app/admin", response_class=HTMLResponse)
async def admin():
    contenido = """
    <script> if (window.role !== 'admin') { window.location.href = '/app/mis-tareas'; } </script>

    <!-- Tabler Icons CDN -->
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@tabler/icons-webfont@latest/tabler-icons.min.css">
    <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    :root {
      --navy: #0f2d6b;
      --navy-mid: #1a3f8f;
      --navy-btn: #1e4fc0;
      --navy-light: #2e63d4;
      --danger: #c0392b;
      --danger-hover: #a93226;
      --success: #1a7a4a;
      --warn: #b7640a;
      --text-on-navy: #e8f0ff;
      --row-hover: #edf2fb;
      --selected-bg: #d6e4fc;
      --border: rgba(30,79,192,0.18);
      --color-background-primary: #ffffff;
      --color-background-secondary: #f4f6fb;
      --color-text-primary: #1a2340;
      --color-text-secondary: #6b7280;
      --color-border-secondary: #d1d5db;
      --color-border-tertiary: #e5e7eb;
      --border-radius-md: 8px;
      --border-radius-lg: 12px;
      --font-sans: 'Inter', sans-serif;
      --font-mono: 'Courier New', monospace;
    }
    .panel { padding: 1rem 0; }
    .tabs { display: flex; gap: 8px; margin-bottom: 1.25rem; flex-wrap: wrap; }
    .tab-btn {
      background: var(--navy);
      color: var(--text-on-navy);
      border: none;
      border-radius: var(--border-radius-md);
      padding: 9px 18px;
      font-size: 13px;
      font-weight: 500;
      cursor: pointer;
      display: flex; align-items: center; gap: 7px;
      transition: background 0.15s;
    }
    .tab-btn:hover { background: var(--navy-light); }
    .tab-btn.active { background: var(--navy-btn); outline: 2px solid #6fa3f7; outline-offset: 1px; }
    .tab-btn i { font-size: 15px; }
    .section { display: none; }
    .section.active { display: block; }
    .toolbar {
      display: flex; align-items: center; gap: 10px;
      margin-bottom: 10px; flex-wrap: wrap;
    }
    .toolbar input[type=text] {
      flex: 1; min-width: 160px; max-width: 280px;
      border: 0.5px solid var(--border);
      border-radius: var(--border-radius-md);
      padding: 7px 12px; font-size: 13px;
      background: var(--color-background-primary);
      color: var(--color-text-primary);
      margin-bottom: 0;
    }
    .toolbar select {
      border: 0.5px solid var(--border);
      border-radius: var(--border-radius-md);
      padding: 7px 10px; font-size: 13px;
      background: var(--color-background-primary);
      color: var(--color-text-primary);
      margin-bottom: 0;
    }
    .btn {
      display: inline-flex; align-items: center; gap: 6px;
      padding: 7px 14px; border-radius: var(--border-radius-md);
      font-size: 13px; font-weight: 500; cursor: pointer; border: none;
      transition: background 0.15s, transform 0.1s;
    }
    .btn:active { transform: scale(0.97); }
    .btn-navy { background: var(--navy-btn); color: #fff; }
    .btn-navy:hover { background: var(--navy-light); }
    .btn-danger-sm { background: var(--danger); color: #fff; }
    .btn-danger-sm:hover { background: var(--danger-hover); }
    .btn-ghost {
      background: transparent; color: var(--color-text-secondary);
      border: 0.5px solid var(--color-border-secondary);
    }
    .btn-ghost:hover { background: var(--color-background-secondary); }
    .btn i { font-size: 14px; }
    .bulk-bar {
      display: none; align-items: center; gap: 10px;
      background: #fff3cd; border: 0.5px solid #f5a623;
      border-radius: var(--border-radius-md); padding: 8px 14px;
      margin-bottom: 10px; font-size: 13px; color: #7a4e00;
    }
    .bulk-bar.visible { display: flex; }
    .main-layout { display: flex; gap: 12px; align-items: flex-start; }
    .table-wrap { flex: 1; min-width: 0; overflow: hidden; }
    .data-table { width: 100%; border-collapse: collapse; font-size: 13px; }
    .data-table th {
      background: var(--navy);
      color: var(--text-on-navy);
      padding: 9px 10px; text-align: left;
      font-weight: 500; font-size: 12px; letter-spacing: 0.02em;
      white-space: nowrap;
    }
    .data-table th:first-child { border-radius: var(--border-radius-md) 0 0 0; width: 32px; }
    .data-table th:last-child { border-radius: 0 var(--border-radius-md) 0 0; }
    .data-table td { padding: 9px 10px; border-bottom: 0.5px solid var(--color-border-tertiary); color: var(--color-text-primary); vertical-align: middle; }
    .data-table tr:hover td { background: var(--row-hover); }
    .data-table tr.selected td { background: var(--selected-bg); }
    .data-table tr.editing td { background: #edf6ff; }
    .admin-badge {
      display: inline-block; padding: 2px 9px; border-radius: 999px;
      font-size: 11px; font-weight: 500;
    }
    .badge-pending { background: #fff3cd; color: #7a4e00; }
    .badge-done { background: #d4edda; color: #155724; }
    .badge-req { background: #d1ecf1; color: #0c5460; }
    .badge-cancel { background: #f8d7da; color: #721c24; }
    .row-actions { display: flex; gap: 5px; }
    .icon-btn {
      background: none; border: none; cursor: pointer;
      padding: 4px; border-radius: 5px; color: var(--color-text-secondary);
      font-size: 15px; display: flex; align-items: center; justify-content: center;
      transition: background 0.12s, color 0.12s;
    }
    .icon-btn:hover.edit { background: #dbeafe; color: var(--navy-btn); }
    .icon-btn:hover.del { background: #fde8e8; color: var(--danger); }
    .editor-panel {
      width: 268px; min-width: 268px;
      background: var(--color-background-primary);
      border: 0.5px solid var(--color-border-secondary);
      border-radius: var(--border-radius-lg);
      padding: 1rem; font-size: 13px;
      display: none;
    }
    .editor-panel.visible { display: block; }
    .editor-panel h3 {
      font-size: 14px; font-weight: 500;
      color: var(--navy);
      margin-bottom: 14px;
      display: flex; align-items: center; gap: 7px; justify-content: space-between;
    }
    .editor-panel h3 span { display: flex; align-items: center; gap: 7px; }
    .close-editor { background: none; border: none; cursor: pointer; color: var(--color-text-secondary); font-size: 16px; padding: 2px; border-radius: 4px; }
    .close-editor:hover { background: var(--color-background-secondary); }
    .field-group { margin-bottom: 11px; }
    .field-group label { display: block; font-size: 11px; color: var(--color-text-secondary); margin-bottom: 4px; text-transform: uppercase; letter-spacing: 0.04em; }
    .field-group input, .field-group select, .field-group textarea {
      width: 100%;
      border: 0.5px solid var(--color-border-secondary);
      border-radius: var(--border-radius-md);
      padding: 7px 10px; font-size: 13px;
      background: var(--color-background-primary);
      color: var(--color-text-primary);
      margin-bottom: 0;
    }
    .field-group textarea { resize: vertical; min-height: 60px; }
    .editor-actions { display: flex; gap: 8px; margin-top: 14px; }
    .editor-actions .btn { flex: 1; justify-content: center; }
    .admin-divider { height: 0.5px; background: var(--color-border-tertiary); margin: 14px 0; }
    .id-badge { font-size: 11px; background: var(--color-background-secondary); color: var(--color-text-secondary); padding: 2px 8px; border-radius: var(--border-radius-md); }
    .sql-area {
      width: 100%;
      border: 0.5px solid var(--color-border-secondary);
      border-radius: var(--border-radius-md);
      padding: 12px; font-size: 13px;
      font-family: var(--font-mono);
      background: var(--color-background-secondary);
      color: var(--color-text-primary);
      min-height: 110px; resize: vertical;
      margin-bottom: 10px;
    }
    .sql-result {
      font-size: 12px; font-family: var(--font-mono);
      background: var(--color-background-secondary);
      border: 0.5px solid var(--color-border-tertiary);
      border-radius: var(--border-radius-md);
      padding: 10px 12px; max-height: 180px; overflow-y: auto;
      color: var(--color-text-primary); white-space: pre-wrap;
      display: none; margin-top: 10px;
    }
    .sql-result.visible { display: block; }
    .sql-presets { display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 10px; }
    .sql-presets button {
      font-size: 11px; padding: 4px 10px;
      background: var(--color-background-secondary);
      border: 0.5px solid var(--color-border-secondary);
      border-radius: var(--border-radius-md);
      cursor: pointer; color: var(--color-text-secondary);
      margin-bottom: 0;
    }
    .sql-presets button:hover { background: var(--navy); color: #fff; border-color: var(--navy); }
    .admin-notice { font-size: 12px; color: var(--color-text-secondary); padding: 6px 10px; background: var(--color-background-secondary); border-radius: var(--border-radius-md); border-left: 3px solid var(--navy-light); margin-bottom: 10px; }
    .pagination { display: flex; align-items: center; gap: 8px; margin-top: 10px; font-size: 12px; color: var(--color-text-secondary); }
    .pagination button {
      background: var(--color-background-secondary);
      border: 0.5px solid var(--color-border-secondary);
      border-radius: var(--border-radius-md);
      padding: 4px 10px; font-size: 12px; cursor: pointer;
      margin-bottom: 0;
    }
    .pagination button:hover { background: var(--navy); color: #fff; border-color: var(--navy); }
    .pagination button:disabled { opacity: 0.4; cursor: not-allowed; }
    </style>

    <div class="panel">
      <div class="tabs">
        <button class="tab-btn active" onclick="showTab('actividades')" id="tab-actividades">
          <i class="ti ti-activity"></i> Actividades
        </button>
        <button class="tab-btn" onclick="showTab('usuarios')" id="tab-usuarios">
          <i class="ti ti-users"></i> Usuarios
        </button>
        <button class="tab-btn" onclick="showTab('unidades')" id="tab-unidades">
          <i class="ti ti-truck"></i> Unidades
        </button>
        <button class="tab-btn" onclick="showTab('sql')" id="tab-sql">
          <i class="ti ti-terminal-2"></i> SQL Directo
        </button>
        <button class="tab-btn" onclick="showTab('evidencias')" id="tab-evidencias">
          <i class="ti ti-photo"></i> Evidencias
        </button>
        <button class="tab-btn" onclick="showTab('lotes')" id="tab-lotes">
          <i class="ti ti-layout-grid"></i> Lotes
        </button>
      </div>

      <!-- -- ACTIVIDADES -- -->
      <div id="sec-actividades" class="section active">
        <div class="toolbar">
          <input type="text" id="search-act" placeholder="Buscar por ID, vehículo, técnico…" oninput="filterTable('act')" />
          <select id="filter-estado" onchange="filterTable('act')">
            <option value="">Todos los estados</option>
            <option value="pendiente">Pendiente</option>
            <option value="en_proceso">En Proceso</option>
            <option value="completada">Completada</option>
            <option value="solicitado">Solicitado</option>
            <option value="cancelado">Cancelado</option>
          </select>
          <button class="btn btn-navy" onclick="recargarActividades()">
            <i class="ti ti-refresh"></i> Recargar
          </button>
        </div>
        <div class="bulk-bar" id="bulk-act">
          <i class="ti ti-checkbox"></i>
          <span id="bulk-count-act">0</span> seleccionados
          <button class="btn btn-danger-sm" style="margin-left:auto" onclick="eliminarSeleccionados('act')">
            <i class="ti ti-trash"></i> Eliminar seleccionados
          </button>
        </div>
        <div class="main-layout">
          <div class="table-wrap">
            <table class="data-table" id="table-act">
              <thead>
                <tr>
                  <th><input type="checkbox" id="check-all-act" onchange="toggleAll('act')" /></th>
                  <th>ID</th><th>Unidad</th><th>Actividad</th><th>Técnico</th><th>Estado</th><th>Acciones</th>
                </tr>
              </thead>
              <tbody id="tbody-act"></tbody>
            </table>
            <div class="pagination" id="pag-act"></div>
          </div>
          <div class="editor-panel" id="editor-act">
            <h3>
              <span><i class="ti ti-edit"></i> Editar registro</span>
              <button class="close-editor" onclick="cerrarEditor('act')"><i class="ti ti-x"></i></button>
            </h3>
            <div id="editor-id-act" class="id-badge" style="margin-bottom:12px"></div>
            <div class="field-group"><label>Unidad</label><input type="text" id="ef-vehiculo" /></div>
            <div class="field-group"><label>Técnico</label><input type="text" id="ef-tecnico" /></div>
            <div class="field-group"><label>Estado</label>
              <select id="ef-estado">
                <option value="pendiente">Pendiente</option>
                <option value="en_proceso">En Proceso</option>
                <option value="solicitado">Solicitado</option>
                <option value="completada">Completada</option>
                <option value="cancelado">Cancelado</option>
              </select>
            </div>
            <div class="admin-divider"></div>
            <div class="editor-actions">
              <button class="btn btn-navy" onclick="guardarEditor('act')"><i class="ti ti-device-floppy"></i> Guardar</button>
              <button class="btn btn-ghost" onclick="cerrarEditor('act')">Cancelar</button>
            </div>
          </div>
        </div>
      </div>

      <!-- -- USUARIOS -- -->
      <div id="sec-usuarios" class="section">
        <div class="toolbar">
          <input type="text" id="search-usr" placeholder="Buscar usuario…" oninput="filterTable('usr')" />
          <select id="filter-rol" onchange="filterTable('usr')">
            <option value="">Todos los roles</option>
            <option value="admin">Administrador</option>
            <option value="tecnico">Técnico</option>
            <option value="visor">Visor</option>
          </select>
          <button class="btn btn-navy" onclick="recargarUsuarios()">
            <i class="ti ti-refresh"></i> Recargar
          </button>
          <button class="btn btn-navy" onclick="nuevoUsuario()">
            <i class="ti ti-plus"></i> Nuevo
          </button>
        </div>
        <div class="bulk-bar" id="bulk-usr">
          <i class="ti ti-checkbox"></i>
          <span id="bulk-count-usr">0</span> seleccionados
          <button class="btn btn-danger-sm" style="margin-left:auto" onclick="eliminarSeleccionados('usr')">
            <i class="ti ti-trash"></i> Eliminar seleccionados
          </button>
        </div>
        <div class="main-layout">
          <div class="table-wrap">
            <table class="data-table" id="table-usr">
              <thead>
                <tr>
                  <th><input type="checkbox" id="check-all-usr" onchange="toggleAll('usr')" /></th>
                  <th>ID</th><th>Usuario</th><th>Rol</th><th>Acciones</th>
                </tr>
              </thead>
              <tbody id="tbody-usr"></tbody>
            </table>
            <div class="pagination" id="pag-usr"></div>
          </div>
          <div class="editor-panel" id="editor-usr">
            <h3>
              <span><i class="ti ti-user-edit"></i> Editar usuario</span>
              <button class="close-editor" onclick="cerrarEditor('usr')"><i class="ti ti-x"></i></button>
            </h3>
            <div id="editor-id-usr" class="id-badge" style="margin-bottom:12px"></div>
            <div class="field-group"><label>Usuario</label><input type="text" id="uf-nombre" /></div>
            <div class="field-group"><label>Rol</label>
              <select id="uf-rol">
                <option value="admin">Administrador</option>
                <option value="tecnico">Técnico</option>
                <option value="visor">Visor (solo lectura)</option>
              </select>
            </div>
            <div class="field-group"><label>Contraseña nueva</label><input type="password" id="uf-pass" placeholder="Dejar en blanco = sin cambios" /></div>
            <div class="admin-divider"></div>
            <div class="editor-actions">
              <button class="btn btn-navy" onclick="guardarEditor('usr')"><i class="ti ti-device-floppy"></i> Guardar</button>
              <button class="btn btn-ghost" onclick="cerrarEditor('usr')">Cancelar</button>
            </div>
          </div>
        </div>
      </div>

      <!-- -- UNIDADES -- -->
      <div id="sec-unidades" class="section">
        <div class="toolbar">
          <input type="text" id="search-uni" placeholder="Buscar unidad…" oninput="filterTable('uni')" />
          <button class="btn btn-navy" onclick="recargarUnidades()">
            <i class="ti ti-refresh"></i> Recargar
          </button>
        </div>
        <div style="display:flex;align-items:center;gap:10px;margin:0 0 14px;padding:12px 16px;background:#eef2ff;border:1px solid #c7d2fe;border-radius:10px;">
          <i class="ti ti-search" style="color:#6366f1;font-size:18px;flex-shrink:0;"></i>
          <input type="text" id="ficha-search-input" placeholder="Buscar ficha por #económico, VIN, Reefer Serial, Motor, Compresor…"
            style="flex:1;border:1px solid #c7d2fe;border-radius:7px;padding:8px 12px;font-size:14px;outline:none;"
            onkeydown="if(event.key==='Enter')buscarFichaUnidad()" />
          <button onclick="buscarFichaUnidad()" style="background:#6366f1;color:white;border:none;border-radius:7px;padding:8px 18px;font-weight:600;cursor:pointer;font-size:14px;white-space:nowrap;">
            🗂️ Ver ficha
          </button>
        </div>
        <div class="bulk-bar" id="bulk-uni">
          <i class="ti ti-checkbox"></i>
          <span id="bulk-count-uni">0</span> seleccionados
          <button class="btn btn-danger-sm" style="margin-left:auto" onclick="eliminarSeleccionados('uni')">
            <i class="ti ti-trash"></i> Eliminar seleccionados
          </button>
        </div>
        <div class="main-layout">
          <div class="table-wrap">
            <table class="data-table" id="table-uni">
              <thead>
                <tr>
                  <th><input type="checkbox" id="check-all-uni" onchange="toggleAll('uni')" /></th>
                  <th>ID</th><th>#Económico</th><th>Lote</th><th>VIN</th><th>Modelo</th><th>Acciones</th>
                </tr>
              </thead>
              <tbody id="tbody-uni"></tbody>
            </table>
            <div class="pagination" id="pag-uni"></div>
          </div>
          <div class="editor-panel" id="editor-uni">
            <h3>
              <span><i class="ti ti-truck"></i> Editar unidad</span>
              <button class="close-editor" onclick="cerrarEditor('uni')"><i class="ti ti-x"></i></button>
            </h3>
            <div id="editor-id-uni" class="id-badge" style="margin-bottom:12px"></div>
            <div class="field-group"><label>#Económico</label><input type="text" id="nf-placa" /></div>
            <div class="field-group"><label>Lote</label><input type="text" id="nf-lote" /></div>
            <div class="field-group"><label>VIN</label><input type="text" id="nf-vin" /></div>
            <div class="field-group"><label>Modelo Reefer</label><input type="text" id="nf-modelo" /></div>
            <div class="admin-divider"></div>
            <div class="editor-actions">
              <button class="btn btn-navy" onclick="guardarEditor('uni')"><i class="ti ti-device-floppy"></i> Guardar</button>
              <button class="btn btn-ghost" onclick="cerrarEditor('uni')">Cancelar</button>
            </div>
          </div>
        </div>
      </div>

      <!-- -- SQL -- -->
      <div id="sec-sql" class="section">
        <div class="admin-notice"><i class="ti ti-info-circle"></i> Ejecuta consultas directas. Los cambios son permanentes.</div>
        <div class="sql-presets">
          <button onclick="setSQL('SELECT * FROM asignaciones;')">asignaciones</button>
          <button onclick="setSQL('SELECT * FROM usuarios;')">usuarios</button>
          <button onclick="setSQL('SELECT * FROM unidades;')">unidades</button>
          <button onclick="setSQL('SELECT * FROM tickets;')">tickets</button>
          <button onclick="setSQL('SELECT * FROM inventarios;')">inventarios</button>
          <button onclick="setSQL(&quot;DELETE FROM asignaciones WHERE estado = 'cancelado';&quot;)">limpiar cancelados</button>
        </div>
        <textarea class="sql-area" id="sql-input" spellcheck="false">SELECT * FROM asignaciones;</textarea>
        <div style="display:flex; gap:8px; align-items:center;">
          <button class="btn btn-navy" onclick="ejecutarSQL()"><i class="ti ti-player-play"></i> Ejecutar</button>
          <button class="btn btn-ghost" onclick="document.getElementById('sql-input').value=''"><i class="ti ti-eraser"></i> Limpiar</button>
        </div>
        <div class="sql-result" id="sql-result"></div>
      </div>

      <!-- -- EVIDENCIAS -- -->
      <div id="sec-evidencias" class="section">
        <div class="toolbar">
          <select id="ev-select-unidad" onchange="evCargarFotos(1)" style="min-width:200px;">
            <option value="">— Selecciona unidad —</option>
          </select>
          <span id="ev-total-badge" style="font-size:13px;color:var(--color-text-secondary);"></span>
          <button class="btn btn-ghost" onclick="evToggleSeleccion()" id="ev-btn-seleccionar" style="display:none;">
            <i class="ti ti-checkbox"></i> Seleccionar
          </button>
          <button class="btn" style="background:#c0392b;color:#fff;display:none;" onclick="evEliminarSeleccionadas()" id="ev-btn-eliminar">
            <i class="ti ti-trash"></i> Eliminar seleccionadas (<span id="ev-sel-count">0</span>)
          </button>
          <button class="btn btn-navy" onclick="evDescargarZip()" id="ev-btn-zip" style="display:none;">
            <i class="ti ti-download"></i> Descargar ZIP
          </button>
        </div>

        <div id="ev-loading" style="display:none;text-align:center;padding:32px;color:var(--color-text-secondary);">
          <i class="ti ti-loader" style="font-size:28px;"></i><br>Cargando fotos…
        </div>

        <div id="ev-grid" style="
          display:grid;
          grid-template-columns:repeat(auto-fill,minmax(160px,1fr));
          gap:12px;
          margin-top:8px;
        "></div>

        <div id="ev-pagination" style="display:flex;gap:8px;margin-top:16px;align-items:center;flex-wrap:wrap;"></div>

        <!-- Lightbox -->
        <div id="ev-lightbox" style="
          display:none;position:fixed;inset:0;background:rgba(0,0,0,.85);
          z-index:9999;align-items:center;justify-content:center;flex-direction:column;gap:12px;
        " onclick="evCloseLightbox(event)">
          <img id="ev-lb-img" style="max-width:92vw;max-height:82vh;border-radius:8px;object-fit:contain;" />
          <span id="ev-lb-caption" style="color:#e8f0ff;font-size:13px;"></span>
        </div>
      </div>

      <!-- ── LOTES ── -->
      <div id="sec-lotes" class="section">
        <div class="toolbar">
          <button class="btn btn-navy" onclick="lotesCargar()">
            <i class="ti ti-refresh"></i> Recargar
          </button>
          <label style="display:flex;align-items:center;gap:6px;font-size:13px;color:var(--color-text-secondary);cursor:pointer;">
            <input type="checkbox" id="lotes-mostrar-ocultos" onchange="lotesCargar()" style="cursor:pointer;">
            Mostrar lotes ocultos
          </label>
        </div>

        <div id="lotes-loading" style="display:none;text-align:center;padding:32px;color:var(--color-text-secondary);">
          <i class="ti ti-loader" style="font-size:24px;"></i> Cargando lotes…
        </div>
        <div id="lotes-empty" style="display:none;text-align:center;padding:32px;color:var(--color-text-secondary);font-size:13px;">
          No hay lotes registrados.
        </div>

        <div id="lotes-grid" style="
          display:grid;
          grid-template-columns:repeat(auto-fill,minmax(300px,1fr));
          gap:14px;
          margin-top:4px;
        "></div>

        <!-- Modal confirmación ocultar lote -->
        <div id="lotes-modal" style="
          display:none;position:fixed;inset:0;background:rgba(0,0,0,.5);
          z-index:9000;align-items:center;justify-content:center;
        ">
          <div style="
            background:#fff;border-radius:12px;padding:24px;max-width:400px;width:90%;
            box-shadow:0 20px 60px rgba(0,0,0,.3);
          ">
            <h3 style="font-size:15px;font-weight:600;color:var(--navy);margin-bottom:8px;display:flex;align-items:center;gap:8px;">
              <i class="ti ti-eye-off" style="color:#b7640a;"></i>
              Ocultar lote del dashboard
            </h3>
            <p id="lotes-modal-texto" style="font-size:13px;color:var(--color-text-secondary);margin-bottom:16px;line-height:1.5;"></p>
            <label style="display:flex;align-items:center;gap:8px;font-size:13px;margin-bottom:18px;cursor:pointer;">
              <input type="checkbox" id="lotes-modal-backup" style="cursor:pointer;">
              Hacer backup a OneDrive antes de ocultar
            </label>
            <div style="display:flex;gap:10px;">
              <button class="btn btn-navy" style="flex:1;justify-content:center;" onclick="lotesConfirmarOcultar()">
                <i class="ti ti-eye-off"></i> Ocultar
              </button>
              <button class="btn btn-ghost" style="flex:1;justify-content:center;" onclick="lotesModal(false)">
                Cancelar
              </button>
            </div>
          </div>
        </div>
      </div>

    <script>
    const fetchAuth = window.fetchAuth;
    const PER_PAGE = 8;
    const DATA   = { act: [], usr: [], uni: [] };
    const filtered = { act: [], usr: [], uni: [] };
    const pages  = { act: 1, usr: 1, uni: 1 };
    const editing = { act: null, usr: null, uni: null };
    const selected = { act: new Set(), usr: new Set(), uni: new Set() };

    // -- Carga desde API --------------------------------------
    async function recargarActividades() {
        const estado = document.getElementById('filter-estado').value;
        const url = estado ? `/api/asignaciones/?estado=${estado}` : '/api/asignaciones/';
        const res = await fetchAuth(url);
        DATA.act = await res.json();
        filterTable('act');
    }

    async function recargarUsuarios() {
        const res = await fetchAuth('/api/usuarios/');
        DATA.usr = await res.json();
        filterTable('usr');
    }

    async function recargarUnidades() {
        const res = await fetchAuth('/api/unidades/');
        DATA.uni = await res.json();
        filterTable('uni');
    }

    // -- Badges ----------------------------------------------
    function badgeEstado(e) {
        const m = {
            pendiente:'badge-pending', en_proceso:'badge-req',
            completada:'badge-done', solicitado:'badge-req',
            cancelado:'badge-cancel', activo:'badge-done',
            inactivo:'badge-cancel', mantenimiento:'badge-pending',
            admin:'badge-req', tecnico:'badge-pending', visor:'badge-done'
        };
        return `<span class="admin-badge ${m[e]||''}">${e}</span>`;
    }

    // -- Render tablas ----------------------------------------
    function renderAct() {
        const pg = pages.act; const rows = filtered.act;
        const slice = rows.slice((pg-1)*PER_PAGE, pg*PER_PAGE);
        document.getElementById('tbody-act').innerHTML = slice.map(r => `
            <tr id="row-act-${r.id}" class="${editing.act===r.id?'editing':''} ${selected.act.has(r.id)?'selected':''}">
              <td><input type="checkbox" onchange="toggleRow('act',${r.id},this)" ${selected.act.has(r.id)?'checked':''}></td>
              <td><span style="font-family:monospace;font-size:12px;color:#6b7280">${r.id}</span></td>
              <td style="font-weight:500">${r.unidad||''}</td>
              <td>${r.actividad_id||''}</td>
              <td>${r.tecnico||''}</td>
              <td>${badgeEstado(r.estado||'')}</td>
              <td><div class="row-actions">
                <button class="icon-btn edit" onclick="editarFilaAct(${r.id})" title="Editar"><i class="ti ti-edit"></i></button>
                <button class="icon-btn del" onclick="eliminarFilaAct(${r.id})" title="Eliminar"><i class="ti ti-trash"></i></button>
              </div></td>
            </tr>`).join('');
        renderPag('act', rows.length);
    }

    function renderUsr() {
        const pg = pages.usr; const rows = filtered.usr;
        const slice = rows.slice((pg-1)*PER_PAGE, pg*PER_PAGE);
        document.getElementById('tbody-usr').innerHTML = slice.map(r => `
            <tr id="row-usr-${r.id}" class="${editing.usr===r.id?'editing':''} ${selected.usr.has(r.id)?'selected':''}">
              <td><input type="checkbox" onchange="toggleRow('usr',${r.id},this)" ${selected.usr.has(r.id)?'checked':''}></td>
              <td style="font-family:monospace;font-size:12px;color:#6b7280">${r.id}</td>
              <td style="font-weight:500">${r.username||''}</td>
              <td>${badgeEstado(r.role||'')}</td>
              <td><div class="row-actions">
                <button class="icon-btn edit" onclick="editarFilaUsr(${r.id})" title="Editar"><i class="ti ti-edit"></i></button>
                <button class="icon-btn del" onclick="eliminarFilaUsr(${r.id})" title="Eliminar"><i class="ti ti-trash"></i></button>
              </div></td>
            </tr>`).join('');
        renderPag('usr', rows.length);
    }

    function renderUni() {
        const pg = pages.uni; const rows = filtered.uni;
        const slice = rows.slice((pg-1)*PER_PAGE, pg*PER_PAGE);
        document.getElementById('tbody-uni').innerHTML = slice.map(r => `
            <tr id="row-uni-${r.id}" class="${editing.uni===r.id?'editing':''} ${selected.uni.has(r.id)?'selected':''}">
              <td><input type="checkbox" onchange="toggleRow('uni',${r.id},this)" ${selected.uni.has(r.id)?'checked':''}></td>
              <td style="font-family:monospace;font-size:12px;color:#6b7280">${r.id}</td>
              <td style="font-weight:500;font-family:monospace">${r.unit_number||''}</td>
              <td>${r.id_lote||''}</td>
              <td style="font-size:12px;color:#6b7280">${r.vin_number||'—'}</td>
              <td>${r.reefer_model||'—'}</td>
              <td><div class="row-actions">
                <button class="icon-btn" onclick="verFichaUnidad('${r.unit_number}')" title="Ver ficha completa" style="color:#6366f1"><i class="ti ti-file-description"></i></button>
                <button class="icon-btn edit" onclick="editarFilaUni(${r.id})" title="Editar"><i class="ti ti-edit"></i></button>
                <button class="icon-btn del" onclick="eliminarFilaUni(${r.id})" title="Eliminar"><i class="ti ti-trash"></i></button>
              </div></td>
            </tr>`).join('');
        renderPag('uni', rows.length);
    }

    function renderPag(t, total) {
        const pg = pages[t]; const tot = Math.ceil(total/PER_PAGE)||1;
        document.getElementById('pag-'+t).innerHTML = `
            <button onclick="changePage('${t}',-1)" ${pg<=1?'disabled':''}>&#8249;</button>
            <span>Pág ${pg} de ${tot} &nbsp;·&nbsp; ${total} registros</span>
            <button onclick="changePage('${t}',1)" ${pg>=tot?'disabled':''}>&#8250;</button>`;
    }

    function changePage(t,d){ pages[t]+=d; render(t); }
    function render(t){ if(t==='act')renderAct(); else if(t==='usr')renderUsr(); else renderUni(); }

    // -- Filtros ----------------------------------------------
    function filterTable(t) {
        if(t==='act'){
            const q=(document.getElementById('search-act').value||'').toLowerCase();
            const es=document.getElementById('filter-estado').value;
            filtered.act=DATA.act.filter(r=>{
                const match=!q||((r.unidad||'')+(r.tecnico||'')+(r.actividad_id||'')+String(r.id)).toLowerCase().includes(q);
                return match&&(!es||r.estado===es);
            }); pages.act=1; renderAct();
        } else if(t==='usr'){
            const q=(document.getElementById('search-usr').value||'').toLowerCase();
            const rl=document.getElementById('filter-rol').value;
            filtered.usr=DATA.usr.filter(r=>{
                const match=!q||(r.username||'').toLowerCase().includes(q);
                return match&&(!rl||r.role===rl);
            }); pages.usr=1; renderUsr();
        } else {
            const q=(document.getElementById('search-uni').value||'').toLowerCase();
            filtered.uni=DATA.uni.filter(r=>!q||((r.unit_number||'')+(r.id_lote||'')).toLowerCase().includes(q));
            pages.uni=1; renderUni();
        }
    }

    // -- Pestañas ---------------------------------------------
    function showTab(t) {
        ['actividades','usuarios','unidades','sql','evidencias','lotes'].forEach(s=>{
            document.getElementById('sec-'+s).classList.toggle('active',s===t);
            document.getElementById('tab-'+s).classList.toggle('active',s===t);
        });
        if (t === 'evidencias') evInicializar();
        if (t === 'lotes') lotesCargar();
    }

    // ── GALERÍA DE EVIDENCIAS ─────────────────────────────────
    let evPaginaActual = 1;
    let evTotalPages   = 1;
    let evCargado      = false;
    let evModoSeleccion = false;
    let evSeleccionadas = new Set();

    async function evInicializar() {
        if (evCargado) return;
        evCargado = true;
        if (window.role === 'admin') {
            document.getElementById('ev-btn-seleccionar').style.display = 'inline-flex';
        }
        const sel = document.getElementById('ev-select-unidad');
        try {
            const res = await fetchAuth('/api/evidencias/unidades-con-fotos');
            if (!res.ok) return;
            const data = await res.json();
            data.forEach(u => {
                const opt = document.createElement('option');
                opt.value = u.unit_number;
                opt.textContent = `${u.unit_number}  (${u.total} foto${u.total===1?'':'s'})`;
                sel.appendChild(opt);
            });
        } catch(e) { console.error('evInicializar', e); }
    }

    async function evCargarFotos(page = 1) {
        const unidad = document.getElementById('ev-select-unidad').value;
        const grid   = document.getElementById('ev-grid');
        const badge  = document.getElementById('ev-total-badge');
        const pag    = document.getElementById('ev-pagination');
        const loading = document.getElementById('ev-loading');
        const btnZip  = document.getElementById('ev-btn-zip');

        grid.innerHTML = '';
        pag.innerHTML  = '';
        badge.textContent = '';
        btnZip.style.display = 'none';
        evSeleccionadas.clear();
        evActualizarBotonEliminar();

        if (!unidad) return;

        loading.style.display = 'block';
        try {
            const res  = await fetchAuth(`/api/evidencias/lista/${unidad}?page=${page}&per_page=20`);
            loading.style.display = 'none';
            if (!res.ok) { grid.innerHTML = '<p style="color:red">Error al cargar evidencias.</p>'; return; }
            const data = await res.json();

            evPaginaActual = data.page;
            evTotalPages   = data.pages;
            badge.textContent = `${data.total} foto${data.total===1?'':'s'}`;
            btnZip.style.display = data.total > 0 ? 'inline-flex' : 'none';

            if (data.fotos.length === 0) {
                grid.innerHTML = '<p style="color:var(--color-text-secondary);padding:24px 0;">No hay fotos para esta unidad.</p>';
                return;
            }

            data.fotos.forEach(f => {
                const card = document.createElement('div');
                card.style.cssText = 'position:relative;background:#f4f6fb;border-radius:10px;overflow:hidden;cursor:pointer;box-shadow:0 2px 8px rgba(0,0,0,.07);transition:transform .15s;';
                card.onmouseenter = ()=>card.style.transform='scale(1.03)';
                card.onmouseleave = ()=>card.style.transform='scale(1)';
                card.onclick = (ev)=>{
                    if (evModoSeleccion) {
                        ev.stopPropagation();
                        evToggleFoto(f.id, card);
                    } else {
                        evAbrirLightbox(f.id, f.nombre, f.tecnico, f.fecha);
                    }
                };

                const img = document.createElement('img');
                img.alt   = f.nombre;
                img.loading = 'lazy';
                img.style.cssText = 'width:100%;height:130px;object-fit:cover;display:block;';
                img.onerror = ()=>{ img.style.display='none'; };
                fetchAuth(`/api/evidencias/foto/${f.id}`)
                    .then(r => r.ok ? r.blob() : Promise.reject())
                    .then(blob => { img.src = URL.createObjectURL(blob); })
                    .catch(() => { img.style.display='none'; });

                const info = document.createElement('div');
                info.style.cssText = 'padding:6px 8px;font-size:11px;color:var(--color-text-secondary);line-height:1.5;';
                info.innerHTML = `<b style="color:var(--color-text-primary);font-size:12px;">${f.nombre.length>22?f.nombre.slice(0,19)+'…':f.nombre}</b><br>
                  👷 ${f.tecnico||'—'}<br>
                  ${f.fecha ? '🗓 '+f.fecha.slice(0,10) : ''}`;

                const checkbox = document.createElement('div');
                checkbox.className = 'ev-checkbox';
                checkbox.dataset.id = f.id;
                checkbox.style.cssText = 'position:absolute;top:6px;left:6px;width:22px;height:22px;'
                    + 'border-radius:50%;border:2px solid #fff;background:rgba(0,0,0,.35);'
                    + 'display:' + (evModoSeleccion ? 'flex' : 'none') + ';align-items:center;justify-content:center;'
                    + 'font-size:13px;color:#fff;z-index:2;';
                checkbox.textContent = evSeleccionadas.has(f.id) ? '✓' : '';
                if (evSeleccionadas.has(f.id)) {
                    checkbox.style.background = 'var(--color-navy, #1F4E78)';
                    checkbox.style.borderColor = 'var(--color-navy, #1F4E78)';
                }

                card.appendChild(img);
                card.appendChild(info);
                card.appendChild(checkbox);
                grid.appendChild(card);
            });

            // Paginación
            if (evTotalPages > 1) {
                const makeBtn = (label, pg, disabled=false) => {
                    const b = document.createElement('button');
                    b.className = 'btn ' + (pg===evPaginaActual ? 'btn-navy' : 'btn-ghost');
                    b.textContent = label;
                    b.disabled = disabled;
                    b.style.padding = '6px 12px';
                    b.onclick = ()=>evCargarFotos(pg);
                    return b;
                };
                pag.appendChild(makeBtn('‹', evPaginaActual-1, evPaginaActual===1));
                const start = Math.max(1, evPaginaActual-2);
                const end   = Math.min(evTotalPages, start+4);
                for (let p=start; p<=end; p++) pag.appendChild(makeBtn(p, p));
                pag.appendChild(makeBtn('›', evPaginaActual+1, evPaginaActual===evTotalPages));
                const lbl = document.createElement('span');
                lbl.style.cssText='font-size:12px;color:var(--color-text-secondary);';
                lbl.textContent = `Página ${evPaginaActual} de ${evTotalPages}`;
                pag.appendChild(lbl);
            }
        } catch(e) {
            loading.style.display = 'none';
            grid.innerHTML = '<p style="color:red">Error de red.</p>';
            console.error('evCargarFotos', e);
        }
    }

    function evAbrirLightbox(id, nombre, tecnico, fecha) {
        const lb  = document.getElementById('ev-lightbox');
        const img = document.getElementById('ev-lb-img');
        const cap = document.getElementById('ev-lb-caption');
        img.src   = '';
        cap.textContent = `${nombre}  ·  👷 ${tecnico||'—'}  ·  ${fecha?fecha.slice(0,10):''}`;
        lb.style.display = 'flex';
        fetchAuth(`/api/evidencias/foto/${id}`)
            .then(r => r.ok ? r.blob() : Promise.reject())
            .then(blob => { img.src = URL.createObjectURL(blob); })
            .catch(() => { img.alt = 'Error al cargar imagen'; });
    }

    function evCloseLightbox(e) {
        if (e.target.id === 'ev-lightbox' || e.target.id === 'ev-lb-img') {
            document.getElementById('ev-lightbox').style.display = 'none';
        }
    }

    async function evDescargarZip() {
        const unidad = document.getElementById('ev-select-unidad').value;
        if (!unidad) return;
        const res = await fetchAuth(`/api/evidencias/download/${unidad}`);
        if (!res.ok) { alert('Error al descargar el ZIP'); return; }
        const blob = await res.blob();
        const url  = URL.createObjectURL(blob);
        const a    = document.createElement('a');
        a.href = url; a.download = `evidencias_${unidad}.zip`; a.click();
        URL.revokeObjectURL(url);
    }

    function evToggleSeleccion() {
        evModoSeleccion = !evModoSeleccion;
        evSeleccionadas.clear();
        evActualizarBotonEliminar();
        const btn = document.getElementById('ev-btn-seleccionar');
        btn.classList.toggle('btn-navy', evModoSeleccion);
        btn.classList.toggle('btn-ghost', !evModoSeleccion);
        btn.innerHTML = evModoSeleccion
            ? '<i class="ti ti-x"></i> Cancelar selección'
            : '<i class="ti ti-checkbox"></i> Seleccionar';
        document.querySelectorAll('.ev-checkbox').forEach(cb => {
            cb.style.display = evModoSeleccion ? 'flex' : 'none';
            cb.textContent = '';
            cb.style.background = 'rgba(0,0,0,.35)';
            cb.style.borderColor = '#fff';
        });
    }

    function evToggleFoto(id, card) {
        const cb = card.querySelector('.ev-checkbox');
        if (evSeleccionadas.has(id)) {
            evSeleccionadas.delete(id);
            cb.textContent = '';
            cb.style.background = 'rgba(0,0,0,.35)';
            cb.style.borderColor = '#fff';
        } else {
            evSeleccionadas.add(id);
            cb.textContent = '✓';
            cb.style.background = 'var(--color-navy, #1F4E78)';
            cb.style.borderColor = 'var(--color-navy, #1F4E78)';
        }
        evActualizarBotonEliminar();
    }

    function evActualizarBotonEliminar() {
        const btn = document.getElementById('ev-btn-eliminar');
        const count = document.getElementById('ev-sel-count');
        count.textContent = evSeleccionadas.size;
        btn.style.display = evSeleccionadas.size > 0 ? 'inline-flex' : 'none';
    }

    async function evEliminarSeleccionadas() {
        if (evSeleccionadas.size === 0) return;
        const ids = Array.from(evSeleccionadas);
        if (!confirm(`¿Eliminar ${ids.length} foto(s)? Esta acción no se puede deshacer.`)) return;

        try {
            const res = await fetchAuth('/api/evidencias/eliminar', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ ids })
            });
            if (!res.ok) {
                const err = await res.json().catch(()=>({}));
                alert('Error al eliminar: ' + (err.detail || res.statusText));
                return;
            }
            evToggleSeleccion(); // salir del modo selección
            await evCargarFotos(evPaginaActual);
        } catch(e) {
            alert('Error de red al eliminar.');
            console.error('evEliminarSeleccionadas', e);
        }
    }

    // -- Editar Actividades -----------------------------------
    function editarFilaAct(id) {
        editing.act=id;
        const r=DATA.act.find(x=>x.id===id); if(!r) return;
        document.getElementById('editor-act').classList.add('visible');
        document.getElementById('editor-id-act').textContent='ID: '+id;
        document.getElementById('ef-vehiculo').value=r.unidad||'';
        document.getElementById('ef-tecnico').value=r.tecnico||'';
        document.getElementById('ef-estado').value=r.estado||'pendiente';
        renderAct();
    }

    async function guardarEditor(t) {
        if(t==='act'){
            const id=editing.act;
            const estado=document.getElementById('ef-estado').value;
            await fetchAuth('/api/asignaciones/'+id, {
                method:'PUT', headers:{'Content-Type':'application/json'},
                body:JSON.stringify({estado})
            });
            cerrarEditor('act'); recargarActividades();
        } else if(t==='usr'){
            const id=editing.usr;
            const username=document.getElementById('uf-nombre').value;
            const role=document.getElementById('uf-rol').value;
            const pass=document.getElementById('uf-pass').value;
            await fetchAuth('/api/usuarios/'+id, {
                method:'PUT', headers:{'Content-Type':'application/json'},
                body:JSON.stringify({username, role})
            });
            if(pass) await fetchAuth('/api/usuarios/'+id+'/password', {
                method:'PUT', headers:{'Content-Type':'application/json'},
                body:JSON.stringify({new_password:pass})
            });
            cerrarEditor('usr'); recargarUsuarios();
        } else {
            const id=editing.uni;
            const unit_number=document.getElementById('nf-placa').value;
            const id_lote=document.getElementById('nf-lote').value;
            const vin_number=document.getElementById('nf-vin').value;
            const reefer_model=document.getElementById('nf-modelo').value;
            await fetchAuth('/api/unidades/'+id, {
                method:'PUT', headers:{'Content-Type':'application/json'},
                body:JSON.stringify({unit_number, id_lote, vin_number, reefer_model})
            });
            cerrarEditor('uni'); recargarUnidades();
        }
    }

    function cerrarEditor(t){
        editing[t]=null;
        document.getElementById('editor-'+t).classList.remove('visible');
        render(t);
    }

    // -- Editar Usuarios --------------------------------------
    function editarFilaUsr(id) {
        editing.usr=id;
        const r=DATA.usr.find(x=>x.id===id); if(!r) return;
        document.getElementById('editor-usr').classList.add('visible');
        document.getElementById('editor-id-usr').textContent='ID: '+id;
        document.getElementById('uf-nombre').value=r.username||'';
        document.getElementById('uf-rol').value=r.role||'tecnico';
        document.getElementById('uf-pass').value='';
        renderUsr();
    }

    async function nuevoUsuario() {
        const username=prompt('Nombre de usuario:'); if(!username) return;
        const password=prompt('Contraseña:'); if(!password) return;
        const role=prompt('Rol (admin/tecnico/visor):','tecnico'); if(!role) return;
        const res=await fetchAuth('/api/usuarios/', {
            method:'POST', headers:{'Content-Type':'application/json'},
            body:JSON.stringify({username, password, role})
        });
        if(res.ok){ recargarUsuarios(); } else { alert('Error al crear usuario'); }
    }

    async function eliminarFilaUsr(id) {
        const r=DATA.usr.find(x=>x.id===id);
        if(!confirm('¿Eliminar usuario "'+( r?.username||id)+'"?')) return;
        await fetchAuth('/api/usuarios/'+id, {method:'DELETE'});
        recargarUsuarios();
    }

    // -- Editar Unidades --------------------------------------
    function editarFilaUni(id) {
        editing.uni=id;
        const r=DATA.uni.find(x=>x.id===id); if(!r) return;
        document.getElementById('editor-uni').classList.add('visible');
        document.getElementById('editor-id-uni').textContent='#: '+r.unit_number;
        document.getElementById('nf-placa').value=r.unit_number||'';
        document.getElementById('nf-lote').value=r.id_lote||'';
        document.getElementById('nf-vin').value=r.vin_number||'';
        document.getElementById('nf-modelo').value=r.reefer_model||'';
        renderUni();
    }

    async function eliminarFilaUni(id) {
        const r=DATA.uni.find(x=>x.id===id);
        if(!confirm('¿Eliminar unidad "'+(r?.unit_number||id)+'"?')) return;
        await fetchAuth('/api/unidades/'+id, {method:'DELETE'});
        recargarUnidades();
    }

    // -- Eliminar Actividades ---------------------------------
    async function eliminarFilaAct(id) {
        if(!confirm('¿Eliminar actividad '+id+'?')) return;
        await fetchAuth('/api/asignaciones/'+id, {method:'DELETE'});
        recargarActividades();
    }

    // -- Selección múltiple -----------------------------------
    function toggleRow(t,id,cb){
        if(cb.checked) selected[t].add(id); else selected[t].delete(id);
        updateBulk(t); render(t);
    }

    function toggleAll(t){
        const cb=document.getElementById('check-all-'+t);
        filtered[t].forEach(r=>{ if(cb.checked) selected[t].add(r.id); else selected[t].delete(r.id); });
        updateBulk(t); render(t);
    }

    function updateBulk(t){
        const bar=document.getElementById('bulk-'+t);
        const n=selected[t].size;
        bar.classList.toggle('visible',n>0);
        document.getElementById('bulk-count-'+t).textContent=n;
    }

    async function eliminarSeleccionados(t) {
        const n=selected[t].size;
        if(!confirm('¿Eliminar '+n+' registros seleccionados?')) return;
        const endpoint = t==='act' ? '/api/asignaciones/' : t==='usr' ? '/api/usuarios/' : '/api/unidades/';
        for(const id of selected[t]) await fetchAuth(endpoint+id, {method:'DELETE'});
        selected[t].clear();
        if(t==='act') recargarActividades();
        else if(t==='usr') recargarUsuarios();
        else recargarUnidades();
        updateBulk(t);
    }

    // -- SQL --------------------------------------------------
    function setSQL(q){ document.getElementById('sql-input').value=q; }
    async function ejecutarSQL(){
        const sql=document.getElementById('sql-input').value.trim();
        const res=document.getElementById('sql-result');
        res.classList.add('visible');
        if(!sql){ res.textContent='Error: consulta vacía.'; return; }
        res.textContent='Ejecutando…';
        try {
            const r=await fetchAuth('/api/admin/execute-sql', {
                method:'POST', headers:{'Content-Type':'application/json'},
                body:JSON.stringify({sql})
            });
            const data=await r.json();
            if(data.error){ res.textContent='Error: '+data.error; return; }
            if(Array.isArray(data)&&data.length){
                const keys=Object.keys(data[0]);
                res.textContent=[keys.join(' | '),'-'.repeat(60),...data.map(row=>keys.map(k=>String(row[k]??'')).join(' | '))].join('\\n');
            } else { res.textContent='Consulta ejecutada. '+JSON.stringify(data); }
        } catch(e){ res.textContent='Error: '+e.message; }
    }

    // ── GESTIÓN DE LOTES ──────────────────────────────────────
    let _loteSeleccionado = null;

    async function lotesCargar() {
        const mostrarOcultos = document.getElementById('lotes-mostrar-ocultos').checked;
        const grid    = document.getElementById('lotes-grid');
        const loading = document.getElementById('lotes-loading');
        const empty   = document.getElementById('lotes-empty');

        grid.style.display = 'none';
        empty.style.display = 'none';
        loading.style.display = 'block';

        try {
            const res  = await fetchAuth('/api/unidades/lotes');
            const data = await res.json();
            loading.style.display = 'none';

            const filtrados = mostrarOcultos ? data : data.filter(l => !l.oculto);
            if (!filtrados.length) { empty.style.display = 'block'; return; }

            grid.style.display = 'grid';
            grid.innerHTML = filtrados.map((l, idx) => {
                const oculto = l.oculto;
                const safeId = String(idx);  // índice seguro para el DOM
                const badgeHtml = oculto
                    ? `<span style="background:#fff3cd;color:#7a4e00;font-size:11px;font-weight:500;padding:2px 8px;border-radius:999px;"><i class="ti ti-eye-off"></i> Oculto</span>`
                    : `<span style="background:#d4edda;color:#155724;font-size:11px;font-weight:500;padding:2px 8px;border-radius:999px;"><i class="ti ti-eye"></i> Visible</span>`;
                return `
                <div data-lote-idx="${safeId}" style="
                  background:#fff;border:0.5px solid var(--color-border-secondary);
                  border-radius:12px;padding:18px;display:flex;flex-direction:column;gap:10px;
                  ${oculto ? 'opacity:.7;' : ''}
                ">
                  <div style="display:flex;align-items:center;justify-content:space-between;gap:8px;">
                    <span style="font-size:15px;font-weight:600;color:var(--navy);">
                      <i class="ti ti-layout-grid" style="font-size:14px;"></i>
                      ${l.id_lote}
                    </span>
                    ${badgeHtml}
                  </div>
                  <div style="font-size:13px;color:var(--color-text-secondary);">
                    <i class="ti ti-truck"></i> ${l.total_unidades} unidad${l.total_unidades!==1?'es':''}
                  </div>
                  <div style="display:flex;gap:8px;flex-wrap:wrap;margin-top:2px;">
                    <button class="btn btn-ghost lote-reporte" data-idx="${safeId}" style="font-size:12px;padding:5px 10px;">
                      <i class="ti ti-file-spreadsheet"></i> Reporte Excel
                    </button>
                    <button class="btn btn-ghost lote-backup" data-idx="${safeId}" style="font-size:12px;padding:5px 10px;">
                      <i class="ti ti-download"></i> Backup ZIP
                    </button>
                    ${oculto
                        ? `<button class="btn btn-navy lote-mostrar" data-idx="${safeId}" style="font-size:12px;padding:5px 10px;">
                             <i class="ti ti-eye"></i> Mostrar
                           </button>`
                        : `<button class="btn lote-ocultar" data-idx="${safeId}" style="font-size:12px;padding:5px 10px;background:var(--warn);color:#fff;">
                             <i class="ti ti-eye-off"></i> Ocultar
                           </button>`
                    }
                  </div>
                </div>`;
            }).join('');

            // Guardar datos en mapa indexado para acceso seguro desde los handlers
            window._lotesData = {};
            filtrados.forEach((l, idx) => { window._lotesData[String(idx)] = l; });

            // Bind de eventos con el valor real del id_lote (sin pasar por HTML)
            grid.querySelectorAll('.lote-reporte').forEach(btn => {
                btn.addEventListener('click', () => lotesDescargarReporte(window._lotesData[btn.dataset.idx].id_lote));
            });
            grid.querySelectorAll('.lote-backup').forEach(btn => {
                btn.addEventListener('click', () => lotesDescargarBackup(window._lotesData[btn.dataset.idx].id_lote));
            });
            grid.querySelectorAll('.lote-mostrar').forEach(btn => {
                btn.addEventListener('click', () => lotesMostrar(window._lotesData[btn.dataset.idx].id_lote));
            });
            grid.querySelectorAll('.lote-ocultar').forEach(btn => {
                btn.addEventListener('click', () => {
                    const l = window._lotesData[btn.dataset.idx];
                    lotesModal(true, l.id_lote, l.total_unidades);
                });
            });

        } catch(e) {
            loading.style.display = 'none';
            empty.style.display = 'block';
            empty.textContent = 'Error al cargar lotes: ' + e.message;
        }
    }

    async function lotesDescargarReporte(id_lote) {
        const url = `/api/reportes/lote?id_lote=${encodeURIComponent(id_lote)}`;
        const res = await fetchAuth(url);
        if (!res.ok) {
            let detalle = 'No se pudo generar el reporte de este lote';
            try { const d = await res.json(); detalle = d.detail || detalle; } catch(e){}
            alert(detalle); return;
        }
        const blob = await res.blob();
        const a = document.createElement('a');
        a.href = URL.createObjectURL(blob);
        a.download = `Reporte_Lote_${id_lote}.xlsx`;
        a.click();
    }

    async function lotesDescargarBackup(id_lote) {
        const url = `/api/unidades/lotes/backup?id_lote=${encodeURIComponent(id_lote)}`;
        const res = await fetchAuth(url);
        if (!res.ok) {
            let detalle = 'No se pudo generar el backup de este lote';
            try { const d = await res.json(); detalle = d.detail || detalle; } catch(e){}
            alert(detalle); return;
        }
        const blob = await res.blob();
        const a = document.createElement('a');
        a.href = URL.createObjectURL(blob);
        a.download = `backup_lote_${id_lote}.zip`;
        a.click();
    }

    function lotesModal(visible, id_lote, total) {
        _loteSeleccionado = visible ? id_lote : null;
        const modal = document.getElementById('lotes-modal');
        modal.style.display = visible ? 'flex' : 'none';
        if (visible) {
            document.getElementById('lotes-modal-texto').textContent =
                `¿Ocultar el lote "${id_lote}" (${total} unidad${total!==1?'es':''}) del dashboard y KPIs? Los datos se conservan en la base de datos y puedes mostrarlo nuevamente.`;
            document.getElementById('lotes-modal-backup').checked = false;
        }
    }

    async function lotesConfirmarOcultar() {
        if (!_loteSeleccionado) return;
        const backup = document.getElementById('lotes-modal-backup').checked;
        const btn = document.querySelector('#lotes-modal .btn-navy');
        btn.disabled = true;
        btn.innerHTML = '<i class="ti ti-loader"></i> Ocultando…';
        try {
            const url = `/api/unidades/lotes/ocultar?id_lote=${encodeURIComponent(_loteSeleccionado)}&backup_onedrive=${backup}`;
            const res = await fetchAuth(url, { method: 'POST' });
            let data = {};
            try { data = await res.json(); } catch(e) {}
            if (!res.ok) { alert(data.detail || `Error ${res.status} al ocultar lote`); return; }
            lotesModal(false);
            let msg = data.mensaje;
            if (data.backup_aviso) msg += '\\n' + data.backup_aviso;
            alert(msg);
            lotesCargar();
        } catch(e) {
            alert('Error de red: ' + e.message);
        } finally {
            btn.disabled = false;
            btn.innerHTML = '<i class="ti ti-eye-off"></i> Ocultar';
        }
    }

    async function lotesMostrar(id_lote) {
        if (!confirm(`¿Mostrar el lote "${id_lote}" en el dashboard nuevamente?`)) return;
        const url = `/api/unidades/lotes/mostrar?id_lote=${encodeURIComponent(id_lote)}`;
        const res = await fetchAuth(url, { method: 'POST' });
        let data = {};
        try { data = await res.json(); } catch(e) {}
        if (!res.ok) { alert(data.detail || `Error ${res.status} al mostrar lote`); return; }
        alert(data.mensaje);
        lotesCargar();
    }

    // -- Ficha de unidad (modal de búsqueda) -------------------
    function mostrarModal(html) {
        const modal = document.createElement('div');
        modal.className = 'modal';
        modal.style.display = 'flex';
        modal.innerHTML = html;
        document.body.appendChild(modal);
        return modal;
    }
    function cerrarModal() {
        const modal = document.querySelector('.modal');
        if (modal) document.body.removeChild(modal);
    }

    function buscarFichaUnidad() {
        const q = (document.getElementById('ficha-search-input').value || '').trim();
        if (!q) { alert('Escribe un número económico, VIN, serial u otro identificador.'); return; }
        verFichaUnidad(q);
    }

    async function verFichaUnidad(unitNumber) {
        mostrarModal(`<div class="modal-content" style="max-width:760px;max-height:85vh;overflow-y:auto;">
            <h3 style="margin:0 0 12px;display:flex;align-items:center;gap:8px;">
                <span style="font-size:22px;">🗂️</span> Cargando ficha de <code>${unitNumber}</code>…
            </h3>
            <p style="color:#6b7280;">Un momento…</p>
            <button class="btn-danger" onclick="cerrarModal()" style="margin-top:12px;">Cerrar</button>
        </div>`);

        let data;
        try {
            const res = await fetchAuth('/api/unidades/ficha?q=' + encodeURIComponent(unitNumber));
            if (!res.ok) {
                const err = await res.json().catch(() => ({ detail: 'Error desconocido' }));
                cerrarModal();
                mostrarModal(`<div class="modal-content"><h3>⚠️ No encontrado</h3><p>${err.detail || 'No se pudo cargar la ficha.'}</p><button class="btn-danger" onclick="cerrarModal()">Cerrar</button></div>`);
                return;
            }
            data = await res.json();
        } catch (e) {
            cerrarModal();
            mostrarModal(`<div class="modal-content"><h3>⚠️ Error de red</h3><p>${e.message}</p><button class="btn-danger" onclick="cerrarModal()">Cerrar</button></div>`);
            return;
        }

        if (data.seleccion_multiple) {
            const opciones = (data.unidades || []).map(u => `
                <button onclick="verFichaUnidad('${u.unit_number}')" style="display:flex;justify-content:space-between;align-items:center;width:100%;text-align:left;background:#f8fafc;border:1px solid #e2e8f0;border-radius:8px;padding:10px 14px;margin-bottom:8px;cursor:pointer;font-size:13px;">
                    <span><b style="font-family:monospace;">${u.unit_number}</b> · ${u.reefer_model||'—'}</span>
                    <span style="color:#6b7280;font-family:monospace;font-size:12px;">${u.vin_number||'—'}</span>
                </button>`).join('');
            cerrarModal();
            mostrarModal(`<div class="modal-content" style="max-width:560px;max-height:80vh;overflow-y:auto;">
                <h3 style="margin:0 0 8px;">🗂️ Varias unidades encontradas</h3>
                <p style="color:#6b7280;font-size:13px;margin:0 0 14px;">El criterio <code>${data.criterio}</code> coincide con ${data.unidades.length} unidades. Elige cuál ver:</p>
                ${opciones}
                <button class="btn-danger" onclick="cerrarModal()" style="margin-top:8px;">Cerrar</button>
            </div>`);
            return;
        }

        const u = data.unidad;
        const seriesRows = [
            ['VIN', u.vin_number], ['Reefer Serial', u.reefer_serial], ['Modelo Reefer', u.reefer_model],
            ['Evap. MJS11', u.evaporator_serial_mjs11], ['Evap. MJD22', u.evaporator_serial_mjd22],
            ['Motor', u.engine_serial], ['Compresor', u.compressor_serial],
            ['Generador', u.generator_serial], ['Cargador Batería', u.battery_charger_serial],
        ].filter(([,v]) => v).map(([k,v]) => `<tr><td style="color:#6b7280;padding:4px 10px 4px 0;white-space:nowrap;">${k}</td><td style="font-family:monospace;font-size:13px;">${v}</td></tr>`).join('');

        const asnRows = (data.asignaciones || []).slice(0,15).map(a => `
            <tr style="border-bottom:1px solid #f1f5f9;">
                <td style="padding:4px 8px 4px 0;color:#6b7280;font-size:12px;">#${a.id}</td>
                <td style="padding:4px 8px;">${a.actividad_id||'—'}</td>
                <td style="padding:4px 8px;">${a.tecnico||'—'}</td>
                <td style="padding:4px 8px;"><span style="background:${a.estado==='completado'?'#dcfce7':a.estado==='en_proceso'?'#fef9c3':'#f1f5f9'};color:${a.estado==='completado'?'#16a34a':a.estado==='en_proceso'?'#b45309':'#6b7280'};padding:2px 8px;border-radius:999px;font-size:11px;font-weight:600;">${a.estado||'—'}</span></td>
                <td style="padding:4px 0;color:#6b7280;font-size:11px;">${(a.fecha_asignacion||'').slice(0,10)}</td>
            </tr>`).join('');

        const tkRows = (data.tickets || []).slice(0,10).map(t => `
            <tr style="border-bottom:1px solid #f1f5f9;">
                <td style="padding:4px 8px 4px 0;color:#6b7280;font-size:12px;">#${t.id}</td>
                <td style="padding:4px 8px;">${t.tipo||'—'}</td>
                <td style="padding:4px 8px;max-width:200px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;" title="${(t.descripcion||'').replace(/"/g,'&quot;')}">${t.descripcion||'—'}</td>
                <td style="padding:4px 0;"><span style="background:${t.estado==='abierto'?'#fee2e2':'#dcfce7'};color:${t.estado==='abierto'?'#dc2626':'#16a34a'};padding:2px 8px;border-radius:999px;font-size:11px;font-weight:600;">${t.estado||'—'}</span></td>
            </tr>`).join('');

        const lote = u.id_lote ? `<span style="background:#e0e7ff;color:#4338ca;padding:2px 10px;border-radius:999px;font-size:12px;font-weight:600;">${u.id_lote}</span>${u.oculto?'<span style="margin-left:6px;background:#fee2e2;color:#dc2626;padding:2px 8px;border-radius:999px;font-size:11px;">🙈 Oculto</span>':''}` : '<span style="color:#9ca3af">Sin lote</span>';

        cerrarModal();
        mostrarModal(`<div class="modal-content" style="max-width:760px;max-height:85vh;overflow-y:auto;padding:24px;">
            <div style="display:flex;align-items:flex-start;justify-content:space-between;margin-bottom:20px;">
                <div>
                    <h2 style="margin:0;font-size:22px;font-family:monospace;">📋 ${u.unit_number}</h2>
                    <div style="margin-top:6px;">${lote}</div>
                </div>
                <button class="btn-danger" onclick="cerrarModal()" style="flex-shrink:0;">✕ Cerrar</button>
            </div>

            <h4 style="margin:0 0 8px;color:#374151;border-bottom:1px solid #e5e7eb;padding-bottom:6px;">🔢 Series registradas</h4>
            ${seriesRows ? `<table style="width:100%;margin-bottom:16px;"><tbody>${seriesRows}</tbody></table>` : '<p style="color:#9ca3af;font-size:13px;margin-bottom:16px;">Sin series registradas.</p>'}

            <h4 style="margin:0 0 8px;color:#374151;border-bottom:1px solid #e5e7eb;padding-bottom:6px;">🔧 Actividades / Asignaciones <span style="font-weight:400;color:#6b7280;font-size:13px;">(${data.asignaciones?.length||0} total)</span></h4>
            ${asnRows ? `<table style="width:100%;margin-bottom:16px;font-size:13px;">
                <thead><tr style="color:#9ca3af;font-size:11px;text-transform:uppercase;">
                    <th style="text-align:left;padding:0 8px 6px 0;">ID</th><th style="text-align:left;padding:0 8px 6px;">Actividad</th>
                    <th style="text-align:left;padding:0 8px 6px;">Técnico</th><th style="text-align:left;padding:0 8px 6px;">Estado</th>
                    <th style="text-align:left;padding:0 0 6px;">Fecha</th>
                </tr></thead><tbody>${asnRows}</tbody></table>` : '<p style="color:#9ca3af;font-size:13px;margin-bottom:16px;">Sin actividades registradas.</p>'}

            <h4 style="margin:0 0 8px;color:#374151;border-bottom:1px solid #e5e7eb;padding-bottom:6px;">🎫 Tickets <span style="font-weight:400;color:#6b7280;font-size:13px;">(${data.tickets?.length||0} total)</span></h4>
            ${tkRows ? `<table style="width:100%;margin-bottom:16px;font-size:13px;">
                <thead><tr style="color:#9ca3af;font-size:11px;text-transform:uppercase;">
                    <th style="text-align:left;padding:0 8px 6px 0;">ID</th><th style="text-align:left;padding:0 8px 6px;">Tipo</th>
                    <th style="text-align:left;padding:0 8px 6px;">Descripción</th><th style="text-align:left;padding:0 0 6px;">Estado</th>
                </tr></thead><tbody>${tkRows}</tbody></table>` : '<p style="color:#9ca3af;font-size:13px;margin-bottom:16px;">Sin tickets.</p>'}

            <h4 style="margin:0 0 8px;color:#374151;border-bottom:1px solid #e5e7eb;padding-bottom:6px;">📸 Evidencias</h4>
            <p style="margin:0 0 16px;"><span style="font-size:22px;font-weight:700;color:#4f46e5;">${data.evidencias_total||0}</span> <span style="color:#6b7280;font-size:13px;">foto${data.evidencias_total!==1?'s':''} registrada${data.evidencias_total!==1?'s':''}</span></p>

            ${data.toma_valores?.length ? `<h4 style="margin:0 0 8px;color:#374151;border-bottom:1px solid #e5e7eb;padding-bottom:6px;">📊 Toma de valores <span style="font-weight:400;color:#6b7280;font-size:13px;">(${data.toma_valores.length} registro${data.toma_valores.length!==1?'s':''})</span></h4>
            <p style="color:#6b7280;font-size:12px;margin:0 0 16px;">Registros disponibles — ver en sección Actividades para detalle completo.</p>` : ''}
        </div>`);
    }

    // -- Init -------------------------------------------------
    recargarActividades();
    recargarUsuarios();
    recargarUnidades();
    </script>
    """
    return HTMLResponse(content=pagina_con_menu("🛠 Panel de Administración", contenido, "admin"))

# ------------------------------------------------------------
# MIS TAREAS (modales con botones grandes y scroll)
# ------------------------------------------------------------
@router.get("/app/mis-tareas", response_class=HTMLResponse)
async def mis_tareas():
    contenido = """
    <script> if (window.role === 'visor') { window.location.href = '/app/dashboard'; } </script>
    <div id="tareasList"></div>
    <script>
        const fetchAuth = window.fetchAuth, username = window.username;

        function mostrarModal(html) {
            const modal = document.createElement('div');
            modal.className = 'modal';
            modal.style.display = 'flex';
            modal.innerHTML = html;
            document.body.appendChild(modal);
            return modal;
        }
        function cerrarModal() {
            const modal = document.querySelector('.modal');
            if (modal) document.body.removeChild(modal);
        }

        async function cargarTareas() {
            const res = await fetchAuth('/api/asignaciones/?tecnico=' + username);
            if (!res.ok) { document.getElementById('tareasList').innerHTML = '<p style="color:red;">Error al cargar tareas.</p>'; return; }
            const tareas = await res.json();
            const activas = Array.isArray(tareas) ? tareas.filter(t => t.estado === 'pendiente' || t.estado === 'en_proceso') : [];
            let html = '';
            if (activas.length === 0) {
                html = '<p>✅ No tienes tareas activas.</p>';
            } else {
                activas.forEach(t => {
                    let btn = '';
                    if (t.estado === 'pendiente') btn = `<button class="btn-primary" onclick="iniciarTarea(${t.id})">▶️ Iniciar Actividad</button>`;
                    else if (t.estado === 'en_proceso') {
                        btn = `<button class="btn-success" onclick="completarTarea(${t.id})">✅ Finalizar</button>`;
                        if (t.actividad_id === 'Evidencia') btn += `<button class="btn-primary" onclick="subirEvidencia(${t.id}, '${t.unidad}')">📸 Subir Fotos</button>`;
                        if (t.actividad_id === 'Toma de Valores') btn += `<button class="btn-primary" onclick="tomarValores(${t.id})">📊 Ingresar Valores</button>`;
                        if (t.actividad_id === 'Toma de Series') btn += `<button class="btn-primary" onclick="tomarSeries(${t.id})">🔢 Ingresar Series</button>`;
                    }
                    html += `<div style="background:white; border-radius:12px; padding:16px; margin-bottom:12px; box-shadow:0 2px 8px rgba(0,0,0,0.05); display:flex; justify-content:space-between; align-items:center;"><div><b>${t.actividad_id}</b> — Unidad: <b>${t.unidad}</b><br><span class="badge" style="background:${t.estado === 'pendiente' ? 'var(--carrier-warn)' : 'var(--carrier-success)'}; color:white;">${t.estado}</span></div><div>${btn}</div></div>`;
                });
            }
            document.getElementById('tareasList').innerHTML = html;
        }

        async function iniciarTarea(id) { const res = await fetchAuth('/api/asignaciones/' + id + '/iniciar', { method: 'PATCH' }); if (res.ok) cargarTareas(); else alert('Error al iniciar la tarea'); }
        async function completarTarea(id) {
            const prev = document.getElementById('modalFinalizar');
            if (prev) prev.remove();

            const modal = document.createElement('div');
            modal.id = 'modalFinalizar';
            modal.style.cssText = 'position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.55);display:flex;justify-content:center;align-items:center;z-index:500;';
            modal.innerHTML = `
                <div style="background:white;border-radius:20px;padding:32px;width:90%;max-width:520px;box-shadow:0 20px 60px rgba(0,43,91,0.25);animation:fadeInM 0.2s ease;">
                    <div style="display:flex;align-items:center;gap:12px;margin-bottom:8px;">
                        <div style="background:#f0fdf4;border-radius:12px;width:48px;height:48px;display:flex;align-items:center;justify-content:center;font-size:1.5rem;">✅</div>
                        <div>
                            <h3 style="margin:0;color:var(--carrier-blue);font-size:1.2rem;font-weight:800;">Finalizar Actividad</h3>
                            <p style="margin:2px 0 0;font-size:0.82rem;color:#6b7280;">Agrega un comentario antes de cerrar esta tarea.</p>
                        </div>
                    </div>
                    <hr style="border:none;border-top:1px solid #e5e7eb;margin:18px 0;">
                    <label style="font-size:0.85rem;font-weight:700;color:var(--carrier-blue);display:block;margin-bottom:6px;">📝 Comentario del técnico</label>
                    <textarea id="comentarioTexto" rows="4" placeholder="Describe brevemente el trabajo realizado, observaciones, etc." style="width:100%;border:1.5px solid #d1d5db;border-radius:12px;padding:12px;font-size:0.95rem;resize:vertical;font-family:inherit;transition:border-color 0.2s;"></textarea>
                    <p id="comentarioError" style="color:var(--carrier-danger);font-size:0.82rem;min-height:18px;margin:4px 0 12px;"></p>
                    <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;">
                        <button onclick="document.getElementById('modalFinalizar').remove()" style="background:#f1f5f9;color:#374151;border:none;border-radius:10px;padding:13px;font-weight:600;font-size:0.95rem;cursor:pointer;">✖ Cancelar</button>
                        <button id="btnConfirmarFinalizar" onclick="confirmarFinalizar(${id})" style="background:linear-gradient(135deg,#16a34a,#15803d);color:white;border:none;border-radius:10px;padding:13px;font-weight:700;font-size:0.95rem;cursor:pointer;">✅ Confirmar y Finalizar</button>
                    </div>
                </div>
                <style>@keyframes fadeInM{from{opacity:0;transform:scale(0.95)}to{opacity:1;transform:scale(1)}}</style>`;
            document.body.appendChild(modal);
            setTimeout(() => document.getElementById('comentarioTexto').focus(), 100);
        }

        async function confirmarFinalizar(id) {
            const comentario = document.getElementById('comentarioTexto').value.trim();
            const errorEl   = document.getElementById('comentarioError');
            if (!comentario) { errorEl.textContent = 'El comentario no puede estar vacío.'; return; }
            const btn = document.getElementById('btnConfirmarFinalizar');
            btn.textContent = 'Guardando...'; btn.disabled = true;
            const res = await fetchAuth('/api/asignaciones/' + id + '/finalizar', { method: 'PATCH', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ comentario }) });
            if (res.ok) {
                document.getElementById('modalFinalizar').remove();
                const toast = document.createElement('div');
                toast.style.cssText = 'position:fixed;bottom:28px;left:50%;transform:translateX(-50%);background:#16a34a;color:white;padding:14px 28px;border-radius:50px;font-weight:700;font-size:0.95rem;box-shadow:0 4px 20px rgba(0,0,0,0.2);z-index:600;';
                toast.textContent = '✅ Actividad finalizada correctamente.';
                document.body.appendChild(toast);
                setTimeout(() => toast.remove(), 3000);
                cargarTareas();
            } else {
                const err = await res.json();
                errorEl.textContent = err.detail || 'No se pudo finalizar. Intenta de nuevo.';
                btn.textContent = '✅ Confirmar y Finalizar'; btn.disabled = false;
            }
        }

        // ---------- EVIDENCIA ----------
        async function subirEvidencia(tareaId, unidad) {
            const cntRes = await fetchAuth(`/api/evidencias/count?unit_number=${unidad}&tecnico=${username}`); const cnt = await cntRes.json();
            const totalPrev = cnt.total || 0; const restantes = 100 - totalPrev;
            if (restantes <= 0) return alert('Límite de 100 fotos alcanzado');
            const modal = mostrarModal(`<div class="modal-content"><h3>📸 Subir Evidencia – ${unidad}</h3><p>Guardadas: <b>${totalPrev}</b> · Disponibles: <b>${restantes}</b></p><input type="file" id="fotosInput" multiple accept="image/*"><div id="previewFotos" style="display:flex; flex-wrap:wrap; gap:8px; margin:12px 0;"></div><div id="compressInfo" style="font-size:12px;color:#666;margin-bottom:8px;"></div><button class="btn-primary" id="btnGuardarFotos">💾 Guardar Fotos</button><button class="btn-danger" onclick="cerrarModal()">Cancelar</button></div>`);

            // Comprime una imagen con Canvas API (max 1200px, calidad 0.75 JPEG)
            async function comprimirImagen(file) {
                return new Promise((resolve) => {
                    const reader = new FileReader();
                    reader.onload = ev => {
                        const img = new Image();
                        img.onload = () => {
                            const MAX = 1200;
                            let { width: w, height: h } = img;
                            if (w > MAX || h > MAX) {
                                if (w > h) { h = Math.round(h * MAX / w); w = MAX; }
                                else       { w = Math.round(w * MAX / h); h = MAX; }
                            }
                            const canvas = document.createElement('canvas');
                            canvas.width = w; canvas.height = h;
                            canvas.getContext('2d').drawImage(img, 0, 0, w, h);
                            canvas.toBlob(blob => {
                                if (blob && blob.size < file.size) {
                                    resolve(new File([blob], file.name.replace(/[.][^.]+$/, '.jpg'), { type: 'image/jpeg' }));
                                } else {
                                    resolve(file); // si ya era pequeño, usar original
                                }
                            }, 'image/jpeg', 0.75);
                        };
                        img.onerror = () => resolve(file); // fallback al original
                        img.src = ev.target.result;
                    };
                    reader.onerror = () => resolve(file);
                    reader.readAsDataURL(file);
                });
            }

            document.getElementById('fotosInput').addEventListener('change', e => {
                const files = Array.from(e.target.files).slice(0, restantes), previewDiv = document.getElementById('previewFotos'); previewDiv.innerHTML = '';
                let totalKB = 0; files.forEach(f => { totalKB += f.size / 1024; const r = new FileReader(); r.onload = ev => { const img = document.createElement('img'); img.src = ev.target.result; img.style.cssText = 'width:70px;height:70px;object-fit:cover;border-radius:8px;'; previewDiv.appendChild(img); }; r.readAsDataURL(f); });
                document.getElementById('compressInfo').textContent = `${files.length} foto(s) · ${(totalKB/1024).toFixed(1)} MB → se comprimirán a ~${Math.round(totalKB * 0.05 / 1024 * 10) / 10 || '<0.5'} MB antes de subir`;
            });

            document.getElementById('btnGuardarFotos').onclick = async () => {
                const input = document.getElementById('fotosInput'); if (!input.files.length) return alert('Selecciona fotos');
                const btn = document.getElementById('btnGuardarFotos'); btn.disabled = true; btn.textContent = '⏳ Comprimiendo...';
                const archivos = Array.from(input.files).slice(0, restantes);
                const comprimidos = await Promise.all(archivos.map(f => comprimirImagen(f)));
                btn.textContent = '📤 Subiendo...';
                const fd = new FormData(); fd.append('unidad', unidad); fd.append('tecnico', username); comprimidos.forEach(f => fd.append('files', f));
                await fetchAuth('/api/evidencias/upload', { method: 'POST', body: fd }); alert('Fotos guardadas'); cerrarModal();
            };
        }

        // ---------- VALORES ----------
        async function tomarValores(tareaId) {
            const camposRes = await fetchAuth('/api/toma-valores/campos'); const campos = await camposRes.json();
            let camposHTML = campos.length ? campos.map((c,i) => `<input type="text" id="campo_${i}" placeholder="${c.campo_nombre}">`).join('') : '<p>No hay campos configurados.</p>';
            const modal = mostrarModal(`<div class="modal-content"><h3>📊 Toma de Valores</h3><div id="camposValores">${camposHTML}</div><button class="btn-primary" id="btnGuardarValores">💾 Guardar Valores</button><button class="btn-danger" onclick="cerrarModal()">Cancelar</button></div>`);
            document.getElementById('btnGuardarValores').onclick = async () => {
                const valores = {}; campos.forEach((c,i) => valores[c.campo_nombre] = document.getElementById('campo_'+i).value);
                await fetchAuth('/api/toma-valores/guardar', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ asignacion_id: tareaId, valores }) }); alert('Valores guardados'); cerrarModal();
            };
        }

        // ---------- SERIES ----------
        async function tomarSeries(tareaId) {
            const camposSeries = [
                { key: 'vin_number', label: 'VIN Number' },{ key: 'reefer_serial', label: 'Serie del Reefer' },{ key: 'reefer_model', label: 'Modelo del Reefer' },
                { key: 'evaporator_serial_mjs11', label: 'Evaporador MJS11' },{ key: 'evaporator_serial_mjd22', label: 'Evaporador MJD22' },
                { key: 'engine_serial', label: 'Motor' },{ key: 'compressor_serial', label: 'Compresor' },{ key: 'generator_serial', label: 'Generador' },
                { key: 'battery_charger_serial', label: 'Cargador de Batería' }
            ];
            let inputs = camposSeries.map((c,i) => `<input type="text" id="serie_${i}" placeholder="${c.label}"><input type="hidden" id="serie_key_${i}" value="${c.key}">`).join('');
            const modal = mostrarModal(`<div class="modal-content"><h3>🔢 Toma de Series</h3><div id="camposSeries">${inputs}</div><button class="btn-primary" id="btnGuardarSeries">💾 Guardar Series</button><button class="btn-danger" onclick="cerrarModal()">Cancelar</button></div>`);
            document.getElementById('btnGuardarSeries').onclick = async () => {
                const tareasRes = await fetchAuth('/api/asignaciones/?tecnico=' + username + '&estado=en_proceso'); const tareas = await tareasRes.json();
                const tarea = Array.isArray(tareas) ? tareas.find(t => t.id == tareaId) : null; if (!tarea) return alert('Tarea no encontrada');
                const keys = [...document.querySelectorAll('[id^="serie_key_"]')].map(el => el.value); const values = { unit_number: tarea.unidad };
                keys.forEach((key,i) => values[key] = document.getElementById('serie_'+i).value);
                const resSeries = await fetchAuth('/api/unidades/series/update', { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(values) }); if (resSeries.ok) { cerrarModal(); cargarTareas(); const t = document.createElement('div'); t.style.cssText = 'position:fixed;bottom:28px;left:50%;transform:translateX(-50%);background:#16a34a;color:white;padding:14px 28px;border-radius:50px;font-weight:700;z-index:600;'; t.textContent = '✅ Series guardadas correctamente.'; document.body.appendChild(t); setTimeout(() => t.remove(), 3000); } else { alert('Error al guardar las series.'); }
            };
        }

        cargarTareas();
    </script>
    """
    return HTMLResponse(content=pagina_con_menu("🎯 Mis Tareas", contenido, "mis-tareas"))

# ------------------------------------------------------------
# NUEVA SOLICITUD
# ------------------------------------------------------------
@router.get("/app/solicitud", response_class=HTMLResponse)
async def solicitud():
    contenido = """
    <form id="solicitudForm">
        <select id="unidad" required><option value="">Unidad</option></select>
        <select id="actividad" required><option value="">Actividad</option></select>
        <button type="submit" class="btn-primary">📤 Enviar Solicitud</button>
        <div id="msgSolicitud" style="font-size:0.85rem;"></div>
    </form>
    <div class="section-title">📋 Mis Solicitudes Recientes</div>
    <div id="historialSolicitudes" style="margin-top:16px;"></div>
    <script>
        const fetchAuth = window.fetchAuth, username = window.username;
        document.getElementById('unidad').addEventListener('change', () => document.getElementById('msgSolicitud').innerHTML = '');
        document.getElementById('actividad').addEventListener('change', () => document.getElementById('msgSolicitud').innerHTML = '');
        async function cargarOpciones() {
            const unidadesRes = await fetchAuth('/api/unidades/'); const unidades = await unidadesRes.json();
            document.getElementById('unidad').innerHTML = '<option value="">Unidad</option>' + (Array.isArray(unidades) ? unidades.map(u => `<option value="${u.unit_number}">${u.unit_number} (${u.id_lote})</option>`).join('') : '');
            document.getElementById('actividad').innerHTML = '<option value="">Actividad</option>' + ['Cableado','Programación','Soldadura','Check de fugas','Vacío','Cerrado','Pre-viaje','Horas Corridas','Standby','GPS','Corriendo','Inspección','Accesorios','Toma de Valores','Evidencia','Toma de Series'].map(a => `<option value="${a}">${a}</option>`).join('');
            const histRes = await fetchAuth('/api/asignaciones/?tecnico=' + username + '&limit=20'); const historial = await histRes.json();
            let hHtml = '';
            if (Array.isArray(historial)) historial.forEach(h => { const color = h.estado === 'solicitado' ? '#fef9c3' : h.estado === 'pendiente' ? '#fff7ed' : h.estado === 'en_proceso' ? '#eff6ff' : '#f0fdf4'; const borderColor = h.estado === 'solicitado' ? '#854d0e' : h.estado === 'pendiente' ? '#9a3412' : h.estado === 'en_proceso' ? '#1e40af' : '#166534'; hHtml += `<div style="background:${color};border-left:4px solid ${borderColor};padding:10px 16px;margin-bottom:6px;border-radius:8px;"><b>${h.actividad_id}</b> — Unidad: ${h.unidad} · ${h.estado}</div>`; });
            document.getElementById('historialSolicitudes').innerHTML = hHtml || '<p>Sin solicitudes recientes.</p>';
        }
        document.getElementById('solicitudForm').addEventListener('submit', async (e) => {
            e.preventDefault(); const unidad = document.getElementById('unidad').value, actividad = document.getElementById('actividad').value;
            if (!unidad || !actividad) return alert('Selecciona unidad y actividad');
            const msgDiv = document.getElementById('msgSolicitud'); msgDiv.innerHTML = '<p style="color:var(--carrier-warn);">Verificando...</p>';
            const res = await fetchAuth('/api/asignaciones/?estado=solicitado,pendiente,en_proceso');
            if (!res.ok) { msgDiv.innerHTML = '<p style="color:var(--carrier-danger);">Error al verificar.</p>'; return; }
            const todas = await res.json(); const activa = todas.find(a => a.unidad === unidad && a.actividad_id === actividad);
            if (activa) { msgDiv.innerHTML = `<p style="color:var(--carrier-danger);">Ya existe una tarea activa para esta combinación (técnico: ${activa.tecnico}). Solo un administrador puede autorizarla.</p>`; return; }
            const crearRes = await fetchAuth('/api/asignaciones/solicitar', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ unidad, actividad_id: actividad, tecnico: username }) });
            if (!crearRes.ok) { const err = await crearRes.json(); msgDiv.innerHTML = `<p style="color:var(--carrier-danger);">${err.detail || 'Error al enviar solicitud'}</p>`; return; }
            msgDiv.innerHTML = '<p style="color:var(--carrier-success);">Solicitud enviada correctamente.</p>'; cargarOpciones();
        });
        cargarOpciones();
    </script>
    """
    return HTMLResponse(content=pagina_con_menu("🔔 Nueva Solicitud", contenido, "solicitud"))

# ------------------------------------------------------------
# MIS TICKETS
# ------------------------------------------------------------
@router.get("/app/mis-tickets", response_class=HTMLResponse)
async def mis_tickets():
    contenido = """
    <div id="ticketsList"></div>
    <script>
        const fetchAuth = window.fetchAuth;

        async function cargarTickets() {
            const res = await fetchAuth('/api/tickets/');
            const tickets = await res.json();
            let html = '';
            if (tickets.length) {
                tickets.forEach(t => {
                    const estado = t.atendido
                        ? (t.reporte_enviado ? '🟢 Completado' : '🟡 Atendido (sin reporte)')
                        : '🔴 No atendido';
                    const color = t.atendido
                        ? (t.reporte_enviado ? 'var(--carrier-success)' : 'var(--carrier-warn)')
                        : 'var(--carrier-danger)';

                    let acciones = '';
                    if (!t.atendido) {
                        acciones = `<button class="btn-warning" onclick="atenderTicket(${t.id})" style="margin-top:10px; width:auto; padding:10px 18px;">✅ Marcar como atendido</button>`;
                    } else if (!t.reporte_enviado) {
                        acciones = `<button class="btn-primary" onclick="enviarReporte(${t.id})" style="margin-top:10px; width:auto; padding:10px 18px;">📤 Enviar reporte final</button>`;
                    }

                    html += `
                        <div style="border-left:6px solid ${color}; background:white; padding:16px; margin-bottom:12px; border-radius:0 12px 12px 0; box-shadow:0 2px 8px rgba(0,0,0,0.05);">
                            <div style="display:flex; justify-content:space-between; align-items:flex-start; flex-wrap:wrap; gap:8px;">
                                <div>
                                    <span style="font-size:1.5rem; font-weight:800; color:var(--carrier-blue);">#${t.ticket_num}</span>
                                    <span class="badge" style="background:${color}; color:white; margin-left:8px;">${estado}</span>
                                    <p style="margin:8px 0 4px;"><b>Unidad:</b> ${t.unit_number} | <b>VIN:</b> ${t.vin_number || 'N/D'}</p>
                                    <p style="margin:4px 0;"><b>Descripción:</b> ${t.descripcion}</p>
                                    <small style="color:#6b7280;">Creado: ${t.fecha_creacion}</small>
                                </div>
                                <div style="display:flex; align-items:center;">${acciones}</div>
                            </div>
                        </div>`;
                });
            }
            if (!html) html = '<p>🎫 No tienes tickets.</p>';
            document.getElementById('ticketsList').innerHTML = html;
        }

        async function atenderTicket(id) {
            if (!confirm('¿Marcar este ticket como atendido?')) return;
            const res = await fetchAuth('/api/tickets/' + id + '/atender', { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ atendido: true }) });
            if (res.ok) { cargarTickets(); }
            else { alert('Error al actualizar el ticket'); }
        }

        async function enviarReporte(ticketId) {
            const prev = document.getElementById('modalReporte');
            if (prev) prev.remove();

            const modal = document.createElement('div');
            modal.id = 'modalReporte';
            modal.style.cssText = 'position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.55);display:flex;justify-content:center;align-items:center;z-index:500;';
            modal.innerHTML = `
                <div style="background:white;border-radius:20px;padding:32px;width:90%;max-width:520px;box-shadow:0 20px 60px rgba(0,43,91,0.25);animation:fadeIn 0.2s ease;">
                    <div style="display:flex;align-items:center;gap:12px;margin-bottom:8px;">
                        <div style="background:var(--carrier-light);border-radius:12px;width:48px;height:48px;display:flex;align-items:center;justify-content:center;font-size:1.5rem;">📋</div>
                        <div>
                            <h3 style="margin:0;color:var(--carrier-blue);font-size:1.2rem;font-weight:800;">Reporte Final del Ticket</h3>
                            <p style="margin:2px 0 0;font-size:0.82rem;color:#6b7280;">Este reporte quedará registrado y cerrará el ticket en verde.</p>
                        </div>
                    </div>
                    <hr style="border:none;border-top:1px solid #e5e7eb;margin:18px 0;">
                    <label style="font-size:0.85rem;font-weight:700;color:var(--carrier-blue);display:block;margin-bottom:6px;">📝 Descripción del trabajo realizado</label>
                    <textarea id="reporteTexto" rows="5" placeholder="Describe detalladamente las acciones realizadas, piezas cambiadas, diagnóstico, etc." style="width:100%;border:1.5px solid #d1d5db;border-radius:12px;padding:12px;font-size:0.95rem;resize:vertical;font-family:inherit;transition:border-color 0.2s;"></textarea>
                    <p id="reporteError" style="color:var(--carrier-danger);font-size:0.82rem;min-height:18px;margin:4px 0 12px;"></p>
                    <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-top:4px;">
                        <button onclick="document.getElementById('modalReporte').remove()" style="background:#f1f5f9;color:#374151;border:none;border-radius:10px;padding:13px;font-weight:600;font-size:0.95rem;cursor:pointer;">✖ Cancelar</button>
                        <button id="btnEnviarReporte" onclick="confirmarReporte(${ticketId})" style="background:linear-gradient(135deg,var(--carrier-blue),var(--carrier-accent));color:white;border:none;border-radius:10px;padding:13px;font-weight:700;font-size:0.95rem;cursor:pointer;">📤 Enviar y Cerrar Ticket</button>
                    </div>
                </div>
                <style>@keyframes fadeIn{from{opacity:0;transform:scale(0.95)}to{opacity:1;transform:scale(1)}}</style>`;
            document.body.appendChild(modal);
            setTimeout(() => document.getElementById('reporteTexto').focus(), 100);
        }

        async function confirmarReporte(id) {
            const reporte = document.getElementById('reporteTexto').value.trim();
            const errorEl = document.getElementById('reporteError');
            if (!reporte) { errorEl.textContent = 'El reporte no puede estar vacío.'; return; }
            const btn = document.getElementById('btnEnviarReporte');
            btn.textContent = 'Enviando...'; btn.disabled = true;
            const res = await fetchAuth('/api/tickets/' + id + '/report', { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ reporte }) });
            if (res.ok) {
                document.getElementById('modalReporte').remove();
                const toast = document.createElement('div');
                toast.style.cssText = 'position:fixed;bottom:28px;left:50%;transform:translateX(-50%);background:#16a34a;color:white;padding:14px 28px;border-radius:50px;font-weight:700;font-size:0.95rem;box-shadow:0 4px 20px rgba(0,0,0,0.2);z-index:600;';
                toast.textContent = '✅ Reporte enviado. Ticket completado.';
                document.body.appendChild(toast);
                setTimeout(() => toast.remove(), 3000);
                cargarTickets();
            } else {
                errorEl.textContent = 'Error al enviar el reporte. Intenta de nuevo.';
                btn.textContent = '📤 Enviar y Cerrar Ticket'; btn.disabled = false;
            }
        }

        cargarTickets();
    </script>
    """
    return HTMLResponse(content=pagina_con_menu("🎫 Mis Tickets", contenido, "mis-tickets"))

# ------------------------------------------------------------
# PANEL DE ASIGNACIÓN POR CLUSTER (CORREGIDO, SIN DEPENDENCIAS)
# ------------------------------------------------------------
@router.get("/app/cluster", response_class=HTMLResponse)
async def panel_cluster():
    contenido = """
    <div id="resumenCluster" style="display:none; background:var(--color-background-secondary); border-radius:var(--border-radius-lg); padding:16px; margin-bottom:20px;"></div>
    <div style="display:grid; grid-template-columns:1fr 1fr 1fr; gap:16px; align-items:start;">
        <div style="background:var(--color-background-primary); border:0.5px solid var(--color-border-tertiary); border-radius:var(--border-radius-lg); padding:16px;">
            <div style="font-weight:500; margin-bottom:12px; color:var(--color-text-primary);">🔧 Técnicos</div>
            <div style="margin-bottom:8px; display:flex; gap:6px;">
                <button onclick="seleccionarTodos('tecnicos')" style="font-size:11px;padding:4px 10px;">Todos</button>
                <button onclick="limpiarTodos('tecnicos')" style="font-size:11px;padding:4px 10px;">Ninguno</button>
            </div>
            <div id="listaTecnicos" style="max-height:320px;overflow-y:auto;display:flex;flex-direction:column;gap:6px;"></div>
        </div>
        <div style="background:var(--color-background-primary); border:0.5px solid var(--color-border-tertiary); border-radius:var(--border-radius-lg); padding:16px;">
            <div style="font-weight:500; margin-bottom:12px; color:var(--color-text-primary);">🎯 Actividades</div>
            <div style="margin-bottom:8px; display:flex; gap:6px;">
                <button onclick="seleccionarTodos('actividades')" style="font-size:11px;padding:4px 10px;">Todas</button>
                <button onclick="limpiarTodos('actividades')" style="font-size:11px;padding:4px 10px;">Ninguna</button>
            </div>
            <div id="listaActividades" style="max-height:320px;overflow-y:auto;display:flex;flex-direction:column;gap:6px;"></div>
        </div>
        <div style="background:var(--color-background-primary); border:0.5px solid var(--color-border-tertiary); border-radius:var(--border-radius-lg); padding:16px;">
            <div style="font-weight:500; margin-bottom:12px; color:var(--color-text-primary);">🚛 Unidades</div>
            <div style="margin-bottom:8px; display:flex; gap:6px;">
                <button onclick="seleccionarTodos('unidades')" style="font-size:11px;padding:4px 10px;">Todas</button>
                <button onclick="limpiarTodos('unidades')" style="font-size:11px;padding:4px 10px;">Ninguna</button>
            </div>
            <div id="filtroLote" style="margin-bottom:8px;"></div>
            <div id="listaUnidades" style="max-height:280px;overflow-y:auto;display:flex;flex-direction:column;gap:6px;"></div>
        </div>
    </div>
    <div style="margin-top:20px; background:var(--color-background-primary); border:0.5px solid var(--color-border-tertiary); border-radius:var(--border-radius-lg); padding:20px;">
        <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:12px;">
            <div id="contadorResumen" style="font-size:13px; color:var(--color-text-secondary);">Selecciona técnicos, actividades y unidades</div>
            <button id="btnAsignar" onclick="ejecutarAsignacion()" style="padding:12px 32px; font-size:0.95rem; font-weight:600; background:linear-gradient(135deg,var(--carrier-blue),var(--carrier-accent)); color:white; border:none; border-radius:10px; cursor:pointer;">⚡ Asignar Cluster</button>
        </div>
    </div>
    <script>
        const fetchAuth = window.fetchAuth;
        let todosTecnicos = [], todasActividades = [], todasUnidades = [];
        let lotes = [];

        function checkItem(tipo, valor) {
            return `<label style="display:flex;align-items:center;gap:8px;padding:6px 10px;border-radius:8px;cursor:pointer;border:0.5px solid var(--color-border-tertiary);font-size:13px;color:var(--color-text-primary);transition:background 0.15s;" onmouseover="this.style.background='var(--color-background-secondary)'" onmouseout="this.style.background='transparent'">
                <input type="checkbox" data-tipo="${tipo}" data-valor="${encodeURIComponent(valor)}" onchange="actualizarContador()" style="width:15px;height:15px;cursor:pointer;">
                ${valor}
            </label>`;
        }

        function seleccionarTodos(tipo) {
            document.querySelectorAll(`input[data-tipo="${tipo}"]`).forEach(c => c.checked = true);
            actualizarContador();
        }
        function limpiarTodos(tipo) {
            document.querySelectorAll(`input[data-tipo="${tipo}"]`).forEach(c => c.checked = false);
            actualizarContador();
        }

        function getSeleccionados(tipo) {
            return [...document.querySelectorAll(`input[data-tipo="${tipo}"]:checked`)].map(c => decodeURIComponent(c.dataset.valor));
        }

        function actualizarContador() {
            const t = getSeleccionados('tecnicos').length;
            const a = getSeleccionados('actividades').length;
            const u = getSeleccionados('unidades').length;
            const total = t * a * u;
            const el = document.getElementById('contadorResumen');
            if (total === 0) {
                el.innerHTML = 'Selecciona técnicos, actividades y unidades';
                el.style.color = 'var(--color-text-secondary)';
            } else {
                el.innerHTML = `<b>${t}</b> técnico(s) × <b>${a}</b> actividad(es) × <b>${u}</b> unidad(es) = <b style="color:var(--carrier-blue);">${total} asignaciones</b>`;
                el.style.color = 'var(--color-text-primary)';
            }
        }

        function filtrarPorLote(lote) {
            const items = document.querySelectorAll('[data-lote]');
            items.forEach(i => {
                i.style.display = (!lote || i.dataset.lote === lote) ? 'flex' : 'none';
            });
        }

        async function cargarDatos() {
            const [resTec, resAct, resUni] = await Promise.all([
                fetchAuth('/api/cluster/tecnicos'),
                fetchAuth('/api/cluster/actividades'),
                fetchAuth('/api/cluster/unidades')
            ]);
            todosTecnicos  = await resTec.json();
            todasActividades = await resAct.json();
            todasUnidades  = await resUni.json();

            document.getElementById('listaTecnicos').innerHTML = todosTecnicos.map(t => checkItem('tecnicos', t.username)).join('');
            document.getElementById('listaActividades').innerHTML = todasActividades.map(a => checkItem('actividades', a.nombre)).join('');

            lotes = [...new Set(todasUnidades.map(u => u.id_lote).filter(Boolean))].sort();
            let filtroHtml = '<select onchange="filtrarPorLote(this.value)" style="width:100%;margin-bottom:6px;font-size:12px;padding:5px;"><option value="">— Todos los lotes —</option>';
            lotes.forEach(l => filtroHtml += `<option value="${l}">${l}</option>`);
            filtroHtml += '</select>';
            document.getElementById('filtroLote').innerHTML = filtroHtml;

            document.getElementById('listaUnidades').innerHTML = todasUnidades.map(u =>
                `<label data-lote="${u.id_lote || ''}" style="display:flex;align-items:center;gap:8px;padding:6px 10px;border-radius:8px;cursor:pointer;border:0.5px solid var(--color-border-tertiary);font-size:13px;color:var(--color-text-primary);transition:background 0.15s;" onmouseover="this.style.background='var(--color-background-secondary)'" onmouseout="this.style.background='transparent'">
                    <input type="checkbox" data-tipo="unidades" data-valor="${encodeURIComponent(u.unit_number)}" onchange="actualizarContador()" style="width:15px;height:15px;cursor:pointer;">
                    <span>${u.unit_number}</span><span style="font-size:11px;color:var(--color-text-secondary);margin-left:auto;">${u.id_lote || ''}</span>
                </label>`
            ).join('');
        }

        async function ejecutarAsignacion() {
            const tecnicos   = getSeleccionados('tecnicos');
            const actividades = getSeleccionados('actividades');
            const unidades   = getSeleccionados('unidades');
            if (!tecnicos.length || !actividades.length || !unidades.length) {
                return alert('Selecciona al menos un técnico, una actividad y una unidad.');
            }
            const total = tecnicos.length * actividades.length * unidades.length;
            if (!confirm(`¿Crear ${total} asignaciones? Esta acción no se puede deshacer.`)) return;

            const btn = document.getElementById('btnAsignar');
            btn.textContent = 'Asignando...'; btn.disabled = true;

            const res = await fetchAuth('/api/cluster/asignar', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ tecnicos, actividades, unidades })
            });
            const data = await res.json();

            btn.textContent = '⚡ Asignar Cluster'; btn.disabled = false;

            const resumen = document.getElementById('resumenCluster');
            resumen.style.display = 'block';
            resumen.innerHTML = res.ok
                ? `<div style="color:var(--color-text-success);font-weight:500;">✅ ${data.mensaje}</div>`
                : `<div style="color:var(--color-text-danger);font-weight:500;">❌ Error: ${data.detail || 'No se pudo completar'}</div>`;

            if (res.ok) {
                const toast = document.createElement('div');
                toast.style.cssText = 'position:fixed;bottom:28px;left:50%;transform:translateX(-50%);background:#16a34a;color:white;padding:14px 28px;border-radius:50px;font-weight:700;font-size:0.95rem;box-shadow:0 4px 20px rgba(0,0,0,0.2);z-index:600;';
                toast.textContent = `✅ ${data.creadas} asignaciones creadas correctamente.`;
                document.body.appendChild(toast);
                setTimeout(() => toast.remove(), 4000);
                limpiarTodos('tecnicos'); limpiarTodos('actividades'); limpiarTodos('unidades');
                actualizarContador();
            }
        }

        cargarDatos();
    </script>
    """
    return HTMLResponse(content=pagina_con_menu("⚡ Asignación por Cluster", contenido, "cluster"))


# ------------------------------------------------------------
# ASISTENCIA – PANEL ADMIN: genera QR con geocoordenadas fijas
# ------------------------------------------------------------
@router.get("/app/asistencia", response_class=HTMLResponse)
async def asistencia_admin():
    contenido = """
    <script>if (window.role !== 'admin' && window.role !== 'visor') { window.location.href = '/app/mis-tareas'; }</script>
    <script src="https://cdn.jsdelivr.net/npm/qrcodejs@1.0.0/qrcode.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/html2canvas@1.4.1/dist/html2canvas.min.js"></script>
    <style>
        .tab-btn { background:white; border:1.5px solid #e5e7eb; border-radius:10px; padding:10px 24px; font-weight:600; font-size:.9rem; color:#6b7280; cursor:pointer; transition:.2s; }
        .tab-btn.active { background:#002B5B; color:white; border-color:#002B5B; }
        .tab-panel { display:none; }
        .tab-panel.active { display:block; }
        .horario-tbl { width:100%; border-collapse:collapse; background:white; border-radius:12px; overflow:hidden; box-shadow:0 2px 12px rgba(0,43,91,0.08); font-size:.85rem; }
        .horario-tbl th { background:#002B5B; color:white; padding:10px 12px; text-align:center; white-space:nowrap; }
        .horario-tbl th:first-child { text-align:left; }
        .horario-tbl td { padding:8px 12px; border-bottom:1px solid #f0f2f5; text-align:center; }
        .horario-tbl td:first-child { font-weight:600; text-align:left; }
        .horario-tbl input[type=time] { border:1px solid #d1d5db; border-radius:6px; padding:4px 8px; font-size:.82rem; width:90px; margin-bottom:0; }
        .est-completo  { background:#dcfce7; color:#16a34a; padding:3px 10px; border-radius:12px; font-size:.78rem; font-weight:600; }
        .est-retardo   { background:#fef3c7; color:#d97706; padding:3px 10px; border-radius:12px; font-size:.78rem; font-weight:600; }
        .est-ausente   { background:#fee2e2; color:#dc2626; padding:3px 10px; border-radius:12px; font-size:.78rem; font-weight:600; }
        .est-libre     { background:#f3f4f6; color:#9ca3af; padding:3px 10px; border-radius:12px; font-size:.78rem; font-weight:600; }
        .est-sin_salida { background:#fef3c7; color:#92400e; padding:3px 10px; border-radius:12px; font-size:.78rem; font-weight:600; }
    </style>

    <!-- Tabs -->
    <div style="display:flex; gap:10px; margin-bottom:28px; flex-wrap:wrap;">
        <button class="tab-btn active" onclick="switchTab('tab-qr',this)">📲 QR de Asistencia</button>
        <button class="tab-btn" onclick="switchTab('tab-horarios',this)">📅 Horario Semanal</button>
        <button class="tab-btn" onclick="switchTab('tab-registros',this)">📋 Registros del Día</button>
    </div>

    <!-- TAB 1: QR -->
    <div id="tab-qr" class="tab-panel active">
        <div class="evidencia-info" style="margin-bottom:20px;">
            <b>📍 Geoposición del punto de asistencia</b><br>
            <span style="font-size:.85rem;">Define las coordenadas del lugar de trabajo. El técnico deberá estar dentro del radio al escanear.</span>
        </div>
        <div style="display:grid; grid-template-columns:1fr 1fr 1fr; gap:16px; margin-bottom:20px;">
            <div><label style="font-size:.82rem; font-weight:600; color:#374151;">Latitud</label><input type="number" id="latFija" step="0.000001" value="32.5027"></div>
            <div><label style="font-size:.82rem; font-weight:600; color:#374151;">Longitud</label><input type="number" id="lonFija" step="0.000001" value="-117.0037"></div>
            <div><label style="font-size:.82rem; font-weight:600; color:#374151;">Radio (metros)</label><input type="number" id="radioMetros" value="200" min="10" max="5000"></div>
        </div>
        <div style="display:flex; gap:12px; margin-bottom:28px; flex-wrap:wrap;">
            <button class="btn-primary" style="width:auto; padding:12px 24px;" onclick="generarQR()">🔄 Generar QR</button>
            <button class="btn-warning" style="width:auto; padding:12px 24px;" onclick="usarUbicacionActual()">📡 Usar mi ubicación</button>
        </div>
        <div id="qrSection" style="display:none; margin-bottom:32px;">
            <div class="section-title">📲 QR Generado</div>
            <div style="display:flex; gap:32px; align-items:flex-start; flex-wrap:wrap;">
                <div style="background:white; padding:24px; border-radius:16px; box-shadow:0 4px 20px rgba(0,43,91,0.1); text-align:center;">
                    <div id="qrCanvas"></div>
                    <p style="font-size:.78rem; color:#6b7280; margin-top:12px;">Expira en <b id="qrTimer">05:00</b></p>
                    <button class="btn-primary" style="width:auto; padding:10px 20px; font-size:.85rem; margin-top:8px;" onclick="generarQR()">🔁 Regenerar</button>
                </div>
                <div style="flex:1; min-width:220px;">
                    <div class="inv-info-bar" style="margin-bottom:12px;">📍 Punto configurado</div>
                    <p style="font-size:.9rem;"><b>Lat:</b> <span id="qrLatLabel"></span></p>
                    <p style="font-size:.9rem;"><b>Lon:</b> <span id="qrLonLabel"></span></p>
                    <p style="font-size:.9rem;"><b>Radio:</b> <span id="qrRadioLabel"></span> m</p>
                    <div id="mapaLink" style="margin-top:8px;"></div>
                </div>
            </div>
        </div>
    </div>

    <!-- TAB 2: HORARIO SEMANAL -->
    <div id="tab-horarios" class="tab-panel">
        <div style="display:flex; gap:12px; align-items:center; margin-bottom:20px; flex-wrap:wrap;">
            <label style="font-weight:600; font-size:.9rem;">Semana del lunes:</label>
            <input type="date" id="semanaInput" style="width:auto; margin-bottom:0;" onchange="cargarHorarios()">
            <button class="btn-primary" style="width:auto; padding:10px 22px;" onclick="guardarHorarios()">💾 Guardar Horarios</button>
            <button class="btn-success" style="width:auto; padding:10px 22px;" onclick="abrirModalImportacion()">📂 Importar Excel</button>
        </div>
        <div id="tablaHorarios" style="overflow-x:auto;"></div>

        <div style="display:flex; align-items:center; justify-content:space-between; margin-top:32px; flex-wrap:wrap; gap:10px;">
            <div class="section-title" style="margin:0;">📊 Resumen Semanal de Asistencia</div>
            <button class="btn-primary" style="width:auto; padding:8px 18px; font-size:.85rem;" onclick="exportarResumenSemanalImagen()">🖼️ Exportar Imagen</button>
        </div>
        <div id="resumenSemanalWrap" style="overflow-x:auto; background:white; padding:4px;">
            <div id="resumenSemanal" style="overflow-x:auto;"></div>
        </div>
    </div>

    <!-- MODAL: Importar Horarios desde Excel -->
    <div id="modalImportacion" style="display:none; position:fixed; inset:0; background:rgba(0,0,0,0.55); z-index:9999; overflow-y:auto;">
      <div style="background:white; margin:30px auto; max-width:960px; border-radius:16px; padding:32px; box-shadow:0 8px 40px rgba(0,43,91,0.18);">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:20px;">
          <h2 style="margin:0; font-size:1.2rem; color:#002B5B;">📂 Importar Horarios desde Excel</h2>
          <button onclick="cerrarModalImportacion()" style="background:none; border:none; font-size:1.5rem; cursor:pointer; color:#6b7280;">✕</button>
        </div>

        <!-- Paso 1: Seleccionar archivo -->
        <div id="imp-paso1">
          <p style="color:#374151; margin-bottom:14px;">Selecciona un archivo <b>.xlsx</b> con el formato de horarios semanal. La columna <code>Técnico (username)</code> puede estar vacía — el sistema intentará identificar a cada técnico por su nombre completo.</p>
          <div style="display:flex; gap:12px; align-items:center; flex-wrap:wrap;">
            <input type="file" id="impFile" accept=".xlsx" style="width:auto; margin-bottom:0;">
            <button class="btn-primary" style="width:auto; padding:10px 20px;" onclick="procesarExcel()">🔍 Procesar</button>
          </div>
          <div id="impError" style="color:#dc2626; margin-top:12px; display:none;"></div>
        </div>

        <!-- Paso 2: Preview -->
        <div id="imp-paso2" style="display:none;">
          <div id="impAvisoSinMatch" style="display:none; background:#fef3c7; border:1px solid #fde68a; border-radius:8px; padding:12px 16px; margin-bottom:16px; color:#92400e;">
            ⚠️ Los siguientes nombres no se identificaron automáticamente. Asigna el username manualmente en la tabla:
            <span id="impListaSinMatch"></span>
          </div>
          <p style="color:#374151; margin-bottom:12px; font-size:.9rem;">Revisa el mapeo <b>Nombre → Username</b>. Puedes corregir el username si es incorrecto. Las filas sin username <b>no se importarán</b>.</p>
          <div style="overflow-x:auto;">
            <table style="width:100%; border-collapse:collapse; font-size:.82rem;">
              <thead>
                <tr style="background:#002B5B; color:white;">
                  <th style="padding:8px 12px; text-align:left;">Nombre en Excel</th>
                  <th style="padding:8px 12px; text-align:left;">Username</th>
                  <th style="padding:8px 12px; text-align:center;">Confianza</th>
                  <th style="padding:8px 12px; text-align:center;">Lu Ent</th>
                  <th style="padding:8px 12px; text-align:center;">Lu Sal</th>
                  <th style="padding:8px 12px; text-align:center;">Ma Ent</th>
                  <th style="padding:8px 12px; text-align:center;">Ma Sal</th>
                  <th style="padding:8px 12px; text-align:center;">Mi Ent</th>
                  <th style="padding:8px 12px; text-align:center;">Mi Sal</th>
                  <th style="padding:8px 12px; text-align:center;">Ju Ent</th>
                  <th style="padding:8px 12px; text-align:center;">Ju Sal</th>
                  <th style="padding:8px 12px; text-align:center;">Vi Ent</th>
                  <th style="padding:8px 12px; text-align:center;">Vi Sal</th>
                  <th style="padding:8px 12px; text-align:center;">Sá Ent</th>
                  <th style="padding:8px 12px; text-align:center;">Sá Sal</th>
                </tr>
              </thead>
              <tbody id="impTableBody"></tbody>
            </table>
          </div>
          <div style="display:flex; gap:12px; margin-top:20px; justify-content:flex-end; flex-wrap:wrap;">
            <button onclick="cerrarModalImportacion()" style="padding:10px 22px; background:#f3f4f6; border:1px solid #d1d5db; border-radius:8px; cursor:pointer; font-weight:600;">Cancelar</button>
            <button class="btn-primary" style="width:auto; padding:10px 24px;" onclick="confirmarImportacion()">✅ Confirmar e Importar</button>
          </div>
          <div id="impResultado" style="display:none; margin-top:16px; background:#dcfce7; border:1px solid #bbf7d0; border-radius:8px; padding:12px 16px; color:#166534; font-weight:600;"></div>
        </div>
      </div>
    </div>

    <!-- TAB 3: REGISTROS DEL DÍA -->
    <div id="tab-registros" class="tab-panel">
        <div style="display:flex; gap:12px; margin-bottom:12px; flex-wrap:wrap; align-items:center;">
            <input type="date" id="fechaFiltro" style="width:auto; margin-bottom:0;" onchange="cargarRegistros()">
            <button class="btn-primary" style="width:auto; padding:10px 20px; font-size:.85rem;" onclick="cargarRegistros()">🔄 Actualizar</button>
            <button class="btn-success" style="width:auto; padding:10px 20px; font-size:.85rem;" onclick="exportarCSV()">📥 Exportar CSV</button>
        </div>
        <div id="tablaAsistencia" style="overflow-x:auto;"></div>
    </div>

    <script>
        // Tabs --------------------------------------------------------------
        function switchTab(id, btn) {
            document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
            document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            document.getElementById(id).classList.add('active');
            btn.classList.add('active');
        }

        // -- Init fechas -------------------------------------------------------
        // FIX: toISOString() devuelve fecha UTC; en Tijuana (UTC-7) puede ser
        // el día siguiente desde las 17:00. Usar Intl.DateTimeFormat en-CA
        // para obtener siempre la fecha local en Tijuana (formato YYYY-MM-DD).
        function fechaTijuana(d) {
            return new Intl.DateTimeFormat('en-CA', { timeZone: 'America/Tijuana' }).format(d || new Date());
        }
        const hoy = new Date();
        document.getElementById('fechaFiltro').value = fechaTijuana(hoy);
        // Calcular lunes de la semana usando la fecha local Tijuana (no UTC)
        const hoyTJ = new Date(fechaTijuana(hoy) + 'T12:00:00');
        const lunes = new Date(hoyTJ); lunes.setDate(hoyTJ.getDate() - (hoyTJ.getDay() === 0 ? 6 : hoyTJ.getDay()-1));
        document.getElementById('semanaInput').value = fechaTijuana(lunes);

        cargarRegistros();
        cargarHorarios();

        // -- QR ----------------------------------------------------------------
        let timerInterval = null; let segundosRestantes = 0;

        function usarUbicacionActual() {
            if (!navigator.geolocation) return alert('Tu navegador no soporta geolocalización.');
            navigator.geolocation.getCurrentPosition(pos => {
                document.getElementById('latFija').value = pos.coords.latitude.toFixed(6);
                document.getElementById('lonFija').value = pos.coords.longitude.toFixed(6);
                alert('✅ Coordenadas actualizadas.');
            }, () => alert('No se pudo obtener la ubicación.'));
        }

        function generarQR() {
            const lat = parseFloat(document.getElementById('latFija').value);
            const lon = parseFloat(document.getElementById('lonFija').value);
            const radio = parseInt(document.getElementById('radioMetros').value);
            if (isNaN(lat)||isNaN(lon)||isNaN(radio)) return alert('Completa todos los campos.');
            const token = btoa(`asistencia:${lat}:${lon}:${radio}:${Date.now()}`);
            const url = `${window.location.origin}/app/checkin?token=${encodeURIComponent(token)}&lat=${lat}&lon=${lon}&radio=${radio}`;
            document.getElementById('qrCanvas').innerHTML = '';
            new QRCode(document.getElementById('qrCanvas'), {text:url, width:220, height:220, colorDark:'#002B5B', colorLight:'#ffffff', correctLevel:QRCode.CorrectLevel.H});
            document.getElementById('qrLatLabel').textContent = lat;
            document.getElementById('qrLonLabel').textContent = lon;
            document.getElementById('qrRadioLabel').textContent = radio;
            document.getElementById('mapaLink').innerHTML = `<a href="https://www.google.com/maps?q=${lat},${lon}" target="_blank" style="color:#0057A8; font-size:.85rem;">🗺 Ver en Google Maps</a>`;
            document.getElementById('qrSection').style.display = 'block';
            if (timerInterval) clearInterval(timerInterval);
            segundosRestantes = 300;
            actualizarTimer();
            timerInterval = setInterval(() => {
                segundosRestantes--;
                actualizarTimer();
                if (segundosRestantes <= 0) {
                    clearInterval(timerInterval);
                    document.getElementById('qrCanvas').innerHTML = '<p style="color:#dc2626;font-weight:600;">⏱ QR expirado. Regenera.</p>';
                }
            }, 1000);
        }

        function actualizarTimer() {
            const m = String(Math.floor(segundosRestantes/60)).padStart(2,'0');
            const s = String(segundosRestantes%60).padStart(2,'0');
            const el = document.getElementById('qrTimer');
            if (el) el.textContent = m+':'+s;
        }

        // -- Horarios Semanales ------------------------------------------------
        let tecnicosData = [];
        let horariosData = {};
        const diasSemana = ['Lunes','Martes','Miércoles','Jueves','Viernes','Sábado'];

        function getLunes(semanaStr) {
            return semanaStr; // ya viene como YYYY-MM-DD del lunes
        }

        function fechasDeSemana(lunesStr) {
            const lunes = new Date(lunesStr + 'T12:00:00');
            return Array.from({length:6}, (_,i) => {
                const d = new Date(lunes); d.setDate(lunes.getDate()+i);
                // FIX: usar Tijuana timezone, no UTC (toISOString puede dar día anterior)
                return new Intl.DateTimeFormat('en-CA', { timeZone: 'America/Tijuana' }).format(d);
            });
        }

        async function cargarHorarios() {
            const semana = document.getElementById('semanaInput').value;
            if (!semana) return;
            try {
                const [tecRes, horRes, resRes, comRes] = await Promise.all([
                    fetchAuth('/api/usuarios/'),
                    fetchAuth(`/api/horarios/?semana=${semana}`),
                    fetchAuth(`/api/horarios/resumen?semana=${semana}`),
                    fetchAuth(`/api/horarios/comentarios?semana=${semana}`)
                ]);
                const tecRaw = await tecRes.json(); tecnicosData = (Array.isArray(tecRaw) ? tecRaw : []).filter(u => u.role === 'tecnico');
                const horarios = await horRes.json();
                const resumen = await resRes.json();
                const comentarios = comRes.ok ? await comRes.json() : {};

                horariosData = {};
                horarios.forEach(h => { horariosData[h.username+'_'+h.fecha] = h; });

                const fechas = fechasDeSemana(semana);

                // Tabla editable de horarios
                let html = '<table class="horario-tbl"><thead><tr><th>Técnico</th>';
                fechas.forEach((f,i) => { html += `<th>${diasSemana[i]}<br><small style="font-weight:400;opacity:.8;">${f.slice(5)}</small></th>`; });
                html += '</tr></thead><tbody>';
                tecnicosData.forEach(tec => {
                    html += `<tr><td>${tec.username}</td>`;
                    fechas.forEach(f => {
                        const h = horariosData[tec.username+'_'+f] || {};
                        html += `<td>
                            <div style="display:flex;flex-direction:column;gap:4px;align-items:center;">
                                <input type="time" class="hor-input" data-user="${tec.username}" data-fecha="${f}" data-tipo="entrada" value="${h.hora_entrada||''}" title="Entrada">
                                <input type="time" class="hor-input" data-user="${tec.username}" data-fecha="${f}" data-tipo="salida"  value="${h.hora_salida||''}"  title="Salida">
                            </div>
                        </td>`;
                    });
                    html += '</tr>';
                });
                html += '</tbody></table>';
                document.getElementById('tablaHorarios').innerHTML = html;

                // Tabla de resumen de asistencia real
                renderResumen(resumen, fechas, comentarios, semana);

            } catch(e) {
                console.error('Error cargando horarios:', e);
                document.getElementById('tablaHorarios').innerHTML = '<p style="color:#dc2626;">Error al cargar horarios.</p>';
            }
        }

        function renderResumen(resumen, fechas, comentarios, semana) {
            comentarios = comentarios || {};
            if (!resumen.length) {
                document.getElementById('resumenSemanal').innerHTML = '<p style="color:#6b7280; padding:12px;">No hay registros de asistencia para esta semana.</p>';
                return;
            }
            const estadoLabel = {completo:'✅ Completo', retardo:'⚠️ Retardo', ausente:'❌ Ausente', libre:'🏖 Libre', sin_salida:'⚠️ Sin salida', sin_entrada:'⚠️ Sin entrada'};
            const estadoClass = {completo:'est-completo', retardo:'est-retardo', ausente:'est-ausente', libre:'est-libre', sin_salida:'est-sin_salida', sin_entrada:'est-retardo'};
            const tecnicos = [...new Set(resumen.map(r=>r.username))].sort();
            let html = '<table class="horario-tbl"><thead><tr><th>Técnico</th>';
            fechas.forEach((f,i) => { html += `<th>${diasSemana[i]}<br><small style="font-weight:400;opacity:.8;">${f.slice(5)}</small></th>`; });
            html += '<th>Hrs. trabajadas</th><th>Horas extra</th><th>Retardos</th><th>Comentarios</th></tr></thead><tbody>';
            tecnicos.forEach(tec => {
                const filas = resumen.filter(r=>r.username===tec);
                let totalHrs = 0;
                let numRetardos = 0;
                let minRetardos = 0;
                filas.forEach(r => {
                    if (r.retardo_min > 0) { numRetardos++; minRetardos += r.retardo_min; }
                });
                html += `<tr><td>${tec}</td>`;
                fechas.forEach(f => {
                    const r = filas.find(x=>x.fecha===f);
                    if (!r) { html += '<td><span class="est-libre">Libre</span></td>'; return; }
                    if (r.horas_trabajadas) totalHrs += parseFloat(r.horas_trabajadas);
                    const est = r.retardo_min > 0 ? 'retardo' : r.estado;
                    const badge = `<span class="${estadoClass[r.estado]||'est-libre'}">${estadoLabel[r.estado]||r.estado}</span>`;
                    const detalle = r.hora_entrada_real ? `<br><small style="color:#6b7280;">${r.hora_entrada_real||'—'} → ${r.hora_salida_real||'—'}</small>` : '';
                    const ret = r.retardo_min > 0 ? `<br><small style="color:#d97706;">+${r.retardo_min}min retardo</small>` : '';
                    html += `<td>${badge}${detalle}${ret}</td>`;
                });
                // Jornada ordinaria semanal = 48 h (LFT). Todo lo que exceda cuenta como hora extra.
                const horasExtra = Math.max(0, totalHrs - 48);
                const extraTxt = horasExtra > 0
                    ? `<b style="color:#d97706;">+${horasExtra.toFixed(1)} h</b>`
                    : `<span style="color:#9ca3af;">—</span>`;
                const comentarioVal = (comentarios[tec] || '').replace(/"/g, '&quot;');
                const retardosTxt = numRetardos > 0
                    ? `<span class="est-retardo">${numRetardos} ${numRetardos===1?'retardo':'retardos'}</span><br><small style="color:#d97706;">${minRetardos} min</small>`
                    : `<span style="color:#9ca3af;">—</span>`;
                html += `<td><b>${totalHrs.toFixed(1)} h</b></td><td>${extraTxt}</td><td>${retardosTxt}</td>`;
                html += `<td><textarea class="coment-input" data-user="${tec}" data-semana="${semana}"
                            placeholder="Sin comentarios..."
                            style="width:160px;min-height:44px;font-size:0.8rem;padding:6px;border:1px solid #e2e8f0;border-radius:8px;resize:vertical;font-family:inherit;"
                            onblur="guardarComentario(this)">${comentarioVal}</textarea></td></tr>`;
            });
            html += '</tbody></table>';
            document.getElementById('resumenSemanal').innerHTML = html;
        }

        async function exportarResumenSemanalImagen() {
            const el = document.getElementById('resumenSemanalWrap');
            if (!el || !el.querySelector('table')) {
                alert('No hay datos de resumen semanal para exportar.');
                return;
            }
            const btn = event && event.target ? event.target.closest('button') : null;
            const textoOriginal = btn ? btn.innerHTML : null;
            if (btn) { btn.disabled = true; btn.innerHTML = '⏳ Generando...'; }
            try {
                const canvas = await html2canvas(el, { backgroundColor: '#ffffff', scale: 2, useCORS: true });
                const semana = document.getElementById('semanaInput').value || 'semana';
                const link = document.createElement('a');
                link.download = `resumen_semanal_asistencia_${semana}.png`;
                link.href = canvas.toDataURL('image/png');
                link.click();
            } catch (e) {
                console.error('Error exportando imagen del resumen semanal:', e);
                alert('No se pudo generar la imagen. Intenta nuevamente.');
            } finally {
                if (btn) { btn.disabled = false; btn.innerHTML = textoOriginal; }
            }
        }

        let _comentarioTimers = {};
        async function guardarComentario(el) {
            const username = el.dataset.user;
            const semana = el.dataset.semana;
            const comentario = el.value;
            const key = username + '_' + semana;
            // pequeño feedback visual mientras guarda
            el.style.borderColor = '#93c5fd';
            try {
                const res = await fetchAuth('/api/horarios/comentarios', {
                    method: 'POST',
                    headers: {'Content-Type':'application/json'},
                    body: JSON.stringify({ semana, comentarios: [{ username, comentario }] })
                });
                if (res.ok) {
                    el.style.borderColor = '#86efac';
                } else {
                    el.style.borderColor = '#fca5a5';
                }
            } catch(e) {
                el.style.borderColor = '#fca5a5';
            }
            setTimeout(() => { el.style.borderColor = '#e2e8f0'; }, 1200);
        }

        async function guardarHorarios() {
            const semana = document.getElementById('semanaInput').value;
            const inputs = document.querySelectorAll('.hor-input');
            const registros = [];
            const map = {};
            inputs.forEach(inp => {
                const key = inp.dataset.user+'_'+inp.dataset.fecha;
                if (!map[key]) map[key] = {username:inp.dataset.user, fecha:inp.dataset.fecha, semana, hora_entrada:null, hora_salida:null};
                if (inp.dataset.tipo==='entrada') map[key].hora_entrada = inp.value||null;
                else map[key].hora_salida = inp.value||null;
            });
            Object.values(map).forEach(r => registros.push(r));
            try {
                const res = await fetchAuth('/api/horarios/', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({registros})});
                const data = await res.json();
                if (data.ok) {
                    alert(`✅ Guardado: ${data.guardados} horarios, ${data.eliminados} días libres.`);
                    cargarHorarios();
                } else { alert('Error al guardar.'); }
            } catch(e) { alert('Error al guardar horarios.'); }
        }

        // -- Importar Excel ----------------------------------------------------
        let _impPreview = null;
        let _impTecnicos = [];

        function abrirModalImportacion() {
            document.getElementById('modalImportacion').style.display = 'block';
            document.getElementById('imp-paso1').style.display = '';
            document.getElementById('imp-paso2').style.display = 'none';
            document.getElementById('impError').style.display = 'none';
            document.getElementById('impFile').value = '';
            document.getElementById('impResultado').style.display = 'none';
            _impPreview = null;
        }

        function cerrarModalImportacion() {
            document.getElementById('modalImportacion').style.display = 'none';
        }

        async function procesarExcel() {
            const semana = document.getElementById('semanaInput').value;
            if (!semana) { alert('Selecciona la semana primero.'); return; }
            const file = document.getElementById('impFile').files[0];
            if (!file) { alert('Selecciona un archivo .xlsx'); return; }

            const errEl = document.getElementById('impError');
            errEl.style.display = 'none';

            const fd = new FormData();
            fd.append('file', file);

            try {
                // Usar fetch directo (NO fetchAuth) para que el browser
                // ponga Content-Type: multipart/form-data con el boundary correcto.
                // Solo agregamos Authorization manualmente.
                const res = await fetch(`/api/horarios/importar-excel?semana=${semana}`, {
                    method: 'POST',
                    headers: { 'Authorization': 'Bearer ' + window.token },
                    body: fd
                });
                if (!res.ok) {
                    const err = await res.json().catch(()=>({}));
                    errEl.textContent = '❌ ' + (err.detail || 'Error ' + res.status + ' procesando el archivo.');
                    errEl.style.display = '';
                    return;
                }
                const data = await res.json();
                _impPreview = data;
                _impTecnicos = data.tecnicos_disponibles || [];
                renderPreview(data);
            } catch(e) {
                errEl.textContent = '❌ Error de red: ' + e.message;
                errEl.style.display = '';
            }
        }

        function renderPreview(data) {
            const tbody = document.getElementById('impTableBody');
            tbody.innerHTML = '';

            const badgeConf = {
                auto:      '<span style="background:#dcfce7;color:#166534;padding:2px 8px;border-radius:10px;font-size:.75rem;">Auto ✓</span>',
                manual:    '<span style="background:#dbeafe;color:#1d4ed8;padding:2px 8px;border-radius:10px;font-size:.75rem;">Excel</span>',
                sin_match: '<span style="background:#fee2e2;color:#dc2626;padding:2px 8px;border-radius:10px;font-size:.75rem;">Sin match ⚠</span>',
            };

            data.preview.forEach((row, idx) => {
                const diasCells = row.horarios.map(d =>
                    `<td style="padding:6px 8px;text-align:center;border-bottom:1px solid #f0f2f5;">${d.hora_entrada||'—'}</td>
                     <td style="padding:6px 8px;text-align:center;border-bottom:1px solid #f0f2f5;">${d.hora_salida||'—'}</td>`
                ).join('');

                const selectOptions = ['<option value="">-- sin asignar --</option>'].concat(
                    _impTecnicos.map(u => `<option value="${u}" ${u===row.username?'selected':''}>${u}</option>`)
                ).join('');

                tbody.innerHTML += `<tr>
                    <td style="padding:6px 12px;border-bottom:1px solid #f0f2f5;white-space:nowrap;">${row.nombre_excel}</td>
                    <td style="padding:6px 8px;border-bottom:1px solid #f0f2f5;">
                        <select id="imp-usr-${idx}" style="font-size:.8rem;padding:3px 6px;border:1px solid #d1d5db;border-radius:6px;">
                            ${selectOptions}
                        </select>
                    </td>
                    <td style="padding:6px 8px;text-align:center;border-bottom:1px solid #f0f2f5;">${badgeConf[row.confianza]||row.confianza}</td>
                    ${diasCells}
                </tr>`;
            });

            // Aviso sin match
            const avisoEl = document.getElementById('impAvisoSinMatch');
            if (data.sin_match && data.sin_match.length) {
                avisoEl.style.display = '';
                document.getElementById('impListaSinMatch').textContent = ' ' + data.sin_match.join(', ');
            } else {
                avisoEl.style.display = 'none';
            }

            document.getElementById('imp-paso1').style.display = 'none';
            document.getElementById('imp-paso2').style.display = '';
        }

        async function confirmarImportacion() {
            if (!_impPreview) return;
            const semana = _impPreview.semana;

            const registros = _impPreview.preview.map((row, idx) => {
                const username = document.getElementById('imp-usr-'+idx)?.value || '';
                return {
                    username,
                    horarios: row.horarios.map(d => ({
                        fecha:        d.fecha,
                        hora_entrada: d.hora_entrada || null,
                        hora_salida:  d.hora_salida  || null,
                    }))
                };
            }).filter(r => r.username);

            if (!registros.length) {
                alert('No hay filas con username asignado para importar.');
                return;
            }

            try {
                const res = await fetchAuth('/api/horarios/confirmar-importacion', {
                    method: 'POST',
                    headers: {'Content-Type':'application/json'},
                    body: JSON.stringify({semana, registros})
                });
                const data = await res.json();
                if (data.ok) {
                    const el = document.getElementById('impResultado');
                    el.textContent = `✅ Importación exitosa: ${data.guardados} horarios guardados, ${data.eliminados} eliminados.`;
                    el.style.display = '';
                    cargarHorarios();
                    setTimeout(() => cerrarModalImportacion(), 2500);
                } else {
                    alert('Error al confirmar importación.');
                }
            } catch(e) {
                alert('Error de red al importar: ' + e.message);
            }
        }

        // -- Registros del día -------------------------------------------------
        async function cargarRegistros() {
            const fecha = document.getElementById('fechaFiltro').value;
            try {
                const res = await fetchAuth(`/api/asistencia/registros?fecha=${fecha}`);
                if (!res.ok) { document.getElementById('tablaAsistencia').innerHTML = '<p style="color:#6b7280; padding:12px;">Sin registros para esta fecha.</p>'; return; }
                const data = await res.json();
                if (!data.length) { document.getElementById('tablaAsistencia').innerHTML = '<p style="color:#6b7280; padding:12px;">No hay registros para esta fecha.</p>'; return; }
                let html = `<table><thead><tr><th>#</th><th>Técnico</th><th>Tipo</th><th>Hora</th><th>Latitud</th><th>Longitud</th><th>Distancia</th><th>Retardo</th><th>Estado</th></tr></thead><tbody>`;
                data.forEach((r,i) => {
                    const badge = r.aprobado
                        ? '<span class="badge" style="background:#dcfce7;color:#16a34a;">✅ Dentro</span>'
                        : '<span class="badge" style="background:#fee2e2;color:#dc2626;">❌ Fuera</span>';
                    const tipo  = r.tipo === 'entrada' ? '🟢 Entrada' : r.tipo === 'salida' ? '🔴 Salida' : (r.tipo || '—');
                    const hora  = r.hora_checkin ? r.hora_checkin.slice(0,5) : '—';
                    const lat   = r.latitud   != null ? parseFloat(r.latitud).toFixed(5)   : '—';
                    const lon   = r.longitud  != null ? parseFloat(r.longitud).toFixed(5)  : '—';
                    const dist  = r.distancia_metros != null ? r.distancia_metros + ' m' : '—';
                    const ret   = r.retardo_min > 0 ? '<span style="color:#d97706;">+' + r.retardo_min + ' min</span>' : '<span style="color:#6b7280;">—</span>';
                    html += `<tr><td>${i+1}</td><td><b>${r.username||'—'}</b></td><td>${tipo}</td><td>${hora}</td><td>${lat}</td><td>${lon}</td><td>${dist}</td><td>${ret}</td><td>${badge}</td></tr>`;
                });
                html += '</tbody></table>';
                document.getElementById('tablaAsistencia').innerHTML = html;
            } catch(e) {
                document.getElementById('tablaAsistencia').innerHTML = '<p style="color:#dc2626;">Error al cargar registros.</p>';
            }
        }

        function exportarCSV() {
            const tabla = document.querySelector('#tablaAsistencia table');
            if (!tabla) return alert('No hay datos para exportar.');
            let csv = '';
            tabla.querySelectorAll('tr').forEach(row => {
                const cols = [...row.querySelectorAll('th,td')].map(c => '"'+c.innerText.replace(/"/g,'""')+'"');
                csv += cols.join(',') + String.fromCharCode(10);
            });
            const blob = new Blob([csv], {type:'text/csv'});
            const a = document.createElement('a'); a.href=URL.createObjectURL(blob);
            a.download=`asistencia_${document.getElementById('fechaFiltro').value}.csv`; a.click();
        }
    </script>
    """
    return HTMLResponse(content=pagina_con_menu("📍 Control de Asistencia", contenido, "asistencia"))


@router.get("/app/checkin", response_class=HTMLResponse)
async def checkin_tecnico():
    contenido = """
    <script>if (window.role !== 'tecnico' && window.role !== 'admin') { window.location.href = '/app/dashboard'; }</script>

    <style>
      /* ── Variables ── */
      :root {
        --ct-blue:       #004B87;
        --ct-blue-light: #0066BB;
        --ct-blue-dim:   #E8F0F8;
        --ct-green:      #16A34A;
        --ct-green-dim:  #DCFCE7;
        --ct-amber:      #D97706;
        --ct-amber-dim:  #FEF3C7;
        --ct-red:        #DC2626;
        --ct-red-dim:    #FEE2E2;
        --ct-bg:         #F2F1ED;
        --ct-card:       #FFFFFF;
        --ct-border:     rgba(0,0,0,0.07);
        --ct-text:       #111827;
        --ct-muted:      #6B7280;
        --ct-radius:     16px;
      }

      .ct-wrap { width:100%; max-width:460px; margin:0 auto; padding-bottom:2rem; }

      /* Greeting */
      .ct-greeting {
        background: var(--ct-blue);
        border-radius: var(--ct-radius);
        padding: 1.25rem 1.5rem;
        color: white;
        margin-bottom: 1rem;
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 12px;
      }
      .ct-greeting-left h2 { font-size:18px; font-weight:600; }
      .ct-greeting-left p  { font-size:13px; opacity:0.75; margin-top:2px; }
      .ct-greeting-time {
        font-family: 'DM Mono', monospace;
        font-size: 28px; font-weight: 500;
        letter-spacing: -1px; white-space: nowrap;
      }

      /* Today card */
      .ct-today {
        background: var(--ct-card);
        border: 1px solid var(--ct-border);
        border-radius: var(--ct-radius);
        padding: 1.25rem;
        margin-bottom: 1rem;
      }
      .ct-today-label {
        font-size:11px; font-weight:600; letter-spacing:0.08em;
        text-transform:uppercase; color:var(--ct-muted); margin-bottom:14px;
      }
      .ct-times { display:grid; grid-template-columns:1fr 1fr; gap:10px; margin-bottom:16px; }
      .ct-time-box {
        background: var(--ct-bg); border-radius:12px; padding:14px; text-align:center;
      }
      .ct-time-box .label { font-size:11px; color:var(--ct-muted); margin-bottom:6px; }
      .ct-time-box .value {
        font-family: 'DM Mono', monospace;
        font-size:24px; font-weight:500; color:var(--ct-text);
      }
      .ct-time-box .value.registered { color:var(--ct-green); }

      /* GPS pill */
      .ct-gps-pill {
        display:inline-flex; align-items:center; gap:6px;
        background:var(--ct-bg); border-radius:20px;
        padding:6px 12px; font-size:12px; color:var(--ct-muted);
        margin-bottom:16px;
      }
      .ct-gps-pill .dot {
        width:8px; height:8px; border-radius:50%;
        background:var(--ct-muted); flex-shrink:0; transition:background 0.3s;
      }
      .ct-gps-pill .dot.ok   { background:var(--ct-green); }
      .ct-gps-pill .dot.warn { background:var(--ct-amber); }
      .ct-gps-pill .dot.bad  { background:var(--ct-red); }

      /* Action buttons */
      .ct-actions { display:grid; grid-template-columns:1fr 1fr; gap:10px; }
      .ct-btn {
        padding:14px 10px; border:none; border-radius:12px;
        font-family:inherit; font-size:14px; font-weight:600;
        cursor:pointer; display:flex; align-items:center;
        justify-content:center; gap:7px;
        transition:opacity 0.15s, transform 0.1s;
      }
      .ct-btn:active { transform:scale(0.97); opacity:0.85; }
      .ct-btn-entrada { background:var(--ct-blue); color:white; }
      .ct-btn-salida  { background:var(--ct-blue-dim); color:var(--ct-blue); }
      .ct-btn:disabled { opacity:0.4; pointer-events:none; }

      /* History */
      .ct-history {
        background:var(--ct-card);
        border:1px solid var(--ct-border);
        border-radius:var(--ct-radius);
        overflow:hidden; margin-bottom:1rem;
      }
      .ct-history-header {
        padding:1rem 1.25rem 0.75rem;
        font-size:11px; font-weight:600; letter-spacing:0.08em;
        text-transform:uppercase; color:var(--ct-muted);
        border-bottom:1px solid var(--ct-border);
      }
      .ct-history-row {
        display:grid; grid-template-columns:1fr 80px 80px;
        padding:11px 1.25rem;
        border-bottom:1px solid var(--ct-border);
        align-items:center; font-size:14px;
      }
      .ct-history-row:last-child { border-bottom:none; }
      .ct-history-row .fecha { color:var(--ct-muted); font-size:13px; }
      .ct-history-row .mono  { font-family:'DM Mono',monospace; font-size:13px; font-weight:500; }
      .ct-history-row .mono.ok  { color:var(--ct-green); }
      .ct-history-row .mono.dim { color:var(--ct-muted); }

      /* Modal overlay */
      .ct-modal-overlay {
        position:fixed; inset:0;
        background:rgba(0,0,0,0.55);
        backdrop-filter:blur(4px);
        z-index:999;
        display:none; align-items:flex-end; justify-content:center;
      }
      .ct-modal-overlay.open { display:flex; }
      .ct-modal {
        background:var(--ct-card);
        border-radius:24px 24px 0 0;
        width:100%; max-width:480px;
        max-height:92vh; overflow-y:auto;
        animation:ctSlideUp 0.28s cubic-bezier(0.34,1.3,0.64,1);
      }
      @keyframes ctSlideUp {
        from { transform:translateY(60px); opacity:0; }
        to   { transform:translateY(0);    opacity:1; }
      }

      /* Progress steps */
      .ct-steps {
        display:flex; align-items:center; justify-content:center;
        gap:8px; padding:20px 24px 0;
      }
      .ct-step-dot {
        width:8px; height:8px; border-radius:50%;
        background:#E5E7EB; transition:all 0.3s;
      }
      .ct-step-dot.active  { background:var(--ct-blue); width:24px; border-radius:4px; }
      .ct-step-dot.done    { background:var(--ct-green); }

      .ct-modal-drag {
        width:40px; height:4px; background:#E5E7EB;
        border-radius:2px; margin:12px auto 0;
      }
      .ct-modal-head {
        display:flex; align-items:center; justify-content:space-between;
        padding:16px 20px 12px;
      }
      .ct-modal-head h3 { font-size:17px; font-weight:600; }
      .ct-modal-head p  { font-size:13px; color:var(--ct-muted); margin-top:2px; }
      .ct-modal-close {
        width:32px; height:32px; border-radius:50%;
        background:var(--ct-bg); border:none; cursor:pointer;
        font-size:16px; display:flex; align-items:center; justify-content:center;
        color:var(--ct-muted); flex-shrink:0;
      }
      .ct-paso { padding:0 20px 24px; }

      /* Scanner */
      .ct-scanner-wrap {
        position:relative; background:#0A1521;
        border-radius:16px; overflow:hidden; aspect-ratio:1/1;
      }
      #ct-qr-video { width:100%; height:100%; object-fit:cover; display:block; }
      .ct-scanner-frame {
        position:absolute; inset:0;
        display:flex; align-items:center; justify-content:center;
      }
      .ct-scanner-frame svg { width:65%; height:65%; opacity:0.6; }
      .ct-scan-line {
        position:absolute; left:12%; right:12%;
        height:2px;
        background:linear-gradient(90deg,transparent,#00FFCC,#00FFCC,transparent);
        animation:ctScanMove 2s ease-in-out infinite;
      }
      @keyframes ctScanMove { 0%{top:20%} 50%{top:80%} 100%{top:20%} }
      #ct-qr-status { text-align:center; font-size:13px; color:var(--ct-muted); margin-top:12px; min-height:20px; }
      .ct-qr-ok {
        background:var(--ct-green-dim); color:var(--ct-green);
        border-radius:8px; padding:8px 14px;
        font-size:13px; font-weight:500;
        text-align:center; display:none; margin-top:10px;
      }

      /* Selfie paso 2 */
      .ct-selfie-area { text-align:center; padding:10px 0 6px; }
      .ct-selfie-icon {
        width:80px; height:80px; border-radius:50%;
        background:var(--ct-blue-dim);
        display:flex; align-items:center; justify-content:center;
        margin:0 auto 16px; font-size:36px; color:var(--ct-blue);
      }
      .ct-selfie-area h4 { font-size:16px; font-weight:600; margin-bottom:6px; }
      .ct-selfie-area p  { font-size:13px; color:var(--ct-muted); line-height:1.5; }

      /* Confirm paso 3 */
      #ct-preview-img {
        width:100%; border-radius:14px; margin-bottom:14px; display:none;
        max-height:240px; object-fit:cover;
      }
      .ct-confirm-info {
        background:var(--ct-bg); border-radius:12px;
        padding:14px; margin-bottom:16px;
        display:grid; grid-template-columns:1fr 1fr; gap:10px;
      }
      .ct-confirm-info .item .k { font-size:11px; color:var(--ct-muted); text-transform:uppercase; letter-spacing:0.05em; }
      .ct-confirm-info .item .v { font-size:14px; font-weight:600; margin-top:2px; }

      /* Modal button */
      .ct-modal-btn {
        width:100%; padding:15px; border:none; border-radius:12px;
        background:var(--ct-blue); color:white;
        font-family:inherit; font-size:15px; font-weight:600;
        cursor:pointer; display:flex; align-items:center;
        justify-content:center; gap:8px;
        transition:opacity 0.15s, transform 0.1s;
      }
      .ct-modal-btn:active  { transform:scale(0.98); opacity:0.9; }
      .ct-modal-btn:disabled { opacity:0.4; pointer-events:none; }
      .ct-modal-btn.success { background:var(--ct-green); }

      /* Toast */
      .ct-toast {
        position:fixed; bottom:80px; left:50%; transform:translateX(-50%) translateY(20px);
        background:#111; color:white; border-radius:12px;
        padding:12px 20px; font-size:14px; font-weight:500;
        white-space:nowrap; opacity:0; pointer-events:none;
        transition:all 0.3s; z-index:1100;
      }
      .ct-toast.show { opacity:1; transform:translateX(-50%) translateY(0); }
      .ct-toast.green { background:var(--ct-green); }
      .ct-toast.red   { background:var(--ct-red); }
    </style>

    <div class="ct-wrap">

      <!-- Saludo / hora -->
      <div class="ct-greeting">
        <div class="ct-greeting-left">
          <h2 id="ct-saludo">Hola 👋</h2>
          <p id="ct-fecha">—</p>
        </div>
        <div class="ct-greeting-time" id="ct-hora-actual">--:--</div>
      </div>

      <!-- Turno de hoy -->
      <div class="ct-today">
        <div class="ct-today-label">Turno de hoy</div>
        <div class="ct-times">
          <div class="ct-time-box">
            <div class="label">↪ Entrada</div>
            <div class="value" id="p-hora-entrada">--:--</div>
          </div>
          <div class="ct-time-box">
            <div class="label">↩ Salida</div>
            <div class="value" id="p-hora-salida">--:--</div>
          </div>
        </div>

        <div class="ct-gps-pill">
          <div class="dot" id="ct-gps-dot"></div>
          <span id="ct-gps-label">Obteniendo ubicación...</span>
        </div>

        <div class="ct-actions">
          <button class="ct-btn ct-btn-entrada" onclick="abrirModalQR('entrada')">
            ↪ Entrada
          </button>
          <button class="ct-btn ct-btn-salida" onclick="abrirModalQR('salida')">
            ↩ Salida
          </button>
        </div>
      </div>

      <!-- Historial reciente -->
      <div class="ct-history">
        <div class="ct-history-header">📋 Historial reciente</div>
        <div id="ct-historial-body">
          <div style="padding:20px;text-align:center;color:var(--ct-muted);font-size:13px;">Cargando...</div>
        </div>
      </div>

    </div>

    <!-- ===== MODAL 3 PASOS ===== -->
    <div class="ct-modal-overlay" id="ct-modal-overlay">
      <div class="ct-modal">
        <div class="ct-modal-drag"></div>

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
            <div class="ct-selfie-icon">📸</div>
            <h4>Confirma tu identidad</h4>
            <p>Toma una foto para verificar<br>que eres tú quien registra la asistencia</p>
          </div>
          <div style="height:16px;"></div>
          <button class="ct-modal-btn" onclick="ct_lanzarFotoConfirmacion()">
            📷 Tomar selfie
          </button>
          <input type="file" id="ct-input-selfie" accept="image/*" capture="user"
                 style="display:none;" onchange="ct_onSelfieSeleccionada(this)">
        </div>

        <!-- Paso 3: Confirmar -->
        <div id="ct-paso3" class="ct-paso" style="display:none;">
          <img id="ct-preview-img" alt="Selfie">
          <div class="ct-confirm-info">
            <div class="item"><div class="k">Tipo</div><div class="v" id="ct-paso3-tipo">—</div></div>
            <div class="item"><div class="k">Hora</div><div class="v" id="ct-paso3-hora">—</div></div>
            <div class="item"><div class="k">GPS</div><div class="v" id="ct-paso3-gps">—</div></div>
            <div class="item"><div class="k">Usuario</div><div class="v" id="ct-paso3-user">—</div></div>
          </div>
          <button id="ct-btn-confirmar" class="ct-modal-btn" onclick="ct_confirmarRegistro()">
            ✅ Confirmar registro
          </button>
        </div>

      </div>
    </div>

    <!-- Toast -->
    <div class="ct-toast" id="ct-toast"></div>

    <script src="https://cdn.jsdelivr.net/npm/jsqr@1.4.0/dist/jsQR.js"></script>
    <script>
    // ── Estado global ──────────────────────────────────────────────────────────
    var _ctTipo        = null;   // 'entrada' | 'salida'
    var _ctStream      = null;   // MediaStream de la cámara
    var _ctScanLoop    = null;   // setInterval del scanner
    var _ctSelfieB64   = null;   // foto base64
    var _ctGeocoords   = null;   // { lat, lon, accuracy }
    var _ctGpsWatchId  = null;   // watchPosition ID para limpiar al salir
    var _ctGeocerca    = null;   // { lat_fija, lon_fija, radio_metros }

    // ── Toast ──────────────────────────────────────────────────────────────────
    function ctToast(msg, type) {
      var t = document.getElementById('ct-toast');
      t.textContent = msg;
      t.className = 'ct-toast show ' + (type || '');
      setTimeout(function() { t.className = 'ct-toast'; }, 3200);
    }

    // ── Hora / Saludo ──────────────────────────────────────────────────────────
    function _ctActualizarHora() {
      var hora = new Intl.DateTimeFormat('es-MX', { timeZone:'America/Tijuana', hour:'2-digit', minute:'2-digit', hour12:false }).format(new Date());
      var el = document.getElementById('ct-hora-actual');
      if (el) el.textContent = hora;
    }
    setInterval(_ctActualizarHora, 15000);
    _ctActualizarHora();

    (function() {
      var ahora = new Date();
      var fechaEl = document.getElementById('ct-fecha');
      if (fechaEl) fechaEl.textContent = ahora.toLocaleDateString('es-MX', { weekday:'long', day:'numeric', month:'long' });
      var h = parseInt(new Date().toLocaleString('es-MX', { timeZone:'America/Tijuana', hour:'numeric', hour12:false }));
      var saludo = h < 12 ? '¡Buenos días 👋' : h < 19 ? '¡Buenas tardes 👋' : '¡Buenas noches 👋';
      var saludoEl = document.getElementById('ct-saludo');
      if (saludoEl) saludoEl.textContent = saludo;
    })();

    // ── Carga de datos ─────────────────────────────────────────────────────────
    async function _ctCargarHorarioHoy() {
      try {
        var hoy = new Intl.DateTimeFormat('en-CA', { timeZone:'America/Tijuana' }).format(new Date());
        var username = window.username || '';
        var res = await window.fetchAuth('/api/horarios/hoy?username=' + username + '&fecha=' + hoy);
        var data = await res.json();
        var h = data.horario || {};
        var eEl = document.getElementById('p-hora-entrada');
        var sEl = document.getElementById('p-hora-salida');
        if (h.hora_entrada) { eEl.textContent = h.hora_entrada.slice(0,5); eEl.classList.add('registered'); }
        if (h.hora_salida)  { sEl.textContent = h.hora_salida.slice(0,5);  sEl.classList.add('registered'); }
      } catch(e) {}
    }

    async function _ctCargarHistorial() {
      try {
        var res = await window.fetchAuth('/api/horarios/mios');
        var data = await res.json();
        var body = document.getElementById('ct-historial-body');
        if (!data || data.length === 0) {
          body.innerHTML = '<div style="padding:20px;text-align:center;color:var(--ct-muted);font-size:13px;">Sin registros recientes</div>';
          return;
        }
        body.innerHTML = data.slice(0, 7).map(function(h) {
          var entrada = h.hora_entrada ? '<span class="mono ok">' + h.hora_entrada.slice(0,5) + '</span>' : '<span class="mono dim">—</span>';
          var salida  = h.hora_salida  ? '<span class="mono ok">' + h.hora_salida.slice(0,5)  + '</span>' : '<span class="mono dim">—</span>';
          return '<div class="ct-history-row"><span class="fecha">' + h.fecha + '</span>' + entrada + salida + '</div>';
        }).join('');
      } catch(e) {}
    }

    // ── Geocerca ───────────────────────────────────────────────────────────────
    async function _ctCargarGeocerca() {
      // 1. Primero intentar parámetros URL (QR dinámico del admin)
      var params = new URLSearchParams(window.location.search);
      if (params.has('lat') && params.has('lon') && params.has('radio')) {
        _ctGeocerca = {
          lat_fija:    parseFloat(params.get('lat')),
          lon_fija:    parseFloat(params.get('lon')),
          radio_metros: parseInt(params.get('radio'))
        };
        return;
      }
      // 2. Sin parámetros: cargar del servidor (QR fijo impreso)
      try {
        var res = await window.fetchAuth('/api/asistencia/configuracion');
        if (res.ok) _ctGeocerca = await res.json();
      } catch(e) {}
    }

    // ── GPS badge ──────────────────────────────────────────────────────────────
    function _ctGPSBadge(accuracy) {
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
      _ctCargarHorarioHoy();
      _ctCargarHistorial();

      // Deshabilitar botones hasta que la geocerca esté lista
      var btnE = document.querySelector('.ct-btn-entrada');
      var btnS = document.querySelector('.ct-btn-salida');
      if (btnE) btnE.disabled = true;
      if (btnS) btnS.disabled = true;

      _ctCargarGeocerca().then(function() {
        if (_ctGeocerca) {
          if (btnE) btnE.disabled = false;
          if (btnS) btnS.disabled = false;
        } else {
          var gpsLabel = document.getElementById('ct-gps-label');
          if (gpsLabel) gpsLabel.textContent = '⚠️ Sin configuración de geocerca';
        }
      });

      if (navigator.geolocation) {
        // ── watchPosition: actualiza continuamente, conserva la mejor lectura ──
        function _ctOnGPSUpdate(pos) {
          var acc = pos.coords.accuracy;
          // Guardar siempre la lectura más precisa que hayamos visto
          if (!_ctGeocoords || acc < _ctGeocoords.accuracy) {
            _ctGeocoords = { lat: pos.coords.latitude, lon: pos.coords.longitude, accuracy: acc };
          }
          _ctGPSBadge(_ctGeocoords.accuracy);
          // Si ya tenemos buena precisión, cancelar el watch para ahorrar batería
          if (_ctGeocoords.accuracy <= 50 && _ctGpsWatchId !== null) {
            navigator.geolocation.clearWatch(_ctGpsWatchId);
            _ctGpsWatchId = null;
          }
        }
        function _ctOnGPSError(err) {
          var dot   = document.getElementById('ct-gps-dot');
          var label = document.getElementById('ct-gps-label');
          if (dot)   dot.className   = 'dot bad';
          if (label) label.textContent = err.code === 1 ? 'Sin permiso de ubicación' : 'GPS no disponible';
        }
        var _gpsOpts = { enableHighAccuracy: true, timeout: 15000, maximumAge: 0 };
        // Primera lectura rápida (puede ser de red, no importa, irá mejorando)
        navigator.geolocation.getCurrentPosition(_ctOnGPSUpdate, _ctOnGPSError, _gpsOpts);
        // Watch para ir refinando hasta alcanzar ≤50m o hasta que se cierre el modal
        _ctGpsWatchId = navigator.geolocation.watchPosition(_ctOnGPSUpdate, _ctOnGPSError, _gpsOpts);
      }
    });

    // ── Modal QR ───────────────────────────────────────────────────────────────
    function abrirModalQR(tipo) {
      _ctTipo      = tipo;
      _ctSelfieB64 = null;

      var label = tipo === 'entrada' ? 'Entrada' : 'Salida';
      document.getElementById('ct-modal-overlay').classList.add('open');

      // Si la geocerca ya está cargada (QR fijo del PDF o QR dinámico con params URL)
      // → saltar el scanner y ir directo a selfie
      if (_ctGeocerca) {
        _ctIrPaso(2);
        document.getElementById('ct-modal-title').textContent    = 'Foto de verificación — ' + label;
        document.getElementById('ct-modal-subtitle').textContent = 'Toma una selfie para verificar tu identidad';
      } else {
        // Geocerca aún no cargada → mostrar scanner QR
        _ctIrPaso(1);
        document.getElementById('ct-modal-title').textContent    = 'Escanear QR — ' + label;
        document.getElementById('ct-modal-subtitle').textContent = 'Apunta la cámara al código QR';
        _ctIniciarScanner();
      }
    }

    function cerrarModalQR() {
      document.getElementById('ct-modal-overlay').classList.remove('open');
      _ctDetenerCamara();
      // Liberar el watchPosition al cerrar el modal
      if (_ctGpsWatchId !== null && navigator.geolocation) {
        navigator.geolocation.clearWatch(_ctGpsWatchId);
        _ctGpsWatchId = null;
      }
    }

    // ── Paso 1: Scanner QR ─────────────────────────────────────────────────────
    function _ctIniciarScanner() {
      document.getElementById('ct-qr-status').textContent = 'Solicitando cámara...';
      document.getElementById('ct-qr-result').style.display = 'none';

      navigator.mediaDevices.getUserMedia({ video: { facingMode: 'environment' } })
        .then(function(stream) {
          _ctStream = stream;
          var video = document.getElementById('ct-qr-video');
          video.srcObject = stream;
          video.play();
          document.getElementById('ct-qr-status').textContent = '🔍 Apunta al código QR...';
          _ctScanLoop = setInterval(_ctEscanearFrame, 300);
        })
        .catch(function() {
          // Si no hay cámara, intentar con parámetros de URL o geocerca cargada
          document.getElementById('ct-qr-status').textContent = '⚠️ Sin cámara — usando configuración del servidor';
          if (_ctGeocerca) {
            setTimeout(function() {
              document.getElementById('ct-qr-result').style.display = 'block';
              document.getElementById('ct-qr-result').textContent = '✅ Geocerca cargada correctamente';
              setTimeout(function() { _ctIrPaso(2); }, 900);
            }, 600);
          } else {
            document.getElementById('ct-qr-status').textContent = '❌ No hay cámara ni configuración. Recarga la página.';
          }
        });
    }

    function _ctEscanearFrame() {
      var video  = document.getElementById('ct-qr-video');
      var canvas = document.getElementById('ct-qr-canvas');
      if (!video || video.readyState !== video.HAVE_ENOUGH_DATA) return;
      canvas.width  = video.videoWidth;
      canvas.height = video.videoHeight;
      var ctx = canvas.getContext('2d');
      ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
      var imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
      var code = jsQR(imageData.data, imageData.width, imageData.height);
      if (!code) return;

      // QR detectado — parsear
      clearInterval(_ctScanLoop);
      try {
        var url = new URL(code.data);
        var p   = url.searchParams;
        var lat  = parseFloat(p.get('lat'));
        var lon  = parseFloat(p.get('lon'));
        var rad  = parseInt(p.get('radio'));
        if (isNaN(lat) || isNaN(lon)) throw new Error('sin coordenadas');
        _ctGeocerca = { lat_fija: lat, lon_fija: lon, radio_metros: rad };
        document.getElementById('ct-qr-result').style.display = 'block';
        document.getElementById('ct-qr-status').textContent   = '✅ QR reconocido';
        _ctDetenerCamara();
        setTimeout(function() { _ctIrPaso(2); }, 700);
      } catch(e) {
        document.getElementById('ct-qr-status').textContent = '❌ QR no reconocido. Intenta de nuevo.';
        _ctScanLoop = setInterval(_ctEscanearFrame, 300);
      }
    }

    // ── Paso 2: Selfie ─────────────────────────────────────────────────────────
    function ct_lanzarFotoConfirmacion() {
      document.getElementById('ct-input-selfie').click();
    }

    function ct_onSelfieSeleccionada(input) {
      if (!input.files || !input.files[0]) return;
      var file = input.files[0];
      // Comprimir con Canvas antes de guardar — máx 800px, calidad 0.65 (~150KB)
      var blobURL = URL.createObjectURL(file);
      var tempImg = new Image();
      tempImg.onload = function() {
        URL.revokeObjectURL(blobURL);
        var MAX = 800;
        var w = tempImg.width, h = tempImg.height;
        if (w > MAX || h > MAX) {
          var ratio = Math.min(MAX / w, MAX / h);
          w = Math.round(w * ratio);
          h = Math.round(h * ratio);
        }
        var canvas = document.createElement('canvas');
        canvas.width = w; canvas.height = h;
        canvas.getContext('2d').drawImage(tempImg, 0, 0, w, h);
        _ctSelfieB64 = canvas.toDataURL('image/jpeg', 0.65);
        _ctMostrarPaso3();
      };
      tempImg.onerror = function() {
        // Fallback: usar FileReader directo si canvas falla
        var reader = new FileReader();
        reader.onload = function(e) { _ctSelfieB64 = e.target.result; _ctMostrarPaso3(); };
        reader.readAsDataURL(file);
      };
      tempImg.src = blobURL;
    }

    function _ctMostrarPaso3() {
        _ctIrPaso(3);
        var img = document.getElementById('ct-preview-img');
        img.src = _ctSelfieB64;
        img.style.display = 'block';
        var hora = new Intl.DateTimeFormat('es-MX', { timeZone:'America/Tijuana', hour:'2-digit', minute:'2-digit', hour12:false }).format(new Date());
        document.getElementById('ct-paso3-tipo').textContent = _ctTipo === 'entrada' ? 'Entrada' : 'Salida';
        document.getElementById('ct-paso3-hora').textContent = hora;
        document.getElementById('ct-paso3-user').textContent = window.username || '—';
        if (_ctGeocoords) {
          document.getElementById('ct-paso3-gps').textContent = '±' + Math.round(_ctGeocoords.accuracy || 0) + 'm';
        } else {
          document.getElementById('ct-paso3-gps').textContent = 'Sin GPS';
        }
    }

    // ── GPS: obtener lectura fresca con timeout ────────────────────────────────
    function _ctGetFreshGPS(maxAccuracy, timeoutMs) {
      return new Promise(function(resolve, reject) {
        if (!navigator.geolocation) { resolve(null); return; }
        var done = false;
        var timer = setTimeout(function() {
          if (!done) { done = true; resolve(_ctGeocoords); } // usar lo que tengamos
        }, timeoutMs);
        navigator.geolocation.getCurrentPosition(
          function(pos) {
            if (done) return; done = true; clearTimeout(timer);
            var candidate = { lat: pos.coords.latitude, lon: pos.coords.longitude, accuracy: pos.coords.accuracy };
            // Conservar la mejor entre la nueva y la acumulada por watchPosition
            var best = (!_ctGeocoords || candidate.accuracy < _ctGeocoords.accuracy) ? candidate : _ctGeocoords;
            _ctGeocoords = best;
            _ctGPSBadge(best.accuracy);
            resolve(best);
          },
          function() { if (!done) { done = true; clearTimeout(timer); resolve(_ctGeocoords); } },
          { enableHighAccuracy: true, timeout: timeoutMs - 500, maximumAge: 0 }
        );
      });
    }

    // ── Paso 3: Confirmar ──────────────────────────────────────────────────────
    async function ct_confirmarRegistro() {
      var btn = document.getElementById('ct-btn-confirmar');
      btn.disabled = true;
      btn.textContent = '⏳ Obteniendo GPS...';

      // Si la precisión actual es mala, intentar una lectura fresca (hasta 12s)
      var currentAcc = _ctGeocoords ? _ctGeocoords.accuracy : 9999;
      if (currentAcc > 80) {
        var fresh = await _ctGetFreshGPS(80, 12000);
        if (fresh) _ctGeocoords = fresh;
      }

      btn.textContent = '⏳ Enviando...';

      var lat = null, lon = null, accuracy = null;
      if (_ctGeocoords) {
        lat      = _ctGeocoords.lat;
        lon      = _ctGeocoords.lon;
        accuracy = _ctGeocoords.accuracy || null;
      }

      try {
        var res = await window.fetchAuth('/api/asistencia/registrar', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            tipo:       _ctTipo,
            lat:        lat,
            lon:        lon,
            accuracy:   accuracy,
            foto_base64: _ctSelfieB64 || null
          })
        });
        var data = await res.json();

        if (res.ok && data.ok) {
          btn.textContent = '✅ ¡Registrado!';
          btn.classList.add('success');
          ctToast(data.mensaje || '✅ Asistencia registrada', 'green');
          // Actualizar horario de hoy en la tarjeta
          _ctCargarHorarioHoy();
          _ctCargarHistorial();
          setTimeout(function() { cerrarModalQR(); }, 1500);
        } else {
          var detalle = data.detail || {};
          var msg = (typeof detalle === 'string') ? detalle : (detalle.mensaje || JSON.stringify(detalle));
          ctToast('❌ ' + msg, 'red');
          btn.disabled = false;
          btn.textContent = '✅ Confirmar registro';
        }
      } catch(e) {
        ctToast('❌ Error de conexión. Intenta de nuevo.', 'red');
        btn.disabled = false;
        btn.textContent = '✅ Confirmar registro';
      }
    }

    // ── Navegación pasos ───────────────────────────────────────────────────────
    function _ctIrPaso(n) {
      [1,2,3].forEach(function(i) {
        document.getElementById('ct-paso' + i).style.display = i === n ? 'block' : 'none';
        var dot = document.getElementById('dot' + i);
        dot.className = 'ct-step-dot' + (i < n ? ' done' : i === n ? ' active' : '');
      });
      var titulos = ['Escanear QR', 'Foto de verificación', 'Confirmar registro'];
      var subtitulos = ['Apunta la cámara al código QR', 'Toma una selfie para verificar tu identidad', 'Revisa los datos y confirma'];
      document.getElementById('ct-modal-title').textContent    = titulos[n-1];
      document.getElementById('ct-modal-subtitle').textContent = subtitulos[n-1];
    }

    function _ctDetenerCamara() {
      if (_ctScanLoop) { clearInterval(_ctScanLoop); _ctScanLoop = null; }
      if (_ctStream)   { _ctStream.getTracks().forEach(function(t){ t.stop(); }); _ctStream = null; }
    }
    </script>
    """
    return HTMLResponse(content=pagina_con_menu("📍 Registrar Asistencia", contenido, "checkin"))

# ------------------------------------------------------------
# ALARM TROUBLESHOOTING (admin, visor, tecnico)
# ------------------------------------------------------------
@router.get("/app/alarmas", response_class=HTMLResponse)
async def alarmas():
    contenido = """
    <style>
        .alarm-search-bar {
            display: flex; gap: 12px; margin-bottom: 20px; align-items: center; flex-wrap: wrap;
        }
        .alarm-search-bar input {
            flex: 1; min-width: 200px; padding: 12px 16px; border: 1.5px solid #c3d4f0;
            border-radius: 10px; font-size: 1rem; margin-bottom: 0;
        }
        .alarm-search-bar input:focus { border-color: var(--carrier-accent); }
        .alarm-search-bar button { width: auto; padding: 12px 24px; }
        .alarm-card {
            background: white; border-radius: 14px; padding: 20px 22px; margin-bottom: 14px;
            box-shadow: 0 2px 12px rgba(0,43,91,0.07); border-left: 6px solid var(--carrier-accent);
            cursor: pointer; transition: box-shadow 0.2s, transform 0.15s;
        }
        .alarm-card:hover { box-shadow: 0 6px 24px rgba(0,43,91,0.13); transform: translateY(-2px); }
        .alarm-code {
            font-family: monospace; font-size: 1.05rem; font-weight: 800;
            color: var(--carrier-blue); background: var(--carrier-light);
            padding: 3px 10px; border-radius: 6px; margin-right: 10px;
        }
        .alarm-title { font-size: 1rem; font-weight: 700; color: var(--carrier-blue); }
        .alarm-ref { border-left-color: #d97706; }
        .alarm-ref .alarm-code { color: #d97706; background: #fef3c7; }
        /* Detail modal */
        .alarm-modal {
            position: fixed; top: 0; left: 0; width: 100%; height: 100%;
            background: rgba(0,0,0,0.52); z-index: 400;
            display: none; justify-content: center; align-items: flex-start;
            padding: 24px 12px; overflow-y: auto;
        }
        .alarm-modal.open { display: flex; }
        .alarm-modal-content {
            background: white; border-radius: 18px; width: 100%; max-width: 720px;
            padding: 28px 30px; box-shadow: 0 12px 48px rgba(0,43,91,0.22);
            animation: modalIn 0.22s ease; margin: auto;
        }
        @keyframes modalIn { from { opacity:0; transform: translateY(20px); } to { opacity:1; transform:none; } }
        .alarm-modal-header {
            display: flex; align-items: flex-start; justify-content: space-between;
            gap: 12px; margin-bottom: 18px;
        }
        .alarm-modal-close {
            background: #f1f5f9; border: none; border-radius: 8px; padding: 8px 14px;
            font-size: 1rem; cursor: pointer; color: #374151; flex-shrink: 0;
        }
        .alarm-section {
            background: #f8fafc; border-radius: 10px; padding: 14px 16px; margin-bottom: 12px;
            border-left: 4px solid var(--carrier-accent);
        }
        .alarm-section-title {
            font-size: 0.78rem; font-weight: 700; color: var(--carrier-accent);
            text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 8px;
        }
        .alarm-section p { margin: 0; font-size: 0.9rem; line-height: 1.6; white-space: pre-wrap; }
        .corrective-step {
            display: flex; gap: 12px; padding: 10px 0; border-bottom: 1px solid #e5e7eb;
        }
        .corrective-step:last-child { border-bottom: none; }
        .step-num {
            background: var(--carrier-blue); color: white; border-radius: 50%;
            width: 26px; height: 26px; display: flex; align-items: center; justify-content: center;
            font-size: 0.78rem; font-weight: 700; flex-shrink: 0; margin-top: 1px;
        }
        .step-text { font-size: 0.88rem; line-height: 1.65; }
        .ref-banner {
            background: #fef3c7; border: 1.5px solid #f59e0b; border-radius: 10px;
            padding: 14px 18px; font-size: 0.9rem; color: #92400e; margin-bottom: 14px;
        }
        .ref-banner a { color: #d97706; font-weight: 700; cursor: pointer; text-decoration: underline; }
        #alarmResults p { color: #6b7280; padding: 16px 0; }
    </style>

    <div class="alarm-search-bar">
        <input type="text" id="alarmQuery" placeholder="Código (ej: 00128 o A00128) o término (ej: coolant, sensor…)"
               onkeydown="if(event.key==='Enter') buscarAlarma()">
        <button class="btn-primary" onclick="buscarAlarma()">🔍 Buscar</button>
        <button id="btnSeed" class="btn-warning" style="width:auto;padding:12px 18px;font-size:.85rem;display:none;" onclick="seedAlarmas()">⚙️ Cargar datos</button>
    </div>

    <div id="alarmResults"></div>

    <!-- Detail modal -->
    <div class="alarm-modal" id="alarmModal">
        <div class="alarm-modal-content" id="alarmModalContent"></div>
    </div>

    <script>
        const fetchAuth = window.fetchAuth;

        // Normaliza el código: quita prefijo de letras antes de dígitos (A00128 → 00128)
        function normalizarQuery(q) {
            return q.trim().replace(/^[A-Za-z\s]+(?=\d)/, '').trim();
        }

        // Verificar al cargar si la tabla tiene datos
        (async () => {
            try {
                const res = await fetchAuth('/api/alarmas/buscar?q=00012');
                if (res.ok) {
                    const data = await res.json();
                    if (data.length === 0 && window.role === 'admin') {
                        document.getElementById('btnSeed').style.display = 'inline-block';
                        document.getElementById('alarmResults').innerHTML =
                            '<p style="color:#d97706;">⚠️ La base de alarmas está vacía. Haz clic en <b>⚙️ Cargar datos</b> para inicializarla.</p>';
                    }
                }
            } catch(e) {}
        })();

        async function seedAlarmas() {
            const btn = document.getElementById('btnSeed');
            btn.disabled = true; btn.textContent = '⏳ Cargando...';
            try {
                const res = await fetchAuth('/api/alarmas/seed');
                const data = await res.json();
                if (res.ok && data.ok) {
                    btn.style.display = 'none';
                    document.getElementById('alarmResults').innerHTML =
                        '<p style="color:var(--carrier-success);">✅ ' + data.mensaje + ' Ahora puedes buscar alarmas.</p>';
                } else {
                    alert('Error: ' + (data.detail || data.mensaje || 'No se pudo cargar'));
                    btn.disabled = false; btn.textContent = '⚙️ Cargar datos';
                }
            } catch(e) {
                alert('Error de red');
                btn.disabled = false; btn.textContent = '⚙️ Cargar datos';
            }
        }

        async function buscarAlarma() {
            const raw = document.getElementById('alarmQuery').value.trim();
            if (!raw) { document.getElementById('alarmResults').innerHTML = '<p>Escribe un código o término de búsqueda.</p>'; return; }
            const q = normalizarQuery(raw) || raw;
            document.getElementById('alarmResults').innerHTML = '<p>⏳ Buscando...</p>';
            try {
                const res = await fetchAuth('/api/alarmas/buscar?q=' + encodeURIComponent(q));
                if (!res.ok) { document.getElementById('alarmResults').innerHTML = '<p style="color:red;">Error al buscar.</p>'; return; }
                const data = await res.json();
                if (!data.length) {
                    document.getElementById('alarmResults').innerHTML =
                        '<p>No se encontraron alarmas para "' + raw + '"' +
                        (raw !== q ? ' (buscado como: <b>' + q + '</b>)' : '') + '.</p>';
                    return;
                }
                renderResults(data);
            } catch(e) {
                document.getElementById('alarmResults').innerHTML = '<p style="color:red;">Error de conexión.</p>';
            }
        }

        function renderResults(alarmas) {
            let html = `<p style="font-size:.85rem;color:#6b7280;margin-bottom:12px;">${alarmas.length} resultado(s)</p>`;
            alarmas.forEach(a => {
                const ref = a.referencia_alarma && typeof a.referencia_alarma === 'string'
                    ? (() => { try { return JSON.parse(a.referencia_alarma); } catch(e) { return null; } })()
                    : (a.referencia_alarma || null);
                const isRef = ref && ref.codigo;
                const figs = a.figuras && typeof a.figuras === 'string'
                    ? (() => { try { return JSON.parse(a.figuras); } catch(e) { return []; } })()
                    : (a.figuras || []);
                html += `<div class="alarm-card ${isRef ? 'alarm-ref' : ''}" onclick='abrirAlarma(${JSON.stringify(JSON.stringify(a))})'>
                    <span class="alarm-code">${a.codigo}</span>
                    <span class="alarm-title">${a.titulo}</span>
                    ${isRef ? '<span style="font-size:.78rem;color:#d97706;margin-left:8px;">→ ver alarma ' + ref.codigo + '</span>' : ''}
                    ${figs.length ? '<span style="font-size:.78rem;color:#7c3aed;margin-left:8px;">📐 con diagrama</span>' : ''}
                </div>`;
            });
            document.getElementById('alarmResults').innerHTML = html;
        }

        function abrirAlarma(jsonStr) {
            const a = JSON.parse(jsonStr);
            const ref = a.referencia_alarma && typeof a.referencia_alarma === 'string'
                ? (() => { try { return JSON.parse(a.referencia_alarma); } catch(e) { return null; } })()
                : (a.referencia_alarma || null);

            const acciones = a.acciones_correctivas && typeof a.acciones_correctivas === 'string'
                ? (() => { try { return JSON.parse(a.acciones_correctivas); } catch(e) { return []; } })()
                : (a.acciones_correctivas || []);

            const relacionadas = a.alarmas_relacionadas && typeof a.alarmas_relacionadas === 'string'
                ? (() => { try { return JSON.parse(a.alarmas_relacionadas); } catch(e) { return []; } })()
                : (a.alarmas_relacionadas || []);

            const figuras = a.figuras && typeof a.figuras === 'string'
                ? (() => { try { return JSON.parse(a.figuras); } catch(e) { return []; } })()
                : (a.figuras || []);

            let html = `
            <div class="alarm-modal-header">
                <div>
                    <span class="alarm-code" style="font-size:1.2rem;">${a.codigo}</span>
                    <h2 style="margin:10px 0 4px;color:var(--carrier-blue);font-size:1.25rem;">${a.titulo}</h2>
                    ${relacionadas.length ? '<p style="font-size:.82rem;color:#6b7280;">También cubre: ' + relacionadas.join(', ') + '</p>' : ''}
                </div>
                <button class="alarm-modal-close" onclick="cerrarModal()">✕ Cerrar</button>
            </div>`;

            if (ref && ref.codigo) {
                html += `<div class="ref-banner">⚠️ Esta alarma remite al procedimiento de la alarma
                    <a onclick='buscarYAbrir("${ref.codigo}")'>${ref.codigo} — ${ref.titulo || ''}</a>
                </div>`;
            }

            if (a.activacion) html += `<div class="alarm-section"><div class="alarm-section-title">⚡ Condición de activación</div><p>${a.activacion}</p></div>`;
            if (a.control_unidad) html += `<div class="alarm-section"><div class="alarm-section-title">🔧 Control de la unidad</div><p>${a.control_unidad}</p></div>`;
            if (a.condicion_reset) html += `<div class="alarm-section"><div class="alarm-section-title">♻️ Condición de reset</div><p>${a.condicion_reset}</p></div>`;
            if (a.notas) html += `<div class="alarm-section" style="border-left-color:#d97706;"><div class="alarm-section-title" style="color:#d97706;">📝 Notas</div><p>${a.notas}</p></div>`;

            if (acciones && acciones.length) {
                html += `<div class="alarm-section" style="border-left-color:var(--carrier-blue);">
                    <div class="alarm-section-title">🛠 Acciones correctivas</div>`;
                acciones.forEach(ac => {
                    html += `<div class="corrective-step">
                        <div class="step-num">${ac.numero}</div>
                        <div class="step-text">${ac.texto}</div>
                    </div>`;
                });
                html += `</div>`;
            }

            if (figuras && figuras.length) {
                html += `<div class="alarm-section" style="border-left-color:#7c3aed;">
                    <div class="alarm-section-title" style="color:#7c3aed;">📐 Diagrama de referencia</div>`;
                figuras.forEach(fig => {
                    html += `<p style="font-size:.85rem;color:#6b7280;margin-bottom:6px;">${fig.titulo || ''}</p>
                        <img src="${fig.url}" alt="${fig.titulo || 'Figura'}"
                             style="width:100%;max-width:520px;border:1.5px solid #c3d4f0;border-radius:10px;cursor:zoom-in;display:block;margin-bottom:14px;"
                             onclick="window.open('${fig.url}', '_blank')">`;
                });
                html += `</div>`;
            }

            document.getElementById('alarmModalContent').innerHTML = html;
            document.getElementById('alarmModal').classList.add('open');
        }

        async function buscarYAbrir(codigo) {
            cerrarModal();
            try {
                const res = await fetchAuth('/api/alarmas/' + codigo);
                if (res.ok) { abrirAlarma(JSON.stringify(await res.json())); }
            } catch(e) {}
        }

        function cerrarModal() {
            document.getElementById('alarmModal').classList.remove('open');
        }

        document.getElementById('alarmModal').addEventListener('click', function(e) {
            if (e.target === this) cerrarModal();
        });
    </script>
    """
    return HTMLResponse(content=pagina_con_menu("🔔 Alarm Troubleshooting", contenido, "alarmas"))
