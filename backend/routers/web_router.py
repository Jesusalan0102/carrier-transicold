from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse, PlainTextResponse
from db import execute_read, execute_write
from auth import verify_token
from pydantic import BaseModel
from typing import List

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

    /* ── Búsqueda global (Ctrl+K) ────────────────────────────────────── */
    .global-search-trigger {
        display: flex; align-items: center; gap: 8px;
        background: var(--card-bg, #fff); border: 1px solid var(--border-color, #d8dee6);
        border-radius: 8px; padding: 8px 14px; font-size: 0.85rem; cursor: pointer;
        color: var(--text-secondary, #5a6b82);
    }
    .global-search-trigger:hover { border-color: #6366f1; color: #6366f1; }
    .global-search-trigger-kbd {
        font-size: 0.7rem; background: rgba(99,102,241,0.1); color: #6366f1;
        padding: 2px 6px; border-radius: 4px; font-family: monospace;
    }
    @media (max-width: 640px) { .global-search-trigger-label, .global-search-trigger-kbd { display: none; } }

    .global-search-overlay {
        display: none; position: fixed; inset: 0; background: rgba(15,23,42,0.55);
        z-index: 3000; align-items: flex-start; justify-content: center; padding-top: 10vh;
    }
    .global-search-overlay.open { display: flex; }
    .global-search-box {
        width: min(560px, 92vw); background: var(--card-bg, #fff); border-radius: 14px;
        box-shadow: 0 20px 60px rgba(0,0,0,0.35); overflow: hidden; max-height: 70vh;
        display: flex; flex-direction: column;
    }
    .global-search-box input {
        border: none; border-bottom: 1px solid var(--border-color, #e5e9f0); padding: 18px 20px;
        font-size: 1.05rem; outline: none; background: transparent; color: var(--text-primary, #1a2332);
    }
    .global-search-results { overflow-y: auto; padding: 8px 0; }
    .global-search-hint { padding: 16px 20px; color: var(--text-secondary, #8a97ab); font-size: 0.9rem; margin: 0; }
    .global-search-section {
        padding: 10px 20px 4px; font-size: 0.72rem; font-weight: 700; letter-spacing: .04em;
        text-transform: uppercase; color: #6366f1;
    }
    .global-search-item {
        display: flex; flex-direction: column; padding: 10px 20px; text-decoration: none;
        color: var(--text-primary, #1a2332); border-bottom: 1px solid var(--border-color, #f0f2f5);
    }
    .global-search-item:hover { background: rgba(99,102,241,0.08); }
    .global-search-item-titulo { font-weight: 600; font-size: 0.92rem; }
    .global-search-item-sub { font-size: 0.8rem; color: var(--text-secondary, #8a97ab); }
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
                <div style="display:flex; align-items:center; gap:10px;">
                    <button id="globalSearchBtn" onclick="abrirBusquedaGlobal()" class="global-search-trigger" title="Buscar en todo el sistema">
                        🔍 <span class="global-search-trigger-label">Buscar</span>
                        <span class="global-search-trigger-kbd">Ctrl K</span>
                    </button>
                    <div id="liveClock" class="time-badge"></div>
                </div>
            </div>

            <!-- ── Búsqueda global (Ctrl+K) ─────────────────────────────── -->
            <div id="globalSearchOverlay" class="global-search-overlay" onclick="if(event.target===this)cerrarBusquedaGlobal()">
                <div class="global-search-box">
                    <input id="globalSearchInput" type="text" placeholder="Buscar unidad, ticket, evidencia… (mínimo 2 letras)" autocomplete="off" oninput="_onGlobalSearchInput()">
                    <div id="globalSearchResults" class="global-search-results"></div>
                </div>
            </div>
            <div id="visorBanner" style="display:none" class="visor-banner">👁 Modo solo lectura — No tienes permisos para editar</div>
            <script>if(window.role==='visor') document.getElementById('visorBanner').style.display='block';</script>
            {contenido}
        </div>


        <script>
            document.addEventListener('DOMContentLoaded', function() {{
                if (window.role === 'visor') {{ document.body.classList.add('visor-mode'); }}
                document.getElementById('sidebarUser').textContent = window.username;
                const roleLabels = {{ admin: '🛡 Administrador', tecnico: '🔧 Técnico', visor: '👁 Visor', lider: '⭐ Líder' }};
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
                    {{ href: '/app/pdi', label: '📋 PDI Pre-Entrega' }},
                    {{ href: '/app/usuarios', label: '👥 Gestión de Usuarios' }},
                    {{ href: '/app/cluster', label: '⚡ Asignación por Cluster' }},
                    {{ href: '/app/asistencia', label: '📍 Control de Asistencia' }},
                    {{ href: '/app/checkin', label: '🕐 Registrar Mi Asistencia' }},
                    {{ href: '/app/alarmas', label: '🔔 Alarm Troubleshooting' }},
                    {{ href: '/app/juegos', label: '🎮 Juegos' }},
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
                    {{ href: '/app/juegos', label: '🎮 Juegos' }},
                ];
                const techMenu = [
                    {{ href: '/app/mis-tareas', label: '🎯 Mis Tareas' }},
                    {{ href: '/app/solicitud', label: '🔔 Nueva Solicitud' }},
                    {{ href: '/app/mis-tickets', label: '🎫 Mis Tickets' }},
                    {{ href: '/app/checkin', label: '📍 Registrar Asistencia' }},
                    {{ href: '/app/juegos', label: '🎮 Juegos' }},
                ];
                const liderMenu = [
                    {{ href: '/app/dashboard', label: '📊 Dashboard Ejecutivo' }},
                    {{ href: '/app/asignaciones', label: '🎯 Control de Asignaciones' }},
                    {{ href: '/app/mis-tareas', label: '✅ Mis Tareas Asignadas' }},
                    {{ href: '/app/tickets', label: '🎫 Tickets' }},
                    {{ href: '/app/admin', label: '📸 Evidencias' }},
                    {{ href: '/app/checkin', label: '📍 Registrar Asistencia' }},
                    {{ href: '/app/juegos', label: '🎮 Juegos' }},
                ];
                const menu = window.role === 'admin' ? adminMenu
                    : (window.role === 'visor' ? visorMenu
                    : (window.role === 'lider' ? liderMenu : techMenu));
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

            // ── Búsqueda global (Ctrl+K) ─────────────────────────────────
            let _globalSearchDebounce = null;

            function abrirBusquedaGlobal() {{
                const overlay = document.getElementById('globalSearchOverlay');
                overlay.classList.add('open');
                const input = document.getElementById('globalSearchInput');
                input.value = '';
                document.getElementById('globalSearchResults').innerHTML = '';
                setTimeout(() => input.focus(), 30);
            }}

            function cerrarBusquedaGlobal() {{
                document.getElementById('globalSearchOverlay').classList.remove('open');
            }}

            function _onGlobalSearchInput() {{
                clearTimeout(_globalSearchDebounce);
                const q = document.getElementById('globalSearchInput').value.trim();
                const resultsEl = document.getElementById('globalSearchResults');
                if (q.length < 2) {{
                    resultsEl.innerHTML = q.length === 0 ? '' : '<p class="global-search-hint">Escribe al menos 2 letras…</p>';
                    return;
                }}
                _globalSearchDebounce = setTimeout(() => _ejecutarBusquedaGlobal(q), 250);
            }}

            async function _ejecutarBusquedaGlobal(q) {{
                const resultsEl = document.getElementById('globalSearchResults');
                resultsEl.innerHTML = '<p class="global-search-hint">Buscando…</p>';
                try {{
                    const res = await window.fetchAuth('/api/search/global?q=' + encodeURIComponent(q));
                    if (!res.ok) {{ resultsEl.innerHTML = '<p class="global-search-hint">Error al buscar.</p>'; return; }}
                    const data = await res.json();
                    const secciones = [
                        {{ key: 'unidades',   label: '📸 Unidades'   }},
                        {{ key: 'tickets',    label: '🎫 Tickets'    }},
                        {{ key: 'evidencias', label: '🖼 Evidencias' }},
                    ];
                    let html = '';
                    let total = 0;
                    secciones.forEach(sec => {{
                        const items = data[sec.key] || [];
                        if (!items.length) return;
                        total += items.length;
                        html += `<div class="global-search-section">${{sec.label}}</div>`;
                        items.forEach(item => {{
                            html += `<a class="global-search-item" href="${{item.url}}">
                                <span class="global-search-item-titulo">${{item.titulo}}</span>
                                <span class="global-search-item-sub">${{item.subtitulo || ''}}</span>
                            </a>`;
                        }});
                    }});
                    resultsEl.innerHTML = total ? html : '<p class="global-search-hint">Sin resultados para "' + q + '"</p>';
                }} catch (e) {{
                    resultsEl.innerHTML = '<p class="global-search-hint">Error al buscar.</p>';
                }}
            }}

            document.addEventListener('keydown', function(e) {{
                const isK = e.key === 'k' || e.key === 'K';
                if ((e.ctrlKey || e.metaKey) && isK) {{
                    e.preventDefault();
                    abrirBusquedaGlobal();
                }} else if (e.key === 'Escape') {{
                    cerrarBusquedaGlobal();
                }}
            }});

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
                actividad_pausada:    function(){{ _playTone([554,440],0.16,'triangle',0.3); }},
                actividad_completada: function(){{ _playTone([523,659,784,1047],0.12,'sine',0.4); }},
                ticket_nuevo:         function(){{ _playTone([330,262,220],0.2,'sawtooth',0.25); }},
                corriendo_6h:         function(){{ _playTone([880,660,880,660],0.16,'square',0.4); }},
                horario_actualizado:  function(){{ _playTone([587,740,880],0.14,'sine',0.32); }},
            }};
            const _LABELS = {{
                solicitud_nueva:      'Solicitud de actividad',
                asignacion_nueva:     'Actividad asignada',
                solicitud_aprobada:   'Solicitud aprobada',
                actividad_iniciada:   'Actividad iniciada',
                actividad_pausada:    'Actividad pausada',
                actividad_completada: 'Actividad completada',
                ticket_nuevo:         'Nuevo ticket creado',
                corriendo_6h:         'Unidad lleva 6 horas corriendo',
                horario_actualizado:  'Tu horario fue actualizado',
            }};
            const _ICONS = {{
                solicitud_nueva:'&#x1F4CB;', asignacion_nueva:'&#x2705;',
                solicitud_aprobada:'&#x1F44D;', actividad_iniciada:'&#x25B6;&#xFE0F;',
                actividad_pausada:'&#x23F8;&#xFE0F;',
                actividad_completada:'&#x1F3C1;', ticket_nuevo:'&#x1F3AB;',
                corriendo_6h:'&#x23F1;&#xFE0F;', horario_actualizado:'&#x1F4C5;',
            }};

            function _showToast(evType, payload) {{
                const label = _LABELS[evType] || evType;
                const icon  = _ICONS[evType]  || '';
                const t = document.createElement('div');
                t.style.cssText = 'position:fixed;bottom:24px;right:24px;background:#1F4E78;color:#fff;'
                    + 'padding:12px 18px;border-radius:10px;font-size:13px;font-family:Arial,sans-serif;'
                    + 'z-index:9999;box-shadow:0 4px 16px rgba(0,0,0,.35);max-width:280px;'
                    + 'line-height:1.4;opacity:0;transition:opacity .25s';
                var extra = (payload && (payload.unidad || payload.unit_number || payload.tecnico || payload.semana))
                    ? '<br><span style="opacity:.75;font-size:11px">'
                        + (payload.unidad || payload.unit_number || (payload.semana ? ('Semana del ' + payload.semana) : ''))
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
                            if (!d.type || d.type === 'status') return;

                            // "horario_actualizado" es dirigido: solo interesa a los
                            // técnicos afectados (payload.usernames) o al admin que lo
                            // guardó (para confirmar que la alerta salió).
                            if (d.type === 'horario_actualizado') {{
                                const usuariosAfectados = (d.payload && d.payload.usernames) || [];
                                const meAfecta = usuariosAfectados.indexOf(window.username) !== -1;
                                if (!meAfecta && window.role !== 'admin') return;
                                if (meAfecta) {{
                                    _SOUNDS[d.type] && _SOUNDS[d.type]();
                                    _showToast(d.type, {{ semana: d.payload.semana }});
                                    // Refrescar widgets de horario del técnico si están visibles
                                    if (typeof _ctCargarHorarioHoy === 'function') _ctCargarHorarioHoy();
                                    if (typeof _ctCargarHistorial === 'function') _ctCargarHistorial();
                                    if (typeof _ctCargarAlertaHorario === 'function') _ctCargarAlertaHorario();
                                }}
                                return;
                            }}

                            if (_SOUNDS[d.type]) {{
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
    <script> if (window.role !== 'admin' && window.role !== 'visor' && window.role !== 'lider') { window.location.href = '/app/mis-tareas'; } </script>
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
        .status-tbl .badge-corriendo {
            display:inline-flex; align-items:center; gap:4px;
            background:#eff6ff; color:#1d4ed8; border:1px solid #bfdbfe;
            border-radius:999px; padding:2px 9px; font-size:0.7rem;
            font-weight:700; white-space:nowrap; font-variant-numeric:tabular-nums;
        }
        .status-tbl .badge-corriendo.alerta6h {
            background:#fef2f2; color:#b91c1c; border-color:#fecaca;
            animation:pulse-badge 1.1s infinite;
        }
        .status-tbl .badge-corriendo.pausado {
            background:#f3f4f6; color:#4b5563; border-color:#d1d5db;
            animation:none;
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

        /* ── Pestañas estilo navegador (Dashboard / Schedule) ─────────────── */
        .browser-tabs { display:flex; align-items:flex-end; gap:4px; margin-bottom:0; padding-left:4px; }
        .browser-tab {
            display:flex; align-items:center; gap:8px; padding:11px 22px 10px;
            background:var(--bg-surface-2); color:var(--text-secondary); font-weight:600; font-size:0.85rem;
            border-radius:12px 12px 0 0; cursor:pointer; user-select:none; border:1px solid var(--border-color);
            border-bottom:none; position:relative; top:1px; transition:background 0.15s, color 0.15s;
        }
        .browser-tab:hover { background:var(--carrier-light); }
        .browser-tab.active { background:var(--bg-surface); color:var(--carrier-blue); box-shadow:0 -3px 10px var(--shadow-soft); }
        body.theme-dark .browser-tab.active { color:#cfe0ff; }
        .tab-panels-wrap { background:var(--bg-surface); border:1px solid var(--border-color); border-radius:0 12px 12px 12px; padding:22px; box-shadow:0 4px 12px var(--shadow-soft); }
        .tab-panel { display:none; }
        .tab-panel.active { display:block; }

        /* ── Grid editable de Schedule de Producción ──────────────────────── */
        .sched-toolbar { display:flex; align-items:center; gap:12px; flex-wrap:wrap; margin-bottom:16px; }
        .sched-toolbar select { width:auto; margin-bottom:0; min-width:170px; }
        .sched-toolbar .btn-primary, .sched-toolbar .btn-success, .sched-toolbar .btn-warning { width:auto; padding:11px 18px; font-size:0.85rem; }
        .sched-scroll { overflow:auto; border:1px solid var(--border-color); border-radius:10px; max-height:65vh; }
        #schedFullscreenWrap.sched-fullscreen-active .sched-scroll { max-height:none; }
        table.sched-tbl { border-collapse:separate; border-spacing:0; font-size:0.74rem; min-width:1400px; background:var(--bg-surface); table-layout:fixed; }
        table.sched-tbl th, table.sched-tbl td { border-right:1px solid var(--border-color-soft); border-bottom:1px solid var(--border-color-soft); padding:0; white-space:nowrap; overflow:hidden; }
        table.sched-tbl thead th { background:var(--carrier-blue); color:white; padding:8px 6px; font-weight:700; text-align:center; position:sticky; top:0; z-index:2; }
        body.theme-dark table.sched-tbl thead th { background:#0a1830; }
        table.sched-tbl thead th.weekend-hdr { background:#111827; }
        table.sched-tbl td.weekend-cell { background:#111827; }
        table.sched-tbl td.sticky-col, table.sched-tbl th.sticky-col { position:sticky; left:0; z-index:1; background:var(--bg-surface); }
        table.sched-tbl th.sticky-col { z-index:3; }
        table.sched-tbl .cell-input { width:100%; height:100%; border:none; border-radius:0; margin:0; padding:6px 8px; font-size:0.74rem; background:transparent; color:var(--text-primary); box-sizing:border-box; }
        table.sched-tbl .cell-input:focus { outline:2px solid var(--carrier-accent); outline-offset:-2px; box-shadow:none; }
        table.sched-tbl .day-input { text-align:center; padding:6px 2px; }
        table.sched-tbl .qty-input { text-align:center; }
        table.sched-tbl .col-resizer { position:absolute; right:0; top:0; bottom:0; width:6px; cursor:col-resize; z-index:4; }
        table.sched-tbl .col-resizer:hover, table.sched-tbl .col-resizer.resizing { background:rgba(255,255,255,0.35); }

        /* ── Ver tabla completa (pantalla ampliada) ───────────────────────── */
        #schedFullscreenWrap.sched-fullscreen-active {
            position:fixed; inset:0; z-index:5000; background:var(--bg-surface);
            padding:18px; margin:0; display:flex; flex-direction:column; border-radius:0;
        }
        #schedFullscreenWrap.sched-fullscreen-active .sched-scroll { flex:1; }
        .sched-fs-btn { margin-left:auto; }
        table.sched-tbl .model-input { }
        table.sched-tbl .owner-input { color:var(--carrier-blue); font-weight:700; }
        body.theme-dark table.sched-tbl .owner-input { color:#5b9bf0; }
        table.sched-tbl .notes-input { background:#fdebd3; }
        body.theme-dark table.sched-tbl .notes-input { background:#3a2c15; }
        table.sched-tbl .lote-input { text-align:center; font-weight:700; color:var(--carrier-success); }
        table.sched-tbl .lote-input.mismatch { color:var(--carrier-warn); }
        table.sched-tbl .del-row-btn { background:none; border:none; color:var(--carrier-danger); cursor:pointer; font-size:0.95rem; padding:6px; }
        table.sched-tbl .del-row-btn:hover { opacity:0.7; }
        .sched-total-row td { background:var(--bg-surface-2); font-weight:700; }
    </style>

    <div class="browser-tabs">
        <div class="browser-tab active" id="tabBtnDashboard" onclick="cambiarTabDashboard('dashboard')">📊 Dashboard</div>
        <div class="browser-tab" id="tabBtnSchedule" onclick="cambiarTabDashboard('schedule')">🗓️ Schedule</div>
        <div class="browser-tab admin-only" id="tabBtnKpiTecnico" onclick="cambiarTabDashboard('kpitecnico')">👷 KPIs Técnico</div>
    </div>
    <div class="tab-panels-wrap">
    <div class="tab-panel active" id="tabPanelDashboard">

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

    <div class="section-title" style="display:flex;align-items:center;justify-content:space-between;gap:12px;flex-wrap:wrap;">
        <span>📋 Estatus de Proceso por Unidad</span>
        <button class="btn-primary admin-only" style="width:auto;padding:8px 16px;font-size:.82rem;" onclick="abrirModalColumnas()">⚙️ Gestionar columnas</button>
    </div>
    <div id="statusTable" style="overflow-x:auto; margin-bottom:32px; border-radius:12px;"></div>

    <!-- Modal: Gestionar columnas ocultas del dashboard -->
    <div id="columnas-modal" style="display:none;position:fixed;inset:0;background:rgba(0,0,0,.5);z-index:2000;align-items:center;justify-content:center;">
        <div style="background:white;border-radius:12px;max-width:420px;width:92%;max-height:80vh;overflow-y:auto;padding:24px;">
            <h3 style="margin-top:0;color:var(--carrier-blue);">⚙️ Columnas del dashboard</h3>
            <p style="color:var(--text-secondary);font-size:.85rem;">Desmarca una actividad para ocultarla de la tabla. Puedes volver a mostrarla cuando quieras.</p>
            <div id="columnas-modal-body" style="display:flex;flex-direction:column;gap:8px;margin:16px 0;"></div>
            <button class="btn-primary" style="width:100%;" onclick="document.getElementById('columnas-modal').style.display='none'">Cerrar</button>
        </div>
    </div>

    <div class="section-title">📦 Lotes y Series por Unidad</div>
    <div id="lotesContainer" style="margin-bottom:32px;"></div>

    <div class="section-title admin-only">📂 Descarga de Evidencias</div>
    <div class="admin-only" style="display:flex; gap:16px; align-items:center; margin-bottom:16px; flex-wrap:wrap;">
        <select id="unidadEv" style="width:auto; flex:1; margin-bottom:0;"><option value="">Selecciona unidad</option></select>
        <button class="btn-primary" style="width:auto; padding:12px 24px;" onclick="descargarEvidencias()">📥 Descargar ZIP</button>
    </div>

    <div class="section-title admin-only">📥 Reportes</div>
    <button class="btn-primary admin-only" style="width:auto; padding:12px 28px;" onclick="descargarReporte()">📊 Descargar Reporte Maestro Excel</button>

    </div><!-- /tabPanelDashboard -->

    <div class="tab-panel" id="tabPanelSchedule">
      <datalist id="schedLotesDatalist"></datalist>
      <div id="schedFullscreenWrap">
        <div class="sched-toolbar">
            <select id="schedMesSelect" onchange="cambiarMesSchedule()"></select>
            <button class="btn-primary admin-only" onclick="nuevoMesSchedule()">🗓️ Nuevo mes</button>
            <button class="btn-success admin-only" onclick="agregarFilaSchedule()">➕ Agregar línea</button>
            <button class="btn-primary admin-only" id="schedSeleccionarBtn" onclick="schedToggleSeleccion()">☑️ Seleccionar filas</button>
            <button class="btn-primary admin-only" id="schedMostrarOcultosBtn" onclick="schedToggleMostrarOcultos()">👁️ Mostrar ocultos</button>
            <span id="schedGuardando" style="font-size:0.78rem;color:var(--text-secondary);"></span>
            <button class="btn-primary sched-fs-btn" id="schedFsBtn" onclick="toggleSchedFullscreen()">⛶ Ver tabla completa</button>
        </div>
        <div class="sched-toolbar admin-only" id="schedAccionesBarra" style="display:none;">
            <span id="schedSeleccionCount" style="font-weight:600;"></span>
            <button class="btn-warning" onclick="schedOcultarSeleccionadas()">🙈 Ocultar seleccionadas</button>
            <button class="btn-success" onclick="schedAbrirModalReporte()">🖨️ Generar reporte</button>
        </div>
        <div class="sched-scroll">
            <table class="sched-tbl" id="schedTabla">
                <colgroup id="schedColgroup"></colgroup>
                <thead><tr id="schedTheadRow"></tr></thead>
                <tbody id="schedTbody"></tbody>
            </table>
        </div>
      </div>
    </div><!-- /tabPanelSchedule -->

    <div class="tab-panel" id="tabPanelKpiTecnico">
        <div style="display:flex; align-items:center; gap:14px; flex-wrap:wrap; margin-bottom:20px;">
            <label style="margin:0; font-size:0.85rem; color:var(--text-secondary);">Ventana de tiempo:</label>
            <select id="kpiTecnicoDias" style="width:auto; margin-bottom:0;" onchange="cargarKpisTecnico()">
                <option value="7">Últimos 7 días</option>
                <option value="30" selected>Últimos 30 días</option>
                <option value="90">Últimos 90 días</option>
            </select>
        </div>
        <div id="kpiTecnicoTabla" style="overflow-x:auto;">
            <p style="color:var(--text-secondary);">Cargando…</p>
        </div>
    </div><!-- /tabPanelKpiTecnico -->

    <!-- Modal: Generar reporte de unidades seleccionadas -->
    <div id="sched-reporte-modal" style="display:none;position:fixed;inset:0;background:rgba(0,0,0,.5);z-index:2000;align-items:center;justify-content:center;">
        <div style="background:white;border-radius:12px;max-width:640px;width:92%;max-height:80vh;overflow-y:auto;padding:24px;">
            <h3 style="margin-top:0;">🖨️ Generar reporte de series</h3>
            <p style="color:var(--text-secondary);font-size:.88rem;">Selecciona qué unidades incluir en el Excel. Por defecto están todas marcadas.</p>
            <div id="sched-reporte-modal-body"></div>
            <div style="display:flex;gap:10px;margin-top:16px;">
                <button class="btn-success" onclick="schedConfirmarGenerarReporte()">⬇️ Descargar Excel</button>
                <button class="btn-primary" onclick="document.getElementById('sched-reporte-modal').style.display='none'">Cancelar</button>
            </div>
        </div>
    </div>


    </div><!-- /tab-panels-wrap -->

    <script>
        const actividades = ['Cableado','Programación','Soldadura','Check de fugas','Vacío','Cerrado','Pre-viaje','Horas Corridas','Standby','GPS','Corriendo','Inspección','Accesorios','Toma de Valores','Evidencia','Toma de Series','Extra Eléctrico','Extra Soldador'];
        const camposSeries = {vin_number:'VIN Number',reefer_serial:'Serie Reefer',reefer_model:'Modelo Reefer',evaporator_model_1:'Evap. 1 Modelo',evaporator_serial_mjs11:'Evap. 1 Serie',evaporator_model_2:'Evap. 2 Modelo',evaporator_serial_mjd22:'Evap. 2 Serie',engine_serial:'Motor',compressor_serial:'Compresor',generator_serial:'Generador',battery_charger_serial:'Cargador Bat.'};

        // ── Contador en vivo de horas 'Corriendo' (se refresca cada segundo) ──
        // Usa segundos ya acumulados (persisten a través de pausas) + el tiempo
        // transcurrido desde el último arranque, si la unidad sigue corriendo.
        let _contadorCorriendoInterval = null;
        function _fmtDuracionCorriendo(ms) {
            if (ms < 0) ms = 0;
            const totalSec = Math.floor(ms / 1000);
            const h = Math.floor(totalSec / 3600);
            const m = Math.floor((totalSec % 3600) / 60);
            const s = totalSec % 60;
            const pad = n => String(n).padStart(2, '0');
            return `${pad(h)}:${pad(m)}:${pad(s)}`;
        }
        function _tickContadoresCorriendo() {
            const nodos = document.querySelectorAll('.badge-corriendo[data-acumulado]');
            const ahora = Date.now();
            nodos.forEach(el => {
                const acumuladoSeg = parseInt(el.getAttribute('data-acumulado'), 10) || 0;
                const desdeStr = el.getAttribute('data-desde');
                let ms = acumuladoSeg * 1000;
                const corriendo = !!desdeStr;
                if (corriendo) {
                    const desde = new Date(desdeStr.replace(' ', 'T')).getTime();
                    if (!isNaN(desde)) ms += Math.max(0, ahora - desde);
                }
                if (corriendo) {
                    el.textContent = '⏱ ' + _fmtDuracionCorriendo(ms);
                    el.classList.remove('pausado');
                } else {
                    el.textContent = '⏸ ' + _fmtDuracionCorriendo(ms);
                    el.classList.add('pausado');
                }
                if ((ms / 3600000) >= 6) {
                    el.classList.add('alerta6h');
                    el.title = corriendo ? 'Lleva 6+ horas corriendo' : 'Pausada — ya acumuló 6+ horas';
                } else {
                    el.classList.remove('alerta6h');
                    el.title = corriendo ? 'Corriendo' : 'Pausada — tiempo acumulado guardado';
                }
            });
        }
        function _iniciarContadoresCorriendo() {
            _tickContadoresCorriendo();
            if (_contadorCorriendoInterval) clearInterval(_contadorCorriendoInterval);
            _contadorCorriendoInterval = setInterval(_tickContadoresCorriendo, 1000);
        }

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
                const tecSet = new Set(usuariosAll.filter(u => u.role === 'tecnico' || u.role === 'lider').map(u => u.username));
                const stats = statsRaw.filter(s => tecSet.has(s.tecnico));

                if (stats.length > 0) {
                    Plotly.newPlot('barChart', [
                        {x: stats.map(s=>s.tecnico_display||s.tecnico), y: stats.map(s=>s.completadas), type:'bar', name:'Completadas', marker:{color:'#16a34a'}},
                        {x: stats.map(s=>s.tecnico_display||s.tecnico), y: stats.map(s=>s.en_curso),    type:'bar', name:'En Curso',    marker:{color:'#d97706'}},
                        {x: stats.map(s=>s.tecnico_display||s.tecnico), y: stats.map(s=>s.pendientes),  type:'bar', name:'Pendientes',  marker:{color:'#dc2626'}},
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
                        // Actividades ocultas del dashboard (solo afecta esta tabla, no los
                        // selects de asignación de actividades en otras pestañas)
                        let actividadesOcultas = [];
                        try {
                            const ocRes = await fetchAuth('/api/dashboard/actividades_ocultas');
                            if (ocRes.ok) actividadesOcultas = await ocRes.json();
                        } catch(e) { console.warn('No se pudo cargar actividades_ocultas:', e); }
                        window._actividadesOcultas = actividadesOcultas;
                        const actividadesVisibles = actividades.filter(a => !actividadesOcultas.includes(a));

                        // Tabla de estatus – CSS correcta
                        const compSet    = new Set(asignaciones.filter(a=>a.estado==='completada').map(a=>a.unidad+'||'+a.actividad_id));
                        const procesoSet = new Set(asignaciones.filter(a=>a.estado==='en_proceso').map(a=>a.unidad+'||'+a.actividad_id));
                        const pendSet    = new Set(asignaciones.filter(a=>a.estado==='pendiente').map(a=>a.unidad+'||'+a.actividad_id));

                        // Contador acumulado de horas 'Corriendo' por unidad (persiste a través de pausas)
                        let corriendoTrack = {};
                        try {
                            const ctRes = await fetchAuth('/api/dashboard/corriendo_tracking');
                            if (ctRes.ok) {
                                const ctRows = await ctRes.json();
                                ctRows.forEach(r => { corriendoTrack[r.unidad] = r; });
                            }
                        } catch(e) { console.warn('No se pudo cargar corriendo_tracking:', e); }

                        let tbl = '<table class="status-tbl"><thead><tr><th>LOTE</th><th>#Económico</th>';
                        actividadesVisibles.forEach(a => { tbl += `<th>${a}</th>`; });
                        tbl += '<th>📝 Comentario</th></tr></thead><tbody>';
                        unidades.forEach(u => {
                            tbl += `<tr><td>${u.id_lote||''}</td><td>${u.unit_number}</td>`;
                            actividadesVisibles.forEach(act => {
                                const key = u.unit_number+'||'+act;
                                const track = act === 'Corriendo' ? corriendoTrack[u.unit_number] : null;
                                if (act === 'Corriendo' && track && (track.corriendo_desde || track.segundos_acumulados > 0)) {
                                    // Contador en vivo/pausado de horas corriendo (persiste tiempo acumulado)
                                    const desdeAttr = track.corriendo_desde ? ` data-desde="${track.corriendo_desde}"` : '';
                                    tbl += `<td><span class="badge-corriendo" data-acumulado="${track.segundos_acumulados||0}"${desdeAttr}>⏱ --:--:--</span></td>`;
                                } else if (compSet.has(key)) {
                                    tbl += '<td><span class="check">✔</span></td>';
                                } else if (procesoSet.has(key)) {
                                    tbl += '<td><span class="badge-proceso" title="En proceso">⚙ En proceso</span></td>';
                                } else if (pendSet.has(key)) {
                                    tbl += '<td><span class="badge-pendiente" title="Pendiente">⏳</span></td>';
                                } else {
                                    tbl += '<td><span class="dash">—</span></td>';
                                }
                            });
                            const comentarioEsc = (u.comentario||'').replace(/"/g,'&quot;');
                            if (window.role === 'admin') {
                                tbl += `<td style="min-width:180px;"><input type="text" class="comentario-unidad-input" data-unidad="${u.unit_number}" data-valor-guardado="${comentarioEsc}" value="${comentarioEsc}" placeholder="Sin comentario" onblur="guardarComentarioUnidad(this)" style="width:100%;border:1px solid #d8dee6;border-radius:6px;padding:6px 8px;font-size:.82rem;"></td>`;
                            } else {
                                tbl += `<td style="min-width:150px;font-size:.82rem;color:var(--text-secondary);">${u.comentario||'—'}</td>`;
                            }
                            tbl += '</tr>';
                        });
                        tbl += '</tbody></table>';
                        document.getElementById('statusTable').innerHTML = tbl;
                        _iniciarContadoresCorriendo();

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

        // ── Comentario libre por unidad (editable solo por admin) ─────────────
        async function guardarComentarioUnidad(input) {
            const unidad = input.dataset.unidad;
            const valorPrevio = input.dataset.valorGuardado !== undefined ? input.dataset.valorGuardado : input.value;
            const comentario = input.value;
            if (comentario === valorPrevio) return; // sin cambios, no llamar al servidor
            try {
                const res = await fetchAuth(`/api/unidades/${encodeURIComponent(unidad)}/comentario`, {
                    method: 'PATCH',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ comentario })
                });
                if (res.ok) {
                    input.dataset.valorGuardado = comentario;
                    input.style.borderColor = '#16a34a';
                    setTimeout(() => { input.style.borderColor = '#d8dee6'; }, 800);
                } else {
                    input.style.borderColor = '#dc2626';
                }
            } catch(e) {
                console.error('guardarComentarioUnidad', e);
                input.style.borderColor = '#dc2626';
            }
        }

        // ── Gestionar columnas (actividades) ocultas del dashboard ────────────
        async function abrirModalColumnas() {
            const body = document.getElementById('columnas-modal-body');
            body.innerHTML = 'Cargando...';
            document.getElementById('columnas-modal').style.display = 'flex';
            let ocultas = window._actividadesOcultas || [];
            try {
                const res = await fetchAuth('/api/dashboard/actividades_ocultas');
                if (res.ok) ocultas = await res.json();
            } catch(e) { console.warn('abrirModalColumnas', e); }
            body.innerHTML = actividades.map(a => `
                <label style="display:flex;align-items:center;gap:8px;font-size:.88rem;cursor:pointer;">
                    <input type="checkbox" ${ocultas.includes(a) ? '' : 'checked'} onchange="toggleColumnaActividad('${a.replace(/'/g,"\\'")}', this.checked)">
                    ${a}
                </label>
            `).join('');
        }

        async function toggleColumnaActividad(actividad, mostrar) {
            try {
                const url = `/api/dashboard/actividades_ocultas/${encodeURIComponent(actividad)}`;
                await fetchAuth(url, { method: mostrar ? 'DELETE' : 'POST' });
                await cargarDashboard();
            } catch(e) {
                console.error('toggleColumnaActividad', e);
                alert('No se pudo actualizar la columna. Intenta de nuevo.');
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

        // ══════════════════════════════════════════════════════════════════
        // ── Pestañas Dashboard / Schedule ────────────────────────────────
        // ══════════════════════════════════════════════════════════════════
        let schedCargado = false;
        function cambiarTabDashboard(tab) {
            document.getElementById('tabBtnDashboard').classList.toggle('active', tab === 'dashboard');
            document.getElementById('tabBtnSchedule').classList.toggle('active', tab === 'schedule');
            document.getElementById('tabBtnKpiTecnico').classList.toggle('active', tab === 'kpitecnico');
            document.getElementById('tabPanelDashboard').classList.toggle('active', tab === 'dashboard');
            document.getElementById('tabPanelSchedule').classList.toggle('active', tab === 'schedule');
            document.getElementById('tabPanelKpiTecnico').classList.toggle('active', tab === 'kpitecnico');
            if (tab === 'schedule' && !schedCargado) {
                schedCargado = true;
                initSchedule();
            }
            if (tab === 'kpitecnico') {
                cargarKpisTecnico();
            }
        }

        // ══════════════════════════════════════════════════════════════════
        // ── KPIs por técnico (tickets + asistencia) ──────────────────────
        // ══════════════════════════════════════════════════════════════════
        async function cargarKpisTecnico() {
            const cont = document.getElementById('kpiTecnicoTabla');
            const dias = document.getElementById('kpiTecnicoDias').value;
            cont.innerHTML = '<p style="color:var(--text-secondary);">Cargando…</p>';
            try {
                const res = await window.fetchAuth('/api/dashboard/kpis_tecnico?dias=' + dias);
                if (res.status === 403) {
                    cont.innerHTML = '<p style="color:var(--text-secondary);">Solo administradores y líderes pueden ver esta vista.</p>';
                    return;
                }
                if (!res.ok) { cont.innerHTML = '<p style="color:var(--carrier-danger);">Error al cargar los KPIs.</p>'; return; }
                const data = await res.json();
                if (!data.tecnicos.length) {
                    cont.innerHTML = '<p style="color:var(--text-secondary);">Sin datos en esta ventana de tiempo.</p>';
                    return;
                }
                let html = '<table class="status-tbl"><thead><tr>' +
                    '<th>Técnico</th><th>Tickets cerrados</th><th>Con reporte</th><th>Sin reporte</th>' +
                    '<th>Hrs. promedio resolución</th><th>Días con check-in</th><th>Días con tardanza</th>' +
                    '<th>% tardanza</th></tr></thead><tbody>';
                data.tecnicos.forEach(t => {
                    const pctTardanza = t.pct_tardanza;
                    const colorPct = pctTardanza === null ? '' :
                        (pctTardanza >= 30 ? 'color:var(--carrier-danger);font-weight:700;' :
                         pctTardanza >= 10 ? 'color:var(--carrier-warn);font-weight:700;' : 'color:var(--carrier-success);font-weight:700;');
                    html += `<tr>
                        <td style="text-align:left;font-weight:700;">${t.tecnico_display}</td>
                        <td>${t.tickets_cerrados}</td>
                        <td>${t.con_reporte_adjunto ?? '—'}</td>
                        <td>${t.sin_reporte_adjunto ?? '—'}</td>
                        <td>${t.horas_promedio_resolucion !== null ? t.horas_promedio_resolucion + 'h' : '—'}</td>
                        <td>${t.dias_con_checkin ?? '—'}</td>
                        <td>${t.dias_con_tardanza ?? '—'}</td>
                        <td style="${colorPct}">${pctTardanza !== null ? pctTardanza + '%' : '—'}</td>
                    </tr>`;
                });
                html += '</tbody></table>';
                cont.innerHTML = html;
            } catch (e) {
                cont.innerHTML = '<p style="color:var(--carrier-danger);">Error al cargar los KPIs.</p>';
            }
        }

        // ══════════════════════════════════════════════════════════════════
        // ── Schedule de Producción (grid editable estilo Excel) ─────────
        // ══════════════════════════════════════════════════════════════════
        let schedFilas = [];
        let schedMesActual = null;
        let schedModoSeleccion = false;
        let schedSeleccionadas = new Set();
        let schedMostrarOcultos = false;
        let schedUnidadesTodas = [];

        // Normaliza un id_lote para comparar sin que espacios, mayúsculas o
        // símbolos (guiones, puntos) causen falsos negativos de coincidencia.
        function schedNormLote(s) {
            return (s || '').toString().trim().toUpperCase().replace(/[^A-Z0-9]/g, '');
        }
        function schedUnidadesDeLote(idLote) {
            const norm = schedNormLote(idLote);
            if (!norm) return [];
            return schedUnidadesTodas.filter(u => schedNormLote(u.id_lote) === norm);
        }
        async function schedCargarUnidadesCache() {
            try {
                const res = await fetchAuth('/api/unidades/?incluir_ocultas=true');
                schedUnidadesTodas = await res.json();
            } catch (e) {
                schedUnidadesTodas = [];
            }
            schedActualizarDatalistLotes();
        }
        function schedActualizarDatalistLotes() {
            const dl = document.getElementById('schedLotesDatalist');
            if (!dl) return;
            const lotesReales = [...new Set(schedUnidadesTodas.map(u => u.id_lote).filter(Boolean))].sort();
            dl.innerHTML = lotesReales.map(l => `<option value="${l.replace(/"/g, '&quot;')}">`).join('');
        }
        const MESES_ES = ['ENE','FEB','MAR','ABR','MAY','JUN','JUL','AGO','SEP','OCT','NOV','DIC'];
        const SCHED_COL_DEFAULTS = {
            line:60, owner:190, size:64, tipo:96, brand:110, notes:170, qty:60, liberadas:110, lote:85
        };
        let schedColWidths = {};
        try {
            schedColWidths = JSON.parse(localStorage.getItem('sched_col_widths_v1') || '{}');
        } catch (e) { schedColWidths = {}; }

        function schedAnchoCol(key) {
            return schedColWidths[key] || SCHED_COL_DEFAULTS[key] || 36;
        }
        function schedGuardarAnchos() {
            try { localStorage.setItem('sched_col_widths_v1', JSON.stringify(schedColWidths)); } catch (e) {}
        }

        function toggleSchedFullscreen() {
            const wrap = document.getElementById('schedFullscreenWrap');
            const activo = wrap.classList.toggle('sched-fullscreen-active');
            document.getElementById('schedFsBtn').textContent = activo ? '✕ Cerrar pantalla completa' : '⛶ Ver tabla completa';
            document.body.style.overflow = activo ? 'hidden' : '';
        }
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                const wrap = document.getElementById('schedFullscreenWrap');
                if (wrap && wrap.classList.contains('sched-fullscreen-active')) toggleSchedFullscreen();
            }
        });

        let schedResizeState = null;
        function schedIniciarResize(e, key) {
            e.preventDefault();
            schedResizeState = { key, startX: e.clientX, startWidth: schedAnchoCol(key), el: e.target };
            e.target.classList.add('resizing');
            document.addEventListener('mousemove', schedDurranteResize);
            document.addEventListener('mouseup', schedFinResize);
        }
        function schedDurranteResize(e) {
            if (!schedResizeState) return;
            const delta = e.clientX - schedResizeState.startX;
            const nuevo = Math.max(28, schedResizeState.startWidth + delta);
            schedColWidths[schedResizeState.key] = nuevo;
            const col = document.querySelector('#schedColgroup col[data-col="' + schedResizeState.key + '"]');
            if (col) col.style.width = nuevo + 'px';
        }
        function schedFinResize() {
            if (schedResizeState && schedResizeState.el) schedResizeState.el.classList.remove('resizing');
            schedResizeState = null;
            schedGuardarAnchos();
            document.removeEventListener('mousemove', schedDurranteResize);
            document.removeEventListener('mouseup', schedFinResize);
        }
        function schedTh(key, label, extraClass) {
            return `<th class="${extraClass || ''}" data-col="${key}">${label}<div class="col-resizer" onmousedown="schedIniciarResize(event,'${key}')"></div></th>`;
        }

        function schedNombreMes(mesAnio) {
            const [y, m] = mesAnio.split('-').map(Number);
            return MESES_ES[m - 1] + ' ' + y;
        }
        function schedDiasDelMes(mesAnio) {
            const [y, m] = mesAnio.split('-').map(Number);
            return new Date(y, m, 0).getDate();
        }
        function schedEsFinDeSemana(mesAnio, dia) {
            const [y, m] = mesAnio.split('-').map(Number);
            const dow = new Date(y, m - 1, dia).getDay();
            return dow === 0 || dow === 6;
        }

        async function initSchedule() {
            try {
                const res = await fetchAuth('/api/schedule/meses');
                let meses = await res.json();
                if (!meses.length) {
                    const hoy = new Date();
                    meses = [hoy.getFullYear() + '-' + String(hoy.getMonth() + 1).padStart(2, '0')];
                }
                const sel = document.getElementById('schedMesSelect');
                sel.innerHTML = meses.map(m => `<option value="${m}">${schedNombreMes(m)}</option>`).join('');
                schedMesActual = meses[0];
                sel.value = schedMesActual;
                await cambiarMesSchedule();
            } catch (err) {
                console.error('Schedule init error:', err);
            }
        }

        async function cambiarMesSchedule() {
            const sel = document.getElementById('schedMesSelect');
            schedMesActual = sel.value;
            document.getElementById('schedGuardando').textContent = 'Cargando...';
            try {
                const [res] = await Promise.all([
                    fetchAuth('/api/schedule/?mes_anio=' + encodeURIComponent(schedMesActual)),
                    schedCargarUnidadesCache()
                ]);
                schedFilas = await res.json();
            } catch (err) {
                schedFilas = [];
            }
            document.getElementById('schedGuardando').textContent = '';
            renderScheduleTabla();
        }

        function nuevoMesSchedule() {
            const mesTxt = prompt('Nuevo mes (formato: MM-AAAA), ej. 08-2026:');
            if (!mesTxt) return;
            const partes = mesTxt.trim().split('-');
            if (partes.length !== 2 || isNaN(partes[0]) || isNaN(partes[1])) {
                alert('Formato inválido. Usa MM-AAAA, ej. 08-2026');
                return;
            }
            const mm = String(parseInt(partes[0])).padStart(2, '0');
            const yyyy = partes[1];
            const mesAnio = yyyy + '-' + mm;
            const sel = document.getElementById('schedMesSelect');
            if (![...sel.options].some(o => o.value === mesAnio)) {
                const opt = document.createElement('option');
                opt.value = mesAnio; opt.textContent = schedNombreMes(mesAnio);
                sel.insertBefore(opt, sel.firstChild);
            }
            sel.value = mesAnio;
            schedMesActual = mesAnio;
            schedFilas = [];
            renderScheduleTabla();
        }

        function renderScheduleTabla() {
            if (!schedMesActual) return;
            const numDias = schedDiasDelMes(schedMesActual);
            const chkWidth = schedModoSeleccion ? 34 : 0;
            const ownerLeft = schedAnchoCol('line') + chkWidth;

            // ── Colgroup (anchos de columnas, editables por arrastre) ──
            let colgroup = '';
            if (schedModoSeleccion) colgroup += `<col style="width:34px;">`;
            colgroup += `
                <col data-col="line" style="width:${schedAnchoCol('line')}px;">
                <col data-col="owner" style="width:${schedAnchoCol('owner')}px;">
                <col data-col="size" style="width:${schedAnchoCol('size')}px;">
                <col data-col="tipo" style="width:${schedAnchoCol('tipo')}px;">
                <col data-col="brand" style="width:${schedAnchoCol('brand')}px;">
                <col data-col="notes" style="width:${schedAnchoCol('notes')}px;">
                <col data-col="qty" style="width:${schedAnchoCol('qty')}px;">
                <col data-col="liberadas" style="width:${schedAnchoCol('liberadas')}px;">
                <col data-col="lote" style="width:${schedAnchoCol('lote')}px;">
            `;
            for (let d = 1; d <= numDias; d++) {
                colgroup += `<col data-col="day_${d}" style="width:${schedAnchoCol('day_' + d)}px;">`;
            }
            colgroup += `<col style="width:40px;">`;
            document.getElementById('schedColgroup').innerHTML = colgroup;

            // ── Encabezado ──
            let thead = '';
            if (schedModoSeleccion) {
                thead += `<th class="sticky-col"><input type="checkbox" id="schedCheckTodos" onchange="schedSeleccionarTodos(this.checked)"></th>`;
            }
            thead += schedTh('line', 'LINE', 'sticky-col').replace('<th class="sticky-col"', `<th class="sticky-col" style="left:${chkWidth}px;"`);
            thead += schedTh('owner', 'OWNER', 'sticky-col').replace('<th class="sticky-col"', `<th class="sticky-col" style="left:${ownerLeft}px;"`);
            thead += schedTh('size', 'SIZE');
            thead += schedTh('tipo', 'TYPE');
            thead += schedTh('brand', 'Reefer/Heated Unit Brand');
            thead += schedTh('notes', 'Notes or Evaps');
            thead += schedTh('qty', "Q'TY");
            thead += schedTh('liberadas', 'UNIDADES LIBERADAS');
            thead += schedTh('lote', 'LOTE');
            for (let d = 1; d <= numDias; d++) {
                const wknd = schedEsFinDeSemana(schedMesActual, d) ? ' weekend-hdr' : '';
                thead += schedTh('day_' + d, d, wknd);
            }
            thead += `<th></th>`;
            document.getElementById('schedTheadRow').innerHTML = thead;

            // ── Filtrado de filas ocultas ──
            const filasVisibles = schedFilas.filter(f => schedMostrarOcultos || !f.oculto);
            const numColsBase = schedModoSeleccion ? 11 : 10;

            // ── Cuerpo ──
            if (!filasVisibles.length) {
                document.getElementById('schedTbody').innerHTML =
                    `<tr><td colspan="${numColsBase + numDias}" style="text-align:center;padding:24px;color:var(--text-secondary);">
                        ${schedFilas.length ? 'Sin líneas visibles (todas ocultas). Usa "👁️ Mostrar ocultos" para verlas.' : `Sin líneas registradas para ${schedNombreMes(schedMesActual)}. Usa "➕ Agregar línea" para comenzar.`}
                    </td></tr>`;
                return;
            }

            let body = '';
            filasVisibles.forEach(f => {
                const dias = f.dias || {};
                let sumaDias = 0;
                Object.values(dias).forEach(v => { sumaDias += (parseInt(v) || 0); });
                const qty = parseInt(f.qty) || 0;
                const coincide = qty > 0 && sumaDias === qty;
                const loteValor = f.lote || '';
                const loteClass = 'cell-input lote-input' + (qty > 0 && !coincide ? ' mismatch' : '');
                const loteUnidadesRow = schedUnidadesDeLote(loteValor);
                const loteSinCoincidencia = loteValor.trim() !== '' && loteUnidadesRow.length === 0 && schedUnidadesTodas.length > 0;
                const loteModelosRow = [...new Set(loteUnidadesRow.map(u => u.reefer_model).filter(Boolean))];
                const loteModeloHtml = loteModelosRow.length
                    ? `<div style="font-size:.68rem;color:var(--text-secondary);line-height:1.15;margin-top:2px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;" title="${loteModelosRow.join(', ').replace(/"/g, '&quot;')}">${loteModelosRow.join(', ')}</div>`
                    : (loteSinCoincidencia ? `<div style="font-size:.68rem;color:var(--carrier-warn);line-height:1.15;margin-top:2px;" title="Este lote no existe en la tabla de unidades. Revisa si hay un error de captura.">⚠ sin unidades</div>` : '');
                const liberadasColor = qty > 0 ? (coincide ? '#16a34a' : '#d97706') : 'var(--text-secondary)';
                const filaOcultaStyle = f.oculto ? ' style="opacity:.55;"' : '';
                const badgeOculto = f.oculto ? ` <span title="Lote oculto" style="font-size:.7rem;background:#fde68a;color:#7d6608;padding:1px 5px;border-radius:6px;">🙈 oculto</span>` : '';
                const checkboxCell = schedModoSeleccion
                    ? `<td class="sticky-col"><input type="checkbox" class="sched-row-check" data-fila-id="${f.id}" ${schedSeleccionadas.has(f.id) ? 'checked' : ''} onchange="schedToggleFila(${f.id}, this.checked)"></td>`
                    : '';

                body += `<tr data-fila-id="${f.id}"${filaOcultaStyle}>
                    ${checkboxCell}
                    <td class="sticky-col" style="left:${chkWidth}px;">
                        <input class="cell-input" value="${f.linea || ''}" onchange="schedGuardarCampo(${f.id},'linea',this.value)">
                    </td>
                    <td class="sticky-col" style="left:${ownerLeft}px;">
                        <input class="cell-input owner-input" value="${(f.owner || '').replace(/"/g, '&quot;')}" onchange="schedGuardarCampo(${f.id},'owner',this.value)">
                    </td>
                    <td><input class="cell-input" value="${f.size || ''}" onchange="schedGuardarCampo(${f.id},'size',this.value)"></td>
                    <td><input class="cell-input" value="${f.tipo || ''}" onchange="schedGuardarCampo(${f.id},'tipo',this.value)"></td>
                    <td><input class="cell-input" value="${f.reefer_brand || ''}" onchange="schedGuardarCampo(${f.id},'reefer_brand',this.value)"></td>
                    <td><input class="cell-input notes-input" value="${(f.notas_evaps || '').replace(/"/g, '&quot;')}" onchange="schedGuardarCampo(${f.id},'notas_evaps',this.value)"></td>
                    <td><input type="number" class="cell-input qty-input" value="${qty || ''}" onchange="schedGuardarCampo(${f.id},'qty',this.value)"></td>
                    <td style="text-align:center;font-weight:700;color:${liberadasColor};" title="Suma automática de unidades por día (columnas numeradas)">${sumaDias || 0}${qty > 0 ? ` / ${qty}` : ''}${coincide ? ' ✔' : ''}</td>
                    <td><input class="${loteClass}" list="schedLotesDatalist" value="${loteValor.replace(/"/g, '&quot;')}" onchange="schedGuardarCampo(${f.id},'lote',this.value)" placeholder="—">${loteModeloHtml}${badgeOculto}</td>
                    ${Array.from({length: numDias}, (_, i) => i + 1).map(d => {
                        const wknd = schedEsFinDeSemana(schedMesActual, d) ? ' weekend-cell' : '';
                        const val = dias[d] !== undefined && dias[d] !== null ? dias[d] : '';
                        return `<td class="${wknd}"><input type="number" class="cell-input day-input" value="${val}" onchange="schedGuardarDia(${f.id},${d},this.value)"></td>`;
                    }).join('')}
                    <td class="admin-only" style="position:sticky;right:0;background:var(--bg-surface);">
                        <button class="del-row-btn" onclick="schedEliminarFila(${f.id})" title="Eliminar línea">🗑</button>
                    </td>
                </tr>`;
            });
            document.getElementById('schedTbody').innerHTML = body;
        }

        // ── Selección de filas, ocultar lotes y reporte de series ────────
        function schedToggleSeleccion() {
            schedModoSeleccion = !schedModoSeleccion;
            if (!schedModoSeleccion) schedSeleccionadas.clear();
            document.getElementById('schedSeleccionarBtn').textContent = schedModoSeleccion ? '✕ Cancelar selección' : '☑️ Seleccionar filas';
            schedActualizarBarraAcciones();
            renderScheduleTabla();
        }

        function schedToggleMostrarOcultos() {
            schedMostrarOcultos = !schedMostrarOcultos;
            document.getElementById('schedMostrarOcultosBtn').textContent = schedMostrarOcultos ? '🙈 Ocultar de nuevo' : '👁️ Mostrar ocultos';
            renderScheduleTabla();
        }

        function schedToggleFila(id, marcado) {
            if (marcado) schedSeleccionadas.add(id); else schedSeleccionadas.delete(id);
            schedActualizarBarraAcciones();
        }

        function schedSeleccionarTodos(marcado) {
            const filasVisibles = schedFilas.filter(f => schedMostrarOcultos || !f.oculto);
            filasVisibles.forEach(f => { if (marcado) schedSeleccionadas.add(f.id); else schedSeleccionadas.delete(f.id); });
            renderScheduleTabla();
            schedActualizarBarraAcciones();
        }

        function schedActualizarBarraAcciones() {
            const barra = document.getElementById('schedAccionesBarra');
            const count = document.getElementById('schedSeleccionCount');
            const n = schedSeleccionadas.size;
            barra.style.display = (schedModoSeleccion && n > 0) ? 'flex' : 'none';
            count.textContent = n > 0 ? `${n} línea${n !== 1 ? 's' : ''} seleccionada${n !== 1 ? 's' : ''}` : '';
        }

        function schedLotesDeSeleccion() {
            const ids = Array.from(schedSeleccionadas);
            const lotes = new Set();
            let sinLote = 0;
            ids.forEach(id => {
                const f = schedFindFila(id);
                if (f && f.lote && f.lote.trim()) lotes.add(f.lote.trim());
                else sinLote++;
            });
            return { lotes: Array.from(lotes), sinLote };
        }

        async function schedOcultarSeleccionadas() {
            const { lotes, sinLote } = schedLotesDeSeleccion();
            if (!lotes.length) { alert('Ninguna de las filas seleccionadas tiene un lote asignado todavía.'); return; }
            let msg = `¿Ocultar ${lotes.length} lote${lotes.length !== 1 ? 's' : ''} (${lotes.join(', ')}) del Schedule, Dashboard y KPIs? Los datos se conservan y puedes mostrarlos de nuevo.`;
            if (sinLote > 0) msg += `\n\n(${sinLote} fila(s) seleccionada(s) sin lote se omitirán.)`;
            if (!confirm(msg)) return;

            let errores = [];
            for (const idLote of lotes) {
                try {
                    const res = await fetchAuth(`/api/unidades/lotes/ocultar?id_lote=${encodeURIComponent(idLote)}&backup_onedrive=false`, { method: 'POST' });
                    if (!res.ok) { const d = await res.json().catch(() => ({})); errores.push(`${idLote}: ${d.detail || res.status}`); }
                } catch (e) { errores.push(`${idLote}: ${e.message}`); }
            }
            schedSeleccionadas.clear();
            schedActualizarBarraAcciones();
            await cambiarMesSchedule();
            if (errores.length) alert('Algunos lotes no se pudieron ocultar:\\n' + errores.join('\\n'));
        }

        let schedUnidadesPorLote = {};
        async function schedAbrirModalReporte() {
            const { lotes, sinLote } = schedLotesDeSeleccion();
            if (!lotes.length) { alert('Ninguna de las filas seleccionadas tiene un lote asignado todavía.'); return; }

            const body = document.getElementById('sched-reporte-modal-body');
            body.innerHTML = '<p>Cargando unidades…</p>';
            document.getElementById('sched-reporte-modal').style.display = 'flex';

            try {
                const res = await fetchAuth('/api/unidades/?incluir_ocultas=true');
                const todas = await res.json();
                schedUnidadesTodas = todas; // refresca el cache global también
                schedActualizarDatalistLotes();
                schedUnidadesPorLote = {};
                lotes.forEach(idLote => {
                    schedUnidadesPorLote[idLote] = schedUnidadesDeLote(idLote);
                });

                let html = '';
                if (sinLote > 0) html += `<p style="color:var(--carrier-warn);font-size:.85rem;">${sinLote} fila(s) seleccionada(s) sin lote se omitieron.</p>`;
                lotes.forEach(idLote => {
                    const unidades = schedUnidadesPorLote[idLote] || [];
                    const modelos = [...new Set(unidades.map(u => u.reefer_model).filter(Boolean))];
                    const resumenModelos = modelos.length ? ` · ${modelos.join(', ')}` : '';
                    html += `<details style="margin-bottom:12px;border:1px solid #e5e7eb;border-radius:8px;padding:10px;" ${unidades.length ? 'open' : ''}>
                        <summary style="font-weight:700;cursor:pointer;">📦 Lote: ${idLote}
                            <span style="font-weight:400;color:var(--text-secondary);">(${unidades.length} unidad${unidades.length !== 1 ? 'es' : ''}${resumenModelos})</span>
                        </summary>
                        <div style="margin-top:8px;padding-left:4px;">`;
                    if (!unidades.length) {
                        html += `<p style="font-size:.85rem;color:var(--text-secondary);">Sin unidades registradas para este lote todavía.</p>`;
                    } else {
                        html += `<label style="display:block;font-size:.8rem;padding:2px 0;color:var(--text-secondary);">
                                <input type="checkbox" onchange="this.closest('div').querySelectorAll('.sched-unidad-check').forEach(c=>c.checked=this.checked)" checked> Seleccionar todas
                            </label>`;
                        unidades.forEach(u => {
                            html += `<label style="display:block;font-size:.85rem;padding:2px 0;">
                                <input type="checkbox" class="sched-unidad-check" data-lote="${idLote}" value="${u.unit_number}" checked> ${u.unit_number}${u.reefer_model ? ` <span style="color:var(--text-secondary);">— ${u.reefer_model}</span>` : ''}
                            </label>`;
                        });
                    }
                    html += `</div></details>`;
                });
                body.innerHTML = html;
            } catch (e) {
                body.innerHTML = `<p style="color:red;">Error al cargar unidades: ${e.message}</p>`;
            }
        }

        async function schedConfirmarGenerarReporte() {
            const checks = document.querySelectorAll('.sched-unidad-check:checked');
            const unidades = Array.from(checks).map(c => c.value);
            if (!unidades.length) { alert('Selecciona al menos una unidad para incluir en el reporte.'); return; }

            try {
                const res = await fetchAuth('/api/reportes/lotes-seleccionados', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ unidades })
                });
                if (!res.ok) {
                    const d = await res.json().catch(() => ({}));
                    alert(d.detail || `Error ${res.status} al generar el reporte`);
                    return;
                }
                const blob = await res.blob();
                const a = document.createElement('a');
                a.href = URL.createObjectURL(blob);
                a.download = `Reporte_Series_Seleccion_${Date.now()}.xlsx`;
                a.click();
                document.getElementById('sched-reporte-modal').style.display = 'none';
            } catch (e) {
                alert('Error de red: ' + e.message);
            }
        }

        function schedFindFila(id) {
            return schedFilas.find(f => f.id === id);
        }

        async function schedGuardarCampo(id, campo, valor) {
            const fila = schedFindFila(id);
            if (!fila) return;
            fila[campo] = campo === 'qty' ? (parseInt(valor) || 0) : valor;
            await schedPersistirFila(fila);
            if (campo === 'qty') renderScheduleTabla();
        }

        async function schedGuardarDia(id, dia, valor) {
            const fila = schedFindFila(id);
            if (!fila) return;
            if (!fila.dias) fila.dias = {};
            const num = parseInt(valor);
            if (isNaN(num) || valor === '') { delete fila.dias[dia]; } else { fila.dias[dia] = num; }
            await schedPersistirFila(fila);
            renderScheduleTabla();
        }

        async function schedPersistirFila(fila) {
            document.getElementById('schedGuardando').textContent = 'Guardando...';
            try {
                await fetchAuth('/api/schedule/' + fila.id, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        mes_anio: schedMesActual,
                        linea: fila.linea || '', owner: fila.owner || '', size: fila.size || '',
                        tipo: fila.tipo || '', reefer_brand: fila.reefer_brand || '',
                        notas_evaps: fila.notas_evaps || '', qty: fila.qty || 0,
                        model_no: fila.model_no || '', lote: fila.lote || '', dias: fila.dias || {}
                    })
                });
                document.getElementById('schedGuardando').textContent = '✔ Guardado';
                setTimeout(() => { document.getElementById('schedGuardando').textContent = ''; }, 1200);
            } catch (err) {
                document.getElementById('schedGuardando').textContent = '⚠ Error al guardar';
            }
        }

        async function schedAgregarFilaSchedule() {
            try {
                const res = await fetchAuth('/api/schedule/', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ mes_anio: schedMesActual, dias: {} })
                });
                const data = await res.json();
                schedFilas.push({
                    id: data.id, mes_anio: schedMesActual, orden: data.orden,
                    linea: '', owner: '', size: '', tipo: '', reefer_brand: '',
                    notas_evaps: '', qty: 0, model_no: '', lote: '', dias: {}
                });
                renderScheduleTabla();
            } catch (err) {
                alert('Error al agregar línea');
            }
        }
        function agregarFilaSchedule() { schedAgregarFilaSchedule(); }

        async function schedEliminarFila(id) {
            if (!confirm('¿Eliminar esta línea del schedule?')) return;
            try {
                await fetchAuth('/api/schedule/' + id, { method: 'DELETE' });
                schedFilas = schedFilas.filter(f => f.id !== id);
                renderScheduleTabla();
            } catch (err) {
                alert('Error al eliminar línea');
            }
        }

        cargarDashboard();
    </script>
    """
    return HTMLResponse(content=pagina_con_menu("📊 Panel de Rendimiento Operativo", contenido, "dashboard"))

@router.get("/app/asignaciones", response_class=HTMLResponse)
async def asignaciones():
    contenido = """
    <script> if (window.role !== 'admin' && window.role !== 'visor' && window.role !== 'lider') { window.location.href = '/app/mis-tareas'; } </script>
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
        const actividades = ['Cableado','Programación','Soldadura','Check de fugas','Vacío','Cerrado','Pre-viaje','Horas Corridas','Standby','GPS','Corriendo','Inspección','Accesorios','Toma de Valores','Evidencia','Toma de Series','Extra Eléctrico','Extra Soldador'];
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
            document.getElementById('tecnico').innerHTML = '<option value="">Técnico</option>' + (Array.isArray(tecnicos) ? tecnicos.filter(u => u.role === 'tecnico' || u.role === 'lider').map(u => `<option value="${u.username}">${u.username}</option>`).join('') : '');
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
    <script> if (window.role !== 'admin' && window.role !== 'visor' && window.role !== 'lider') { window.location.href = '/app/mis-tareas'; } </script>
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
                html += `<div style="border-left:6px solid ${color}; background:white; padding:16px; margin-bottom:12px; border-radius:0 12px 12px 0; box-shadow:0 2px 8px rgba(0,0,0,0.05);"><span style="font-size:1.5rem; font-weight:800; color:var(--carrier-blue);">#${t.ticket_num}</span><span class="badge" style="background:${color}; color:white;">${estado}</span><p><b>Unidad:</b> ${t.unit_number} | <b>VIN:</b> ${t.vin_number || 'N/D'}</p><p><b>Descripción:</b> ${t.descripcion}</p><small>Creado por: ${t.creado_por} · ${t.fecha_creacion}</small>${t.reporte_archivo_url ? `<p style="margin:8px 0 0;"><a href="${t.reporte_archivo_url}" target="_blank" style="color:var(--carrier-blue);font-weight:600;">📎 Ver reporte adjunto</a></p>` : ''}${!t.atendido && window.role === 'admin' ? `<button class="btn-danger" onclick="eliminarTicket(${t.id})">🗑️</button>` : ''}${t.atendido && !t.reporte_enviado ? `<button class="btn-primary" onclick="marcarReporte(${t.id})">📤 Marcar reporte enviado</button>` : ''}</div>`;
            });
            if (!html) html = '<p>📋 No hay tickets.</p>'; document.getElementById('ticketsList').innerHTML = html;
            const [unidadesRes, tecnicosRes] = await Promise.all([fetchAuth('/api/unidades/'), fetchAuth('/api/usuarios/')]);
            const unidades = await unidadesRes.json(); const tecnicos = await tecnicosRes.json();
            document.getElementById('unidad').innerHTML = '<option value="">Unidad</option>' + (Array.isArray(unidades) ? unidades.map(u => `<option value="${u.unit_number}">${u.unit_number} (${u.id_lote})</option>`).join('') : '');
            document.getElementById('tecnico').innerHTML = '<option value="">Asignar a técnico</option>' + (Array.isArray(tecnicos) ? tecnicos.filter(u => u.role === 'tecnico' || u.role === 'lider').map(u => `<option value="${u.username}">${u.username}</option>`).join('') : '');
        }
        async function eliminarTicket(id) { if (confirm('¿Eliminar ticket?')) { await fetchAuth('/api/tickets/' + id, { method: 'DELETE' }); cargarTickets(); } }
        async function marcarReporte(id) { const fd = new FormData(); fd.append('reporte', 'Reporte enviado'); await fetchAuth('/api/tickets/' + id + '/report', { method: 'PUT', body: fd }); cargarTickets(); }
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
    <div class="admin-only" style="display:flex; align-items:center; gap:10px; margin-bottom:14px; padding:12px; background:#eff6ff; border:1px dashed #93c5fd; border-radius:10px;">
        <label for="inputEscanearPlaca" class="btn-primary" style="cursor:pointer; margin:0; display:inline-flex; align-items:center; gap:6px;">
            📷 Escanear placa
        </label>
        <input type="file" id="inputEscanearPlaca" accept="image/*" capture="environment" style="display:none;" onchange="escanearPlaca(this)">
        <span id="ocrPlacaEstado" style="font-size:0.85rem; color:#374151;">Toma una foto acercándote al código QR de la placa (el de abajo a la izquierda) para precargar VIN y número de lote, gratis. Siempre podrás corregir los campos antes de guardar.</span>
    </div>
    <form id="unidadForm" class="admin-only" style="display:grid; grid-template-columns: 1fr 1fr; gap:12px;">
        <input type="text" id="unit_number" placeholder="Número Económico" required><input type="text" id="id_lote" placeholder="Número de Lote">
        <input type="text" id="vin_number" placeholder="VIN Number"><input type="text" id="reefer_serial" placeholder="Serie del Reefer">
        <input type="text" id="reefer_model" placeholder="Modelo del Reefer">
        <div style="display:flex; gap:6px; align-items:center;">
            <select id="evaporator_model_1" style="width:135px; flex-shrink:0;" onchange="toggleEvapNA(1)">
                <option value="">Evap. 1: Modelo</option>
                <option value="MJD 1100">MJD 1100</option>
                <option value="MJS 1100">MJS 1100</option>
                <option value="MJD 2200">MJD 2200</option>
                <option value="MJS 2200">MJS 2200</option>
                <option value="N/A">N/A</option>
            </select>
            <input type="text" id="evaporator_serial_mjs11" placeholder="Número de serie" style="flex:1;">
        </div>
        <div style="display:flex; gap:6px; align-items:center;">
            <select id="evaporator_model_2" style="width:135px; flex-shrink:0;" onchange="toggleEvapNA(2)">
                <option value="">Evap. 2: Modelo</option>
                <option value="MJD 1100">MJD 1100</option>
                <option value="MJS 1100">MJS 1100</option>
                <option value="MJD 2200">MJD 2200</option>
                <option value="MJS 2200">MJS 2200</option>
                <option value="N/A">N/A</option>
            </select>
            <input type="text" id="evaporator_serial_mjd22" placeholder="Número de serie" style="flex:1;">
        </div>
        <input type="text" id="engine_serial" placeholder="Motor">
        <input type="text" id="compressor_serial" placeholder="Compresor"><input type="text" id="generator_serial" placeholder="Generador">
        <input type="text" id="battery_charger_serial" placeholder="Cargador de Batería">
        <button type="submit" class="btn-primary" style="grid-column: span 2;">💾 Guardar Registro</button>
    </form>
    <div class="section-title">🔗 Homologar Unidad Duplicada</div>
    <p style="color:#6b7280; font-size:0.85rem; margin:-6px 0 10px;">
        Usa esto si por error se registró/trabajó una unidad con un número incorrecto (ej. le faltó un dígito)
        y ya existe la unidad con el número correcto. Esto migra todo el historial (asignaciones, evidencias,
        tickets) del número incorrecto hacia el correcto, y elimina el registro duplicado.
    </p>
    <div style="display:grid; grid-template-columns: 1fr 1fr auto; gap:10px; align-items:center; margin-bottom:24px;">
        <input type="text" id="homologarAnterior" placeholder="Número incorrecto (ej. 245)">
        <input type="text" id="homologarCorrecto" placeholder="Número correcto (ej. 2145)">
        <button class="btn-primary" onclick="homologarUnidad()">🔗 Homologar</button>
    </div>
    <div class="section-title">📸 Unidades Registradas</div>
    <div id="unidadesList"></div>
    <script src="https://cdn.jsdelivr.net/npm/jsqr@1.4.0/dist/jsQR.js"></script>
    <script>
        const fetchAuth = window.fetchAuth;

        function _cargarImagen(file) {
            return new Promise((resolve, reject) => {
                const img = new Image();
                img.onload = () => resolve(img);
                img.onerror = () => reject(new Error('No se pudo abrir la imagen'));
                img.src = URL.createObjectURL(file);
            });
        }

        function _parsearQR(textoQR) {
            // Formato confirmado de las placas Hyundai Translead:
            // MATERIAL | SERIAL NO. | código interno | VIN completo
            const partes = textoQR.split('|').map(s => s.trim());
            if (partes.length === 4) {
                return {
                    id_lote: partes[0],       // MATERIAL -> Número de Lote en nuestro sistema
                    reefer_serial: partes[1], // SERIAL NO.
                    vin_number: partes[3],    // VIN completo de 17 caracteres
                    texto_completo: textoQR
                };
            }
            // Fallback genérico si la placa no trae exactamente este formato
            const t = textoQR.toUpperCase();
            const vin = (t.match(/\b([A-HJ-NPR-Z0-9]{17})\b/) || [])[1] || '';
            return { vin_number: vin, id_lote: '', reefer_serial: '', texto_completo: textoQR };
        }

        function _prepararCanvas(img, maxDim) {
            const escala = maxDim ? Math.min(1, maxDim / Math.max(img.naturalWidth, img.naturalHeight)) : 1;
            const canvas = document.createElement('canvas');
            canvas.width = Math.max(1, Math.round(img.naturalWidth * escala));
            canvas.height = Math.max(1, Math.round(img.naturalHeight * escala));
            const ctx = canvas.getContext('2d');
            ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
            return { canvas, ctx };
        }

        // Escala de grises + estiramiento de contraste — ayuda cuando el brillo del metal
        // de la placa aplana el contraste del QR.
        function _realzarContraste(ctx, w, h) {
            const imgData = ctx.getImageData(0, 0, w, h);
            const d = imgData.data;
            let min = 255, max = 0;
            for (let i = 0; i < d.length; i += 4) {
                const g = d[i] * 0.299 + d[i + 1] * 0.587 + d[i + 2] * 0.114;
                if (g < min) min = g;
                if (g > max) max = g;
            }
            const rango = Math.max(1, max - min);
            for (let i = 0; i < d.length; i += 4) {
                const g = d[i] * 0.299 + d[i + 1] * 0.587 + d[i + 2] * 0.114;
                const v = Math.min(255, Math.max(0, ((g - min) / rango) * 255));
                d[i] = d[i + 1] = d[i + 2] = v;
            }
            ctx.putImageData(imgData, 0, 0);
        }

        // Busca TODOS los códigos QR visibles en el canvas (la placa trae hasta 3: QR CODE,
        // OP. MANUAL y V.I.N.), tapando cada uno encontrado para poder detectar el siguiente.
        function _buscarQRsEnCanvas(canvas, ctx, maxIntentos = 6) {
            const resultados = [];
            for (let i = 0; i < maxIntentos; i++) {
                const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
                const r = jsQR(imageData.data, canvas.width, canvas.height, { inversionAttempts: 'attemptBoth' });
                if (!r) break;
                resultados.push(r.data);
                const loc = r.location;
                const xs = [loc.topLeftCorner.x, loc.topRightCorner.x, loc.bottomLeftCorner.x, loc.bottomRightCorner.x];
                const ys = [loc.topLeftCorner.y, loc.topRightCorner.y, loc.bottomLeftCorner.y, loc.bottomRightCorner.y];
                const minX = Math.max(0, Math.min(...xs) - 8), maxX = Math.min(canvas.width, Math.max(...xs) + 8);
                const minY = Math.max(0, Math.min(...ys) - 8), maxY = Math.min(canvas.height, Math.max(...ys) + 8);
                ctx.fillStyle = '#808080';
                ctx.fillRect(minX, minY, maxX - minX, maxY - minY);
            }
            return resultados;
        }

        // De todos los QR encontrados, prioriza el que tenga el formato de 4 campos conocido;
        // si no, el que contenga un VIN válido.
        function _elegirMejorTexto(textos) {
            const conFormato = textos.find(t => t.split('|').length === 4);
            if (conFormato) return conFormato;
            const conVin = textos.find(t => /\b[A-HJ-NPR-Z0-9]{17}\b/i.test(t));
            if (conVin) return conVin;
            return textos[0] || '';
        }

        async function escanearPlaca(inputEl) {
            const file = inputEl.files[0];
            if (!file) return;
            const estado = document.getElementById('ocrPlacaEstado');
            estado.textContent = '🔎 Buscando el código QR en la foto...';
            estado.style.color = '#1d4ed8';
            try {
                const img = await _cargarImagen(file);
                // Las fotos de celular reales pueden ser muy grandes; se prueban varias escalas
                // (reducida, completa y una intermedia), y en cada una se intenta también con
                // contraste realzado, hasta encontrar al menos un QR.
                const escalasAProbar = [1800, null, 1000];
                let textos = [];
                for (const maxDim of escalasAProbar) {
                    const { canvas, ctx } = _prepararCanvas(img, maxDim);
                    textos = _buscarQRsEnCanvas(canvas, ctx);
                    if (textos.length) break;

                    const { canvas: canvas2, ctx: ctx2 } = _prepararCanvas(img, maxDim);
                    _realzarContraste(ctx2, canvas2.width, canvas2.height);
                    textos = _buscarQRsEnCanvas(canvas2, ctx2);
                    if (textos.length) break;
                }

                if (!textos.length) {
                    estado.textContent = '⚠️ No se detectó ningún código QR en la foto. Acércate más solo al QR (el de abajo a la izquierda), evita el reflejo del metal, y vuelve a intentar.';
                    estado.style.color = '#d97706';
                    return;
                }

                const campos = _parsearQR(_elegirMejorTexto(textos));
                let algo = false;
                if (campos.vin_number) { document.getElementById('vin_number').value = campos.vin_number; algo = true; }
                if (campos.id_lote)    { document.getElementById('id_lote').value = campos.id_lote; algo = true; }

                if (algo) {
                    estado.textContent = '✅ Datos leídos del código QR. Revisa y corrige lo que haga falta antes de guardar.';
                    estado.style.color = '#16a34a';
                } else {
                    estado.textContent = `ℹ️ Se leyó un QR pero no reconocí el formato. Contenido leído: "${campos.texto_completo}". Cópialo manualmente si aplica.`;
                    estado.style.color = '#374151';
                }
            } catch (e) {
                console.error(e);
                estado.textContent = '❌ Error al procesar la imagen — llena los campos manualmente.';
                estado.style.color = '#dc2626';
            } finally {
                inputEl.value = '';
            }
        }
        async function homologarUnidad() {
            const anterior = document.getElementById('homologarAnterior').value.trim();
            const correcto = document.getElementById('homologarCorrecto').value.trim();
            if (!anterior || !correcto) return alert('Ingresa ambos números de unidad.');
            if (!confirm(`¿Migrar todo el historial de "${anterior}" hacia "${correcto}"? Esto no se puede deshacer.`)) return;
            const res = await fetchAuth(`/api/unidades/homologar?numero_anterior=${encodeURIComponent(anterior)}&numero_correcto=${encodeURIComponent(correcto)}`, { method: 'POST' });
            const data = await res.json();
            if (res.ok) {
                alert(`✅ ${data.mensaje}\nAsignaciones migradas: ${data.asignaciones_migradas}\nEvidencias migradas: ${data.evidencias_migradas}\nTickets migrados: ${data.tickets_migrados}`);
                document.getElementById('homologarAnterior').value = '';
                document.getElementById('homologarCorrecto').value = '';
                cargarUnidades();
            } else {
                alert('❌ ' + (data.detail || 'Error al homologar la unidad.'));
            }
        }
        function toggleEvapNA(slot) {
            const modelSel = document.getElementById('evaporator_model_' + slot);
            const serialField = slot === 1 ? 'evaporator_serial_mjs11' : 'evaporator_serial_mjd22';
            const input = document.getElementById(serialField);
            if (modelSel.value === 'N/A') { input.value = 'N/A'; input.disabled = true; }
            else { if (input.value === 'N/A') input.value = ''; input.disabled = false; }
        }
        async function cargarUnidades() { const res = await fetchAuth('/api/unidades/'); const unidades = await res.json(); let html = '<table><thead><tr><th>#Económico</th><th>Lote</th><th>VIN</th><th>Reefer Serial</th><th>Modelo</th><th>Motor</th><th>Compresor</th></tr></thead><tbody>'; if (Array.isArray(unidades)) unidades.forEach(u => html += `<tr><td>${u.unit_number}</td><td>${u.id_lote||''}</td><td style="font-family:monospace;">${u.vin_number||''}</td><td>${u.reefer_serial||''}</td><td>${u.reefer_model||''}</td><td style="font-family:monospace;">${u.engine_serial||''}</td><td>${u.compressor_serial||''}</td>`); html += '</tbody></table>'; document.getElementById('unidadesList').innerHTML = html; }
        document.getElementById('unidadForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            const data = {
                unit_number: document.getElementById('unit_number').value,
                id_lote: document.getElementById('id_lote').value,
                vin_number: document.getElementById('vin_number').value,
                reefer_serial: document.getElementById('reefer_serial').value,
                reefer_model: document.getElementById('reefer_model').value,
                evaporator_model_1: document.getElementById('evaporator_model_1').value,
                evaporator_serial_mjs11: document.getElementById('evaporator_serial_mjs11').value,
                evaporator_model_2: document.getElementById('evaporator_model_2').value,
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
# PDI — PRE-DELIVERY INSPECTION (Inspección Pre-Entrega)
# ------------------------------------------------------------
@router.get("/app/pdi", response_class=HTMLResponse)
async def pdi_lista():
    contenido = """
    <script> if (window.role !== 'admin') { window.location.href = '/app/mis-tareas'; } </script>
    <div class="inv-info-bar" id="infoBar">📋 Selecciona un lote para asignar el tipo de reefer (X4 / Vector) y ver el estado de PDI de cada unidad.</div>

    <div id="loteConfigAdmin" style="display:none; margin-bottom:16px;"></div>

    <div style="display:flex; gap:12px; margin-bottom:16px; flex-wrap:wrap; align-items:center;">
        <select id="selLote" onchange="cargarUnidadesLote()" style="min-width:220px;"><option value="">— Selecciona un lote —</option></select>
        <span id="tipoLoteBadge"></span>
    </div>

    <div id="pdiTabla"></div>

    <script>
        const fetchAuth = window.fetchAuth;
        let lotesConfig = [];

        async function cargarLotes() {
            const res = await fetchAuth('/api/pdi/lotes-config');
            lotesConfig = await res.json();
            const sel = document.getElementById('selLote');
            sel.innerHTML = '<option value="">— Selecciona un lote —</option>' +
                lotesConfig.map(l => `<option value="${l.id_lote}">${l.id_lote} (${l.total_unidades} unidades)${l.tipo_reefer ? ' — ' + l.tipo_reefer.toUpperCase() : ' — sin tipo asignado'}</option>`).join('');
        }

        function renderTipoBadge(lote) {
            if (!lote) { document.getElementById('tipoLoteBadge').innerHTML = ''; return; }
            const badge = lote.tipo_reefer
                ? `<span class="user-chip" style="background:#0057A8;">🧊 ${lote.tipo_reefer.toUpperCase()}</span>`
                : `<span class="user-chip" style="background:#d97706;">⚠️ Sin tipo de reefer asignado</span>`;
            document.getElementById('tipoLoteBadge').innerHTML = badge;

            if (window.role === 'admin') {
                document.getElementById('loteConfigAdmin').style.display = 'block';
                document.getElementById('loteConfigAdmin').innerHTML = `
                    <div style="background:var(--bg-surface); border-radius:12px; padding:14px 18px; display:flex; gap:12px; align-items:center; flex-wrap:wrap;">
                        <strong>Tipo de reefer para el lote ${lote.id_lote}:</strong>
                        <button class="btn-primary" onclick="setTipoLote('${lote.id_lote}','x4')">X4 7300/7500</button>
                        <button class="btn-primary" onclick="setTipoLote('${lote.id_lote}','vector')">Vector 8100/8500/8600MT/8611MT</button>
                    </div>`;
            }
        }

        async function setTipoLote(id_lote, tipo) {
            const res = await fetchAuth('/api/pdi/lotes-config', { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({id_lote, tipo_reefer: tipo}) });
            const data = await res.json();
            if (!res.ok) { alert(data.detail || 'Error'); return; }
            await cargarLotes();
            const sel = document.getElementById('selLote');
            sel.value = id_lote;
            cargarUnidadesLote();
        }

        async function cargarUnidadesLote() {
            const id_lote = document.getElementById('selLote').value;
            const lote = lotesConfig.find(l => l.id_lote === id_lote);
            renderTipoBadge(lote);
            const tabla = document.getElementById('pdiTabla');
            if (!id_lote) { tabla.innerHTML = ''; return; }

            const [unidadesRes, pdisRes] = await Promise.all([
                fetchAuth('/api/unidades/'),
                fetchAuth(`/api/pdi?id_lote=${encodeURIComponent(id_lote)}`)
            ]);
            const unidades = (await unidadesRes.json()).filter(u => u.id_lote === id_lote);
            const pdis = await pdisRes.json();
            const pdiPorUnidad = {};
            pdis.forEach(p => { pdiPorUnidad[p.unit_number] = p; });

            let html = '<table><thead><tr><th>Unidad</th><th>Modelo</th><th>Tipo PDI</th><th>Estado</th><th>Acción</th></tr></thead><tbody>';
            unidades.forEach(u => {
                const p = pdiPorUnidad[u.unit_number];
                const estado = p ? p.estado : 'sin iniciar';
                const colores = {'sin iniciar':'#9ca3af','borrador':'#d97706','completado':'#16a34a'};
                html += `<tr>
                    <td><strong>${u.unit_number}</strong></td>
                    <td>${u.reefer_model || '<em>sin capturar</em>'}</td>
                    <td>${p ? p.tipo.toUpperCase() : '—'}</td>
                    <td><span style="color:${colores[estado]}; font-weight:700;">${estado}</span></td>
                    <td><button class="btn-primary" onclick="location.href='/app/pdi/${u.unit_number}'">📋 Abrir PDI</button></td>
                </tr>`;
            });
            html += '</tbody></table>';
            if (!unidades.length) html = '<p style="color:var(--text-secondary);">Este lote no tiene unidades registradas todavía.</p>';
            tabla.innerHTML = html;
        }

        cargarLotes();
    </script>
    """
    return HTMLResponse(content=pagina_con_menu("📋 PDI — Inspección Pre-Entrega", contenido, "pdi"))


@router.get("/app/pdi/{unit_number}", response_class=HTMLResponse)
async def pdi_form(unit_number: str):
    contenido = f"""
    <script> if (window.role !== 'admin') {{ window.location.href = '/app/mis-tareas'; }} </script>
    <div id="pdiRoot">Cargando PDI de {unit_number}…</div>

    <script>
        const fetchAuth = window.fetchAuth;
        const UNIT = {unit_number!r};
        let PDI_ID = null, TEMPLATE = null, DATOS = {{}};

        function chk(clave) {{ return DATOS[clave] === '1'; }}
        function val(clave) {{ return DATOS[clave] || ''; }}
        function esc(s) {{ return (s || '').toString().replace(/"/g, '&quot;'); }}

        async function cargar() {{
            const res = await fetchAuth(`/api/pdi/unidad/${{UNIT}}`);
            const data = await res.json();

            if (data.requiere_tipo) {{
                document.getElementById('pdiRoot').innerHTML = `
                    <div style="background:#fef3c7; border:1px solid #d97706; border-radius:12px; padding:20px;">
                        <h3 style="margin-top:0;">⚠️ Falta asignar el tipo de reefer</h3>
                        <p>${{data.mensaje}}</p>
                        <button class="btn-primary" onclick="location.href='/app/pdi'">Ir a configurar el lote</button>
                    </div>`;
                return;
            }}

            PDI_ID = data.pdi.id; TEMPLATE = data.template; DATOS = data.datos;
            renderForm(data.pdi, data.campos_faltantes);
        }}

        function renderForm(pdi, faltantes) {{
            let html = '';

            html += `<div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:10px; margin-bottom:16px;">
                <div><span class="user-chip" style="background:#0057A8;">🧊 ${{TEMPLATE.nombre}}</span> &nbsp; <span style="color:var(--text-secondary);">Unidad ${{UNIT}}</span></div>
                <div>
                    <button class="btn-warning" onclick="guardar('borrador')">💾 Guardar borrador</button>
                    <button class="btn-primary" onclick="guardar('completado')">✅ Marcar como completado</button>
                    <button class="btn-primary" onclick="window.print()">🖨️ Imprimir</button>
                    <button class="btn-primary" onclick="descargarPDF()" title="El PDF refleja el último guardado. Guarda antes de descargar si hiciste cambios.">📄 Descargar PDF</button>
                </div>
            </div>`;

            if (faltantes && faltantes.length) {{
                html += `<div style="background:#fef3c7; border:1px solid #d97706; border-radius:12px; padding:14px 18px; margin-bottom:16px;">
                    <strong>⚠️ Estas lecturas no existen todavía en Toma de Valores:</strong>
                    <ul style="margin:8px 0;">${{faltantes.map(f => `<li>${{f}}</li>`).join('')}}</ul>
                    ${{window.role === 'admin'
                        ? `<button class="btn-primary" onclick='agregarFaltantes(${{JSON.stringify(faltantes)}})'>➕ Agregar a Toma de Valores</button>`
                        : `<em>Pide a un administrador que los agregue a Toma de Valores para que se autocompleten aquí.</em>`}}
                </div>`;
            }}

            // ── Encabezado ──────────────────────────────────────────────
            html += `<div class="card" style="background:var(--bg-surface); border-radius:14px; padding:18px 22px; margin-bottom:18px;">
                <h3 style="margin-top:0;">🧾 Identificación</h3>
                <div style="display:grid; grid-template-columns:repeat(auto-fill, minmax(240px,1fr)); gap:12px;">
                    ${{TEMPLATE.header_fields.map(hf => `
                        <div>
                            <label style="font-size:0.8rem; color:var(--text-secondary); display:block; margin-bottom:4px;">${{hf.label}}</label>
                            <input type="text" data-header="${{hf.clave}}" value="${{esc(pdi[hf.clave] || '')}}" style="width:100%;">
                        </div>`).join('')}}
                </div>
            </div>`;

            // ── Checklist por secciones ─────────────────────────────────
            TEMPLATE.secciones.forEach(sec => {{
                const badgeAuto = !sec.es_registro ? `<span style="font-size:0.75rem; color:#16a34a; font-weight:600;">✓ auto-completado — revisa y desmarca si algo falló</span>` : `<span style="font-size:0.75rem; color:#d97706; font-weight:700;">✋ requiere llenado manual</span>`;
                html += `<div class="card" style="background:var(--bg-surface); border-radius:14px; padding:18px 22px; margin-bottom:14px;">
                    <h3 style="margin-top:0; display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:8px;">${{sec.titulo}} ${{badgeAuto}}</h3>`;
                sec.items.forEach((texto, i) => {{
                    const clave = `chk_${{sec.clave}}_${{i+1}}`;
                    html += `<label style="display:flex; gap:10px; align-items:flex-start; padding:6px 0; border-bottom:1px solid var(--border-color-soft);">
                        <input type="checkbox" data-check="${{clave}}" ${{chk(clave) ? 'checked' : ''}} style="margin-top:3px;">
                        <span>${{texto}}</span>
                    </label>`;
                }});
                html += `</div>`;
            }});

            // ── Lecturas ────────────────────────────────────────────────
            const gruposLecturas = {{}};
            TEMPLATE.lecturas.forEach(l => {{ (gruposLecturas[l.grupo] = gruposLecturas[l.grupo] || []).push(l); }});
            html += `<div class="card" style="background:var(--bg-surface); border-radius:14px; padding:18px 22px; margin-bottom:14px;">
                <h3 style="margin-top:0;">📊 Lecturas del Run Test</h3>
                <p style="color:var(--text-secondary); font-size:0.85rem;">Se pre-llenan automáticamente desde Toma de Valores cuando existe un campo equivalente.</p>`;
            Object.keys(gruposLecturas).forEach(grupo => {{
                html += `<h4 style="margin:14px 0 6px; color:var(--text-secondary);">${{grupo}}</h4>
                    <div style="display:grid; grid-template-columns:repeat(auto-fill, minmax(220px,1fr)); gap:12px;">`;
                gruposLecturas[grupo].forEach(l => {{
                    const clave = `lec_${{l.clave}}`;
                    html += `<div>
                        <label style="font-size:0.8rem; color:var(--text-secondary); display:block; margin-bottom:4px;">${{l.label}} ${{l.unidad ? '(' + l.unidad + ')' : ''}}</label>
                        <input type="text" data-lectura="${{clave}}" value="${{esc(val(clave))}}" style="width:100%;">
                    </div>`;
                }});
                html += `</div>`;
            }});
            html += `</div>`;

            // ── Tabla de configuración ─────────────────────────────────
            html += `<details style="background:var(--bg-surface); border-radius:14px; padding:14px 22px; margin-bottom:14px;">
                <summary style="cursor:pointer; font-weight:700; font-size:1.05rem;">⚙️ Tabla de Configuración (Ajuste de Fábrica / Cambio a)</summary>
                <table style="margin-top:12px;"><thead><tr><th>Grupo</th><th>Parámetro</th><th>Ajuste de Fábrica</th><th>Cambio a</th></tr></thead><tbody>`;
            TEMPLATE.config_table.forEach((row, i) => {{
                const clave = `cfg_${{i}}`;
                html += `<tr><td>${{row[0]}}</td><td>${{row[1]}}</td><td>${{row[2]}}</td>
                    <td><input type="text" data-config="${{clave}}" value="${{esc(val(clave))}}" style="width:100%; margin:0;"></td></tr>`;
            }});
            html += `</tbody></table></details>`;

            // ── Firma / comentarios ─────────────────────────────────────
            html += `<div class="card" style="background:var(--bg-surface); border-radius:14px; padding:18px 22px; margin-bottom:18px;">
                <h3 style="margin-top:0;">✍️ Cierre</h3>
                <div style="display:grid; grid-template-columns:repeat(auto-fill, minmax(240px,1fr)); gap:12px;">
                    <div><label style="font-size:0.8rem; color:var(--text-secondary); display:block; margin-bottom:4px;">Dealer / Distribuidor</label>
                        <input type="text" data-header="dealer_firma" value="${{esc(pdi.dealer_firma || '')}}" style="width:100%;"></div>
                    <div><label style="font-size:0.8rem; color:var(--text-secondary); display:block; margin-bottom:4px;">Técnico que Inspeccionó</label>
                        <input type="text" data-header="tecnico_inspecciono" value="${{esc(pdi.tecnico_inspecciono || '')}}" style="width:100%;"></div>
                </div>
                <label style="font-size:0.8rem; color:var(--text-secondary); display:block; margin:12px 0 4px;">Comentarios</label>
                <textarea data-header="comentarios" rows="3" style="width:100%;">${{pdi.comentarios || ''}}</textarea>
            </div>`;

            document.getElementById('pdiRoot').innerHTML = html;
        }}

        async function agregarFaltantes(campos) {{
            const res = await fetchAuth(`/api/pdi/${{PDI_ID}}/campos-faltantes/agregar`, {{method:'POST', headers:{{'Content-Type':'application/json'}}, body: JSON.stringify({{campos}})}});
            const data = await res.json();
            alert(data.mensaje || 'Listo');
            cargar();
        }}

        async function guardar(estado) {{
            const root = document.getElementById('pdiRoot');
            const headerValores = {{}};
            root.querySelectorAll('[data-header]').forEach(el => headerValores[el.dataset.header] = el.value);
            const datosValores = {{}};
            root.querySelectorAll('[data-check]').forEach(el => datosValores[el.dataset.check] = el.checked ? '1' : '0');
            root.querySelectorAll('[data-lectura]').forEach(el => datosValores[el.dataset.lectura] = el.value);
            root.querySelectorAll('[data-config]').forEach(el => {{ if (el.value) datosValores[el.dataset.config] = el.value; }});

            await fetchAuth(`/api/pdi/${{PDI_ID}}`, {{method:'PUT', headers:{{'Content-Type':'application/json'}}, body: JSON.stringify({{valores: headerValores, estado}})}});
            await fetchAuth(`/api/pdi/${{PDI_ID}}/datos`, {{method:'POST', headers:{{'Content-Type':'application/json'}}, body: JSON.stringify({{valores: datosValores}})}});
            alert(estado === 'completado' ? '✅ PDI marcado como completado' : '💾 Borrador guardado');
            cargar();
        }}

        async function descargarPDF() {{
            const btn = event.target;
            const textoOriginal = btn.textContent;
            btn.disabled = true; btn.textContent = '⏳ Generando...';
            try {{
                const resp = await fetchAuth(`/api/pdi/${{PDI_ID}}/pdf`);
                if (!resp.ok) throw new Error('No se pudo generar el PDF');
                const blob = await resp.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `PDI_${{TEMPLATE.clave.toUpperCase()}}_${{UNIT}}.pdf`;
                document.body.appendChild(a);
                a.click();
                a.remove();
                window.URL.revokeObjectURL(url);
            }} catch (e) {{
                alert('❌ Error al generar el PDF: ' + e.message);
            }} finally {{
                btn.disabled = false; btn.textContent = textoOriginal;
            }}
        }}

        cargar();
    </script>
    """
    return HTMLResponse(content=pagina_con_menu(f"📋 PDI — {unit_number}", contenido, "pdi"))

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
            <option value="lider">Líder</option>
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
                        <button class="btn-sm btn-sm-blue" onclick="abrirModalPerfil(${u.id}, '${u.username}', '${u.foto_url || ''}', '${(u.puesto || '').replace(/'/g,"\\'")}', '${(u.nombre_completo || '').replace(/'/g,"\\'")}')">🖼 Perfil</button>
                        <button class="btn-sm btn-sm-amber" onclick="abrirModalPassword(${u.id}, '${u.username}')">🔑 Pwd</button>
                        <button class="btn-sm btn-sm-red" onclick="eliminarUsuario(${u.id}, '${u.username}')">🗑</button>
                    ` : '';
                    const nombreMostrar = u.nombre_completo
                        ? `${ROLE_EMOJI[u.role] || ''} ${u.nombre_completo} <span style="font-weight:400;color:var(--text-secondary);font-size:0.78rem;">(${u.username})</span>`
                        : `${ROLE_EMOJI[u.role] || ''} ${u.username}`;

                    html += `
                    <div class="perfil-card role-${u.role}">
                        ${fotoHtml}
                        <div class="perfil-body">
                            <div class="perfil-nombre">${nombreMostrar}</div>
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
        function abrirModalPerfil(userId, username, fotoActual, puestoActual, nombreActual) {
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

                    <!-- Nombre completo -->
                    <label style="font-size:0.82rem;font-weight:700;color:var(--carrier-blue);display:block;margin-bottom:4px;">Nombre completo</label>
                    <input id="inputNombreCompleto" type="text" placeholder="Ej: Carlos Ramírez" value="${nombreActual || ''}" style="margin-bottom:14px;">
                    <p style="font-size:0.75rem;color:var(--text-secondary);margin:-10px 0 14px;">Este nombre se usará en gráficas y horarios en lugar del usuario (${username}).</p>

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
            const nombre_completo = document.getElementById('inputNombreCompleto').value.trim();
            const btn = document.getElementById('btnGuardarPerfil');
            btn.textContent = 'Guardando...'; btn.disabled = true;
            const [res] = await Promise.all([
                fetchAuth('/api/usuarios/' + userId + '/perfil', {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ foto_url, puesto })
                }),
                fetchAuth('/api/usuarios/' + userId + '/nombre', {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ nombre_completo })
                })
            ]);
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
    <script> if (window.role !== 'admin' && window.role !== 'lider') { window.location.href = '/app/mis-tareas'; } </script>

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

      <script>
        // Los líderes solo pueden ver la galería de evidencias en este panel;
        // el resto de pestañas (usuarios, unidades, SQL, lotes) sigue siendo admin-only.
        if (window.role === 'lider') {
          ['usuarios', 'unidades', 'sql', 'lotes'].forEach(s => {
            const tabBtn = document.getElementById('tab-' + s);
            if (tabBtn) tabBtn.style.display = 'none';
          });
          document.addEventListener('DOMContentLoaded', () => { if (typeof showTab === 'function') showTab('evidencias'); });
        }
      </script>

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
            <option value="lider">Líder</option>
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
                <option value="lider">Líder</option>
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
          <video id="ev-lb-video" controls playsinline style="display:none;max-width:92vw;max-height:82vh;border-radius:8px;"></video>
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
            let grupoActual = null, optgroup = null;
            data.forEach(u => {
                const lote = u.id_lote || 'Sin lote';
                if (lote !== grupoActual) {
                    grupoActual = lote;
                    optgroup = document.createElement('optgroup');
                    optgroup.label = lote;
                    sel.appendChild(optgroup);
                }
                const opt = document.createElement('option');
                opt.value = u.unit_number;
                opt.textContent = `${u.unit_number}  (${u.total} foto${u.total===1?'':'s'})`;
                optgroup.appendChild(opt);
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
            badge.textContent = `${data.total} archivo${data.total===1?'':'s'}`;
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
                        evAbrirLightbox(f.id, f.nombre, f.tecnico, f.fecha, f.actividad, f.tipo);
                    }
                };

                const esVideo = f.tipo === 'video';
                const media = document.createElement(esVideo ? 'video' : 'img');
                media.alt   = f.nombre;
                if (esVideo) {
                    media.muted = true;
                    media.preload = 'metadata';
                    media.style.cssText = 'width:100%;height:130px;object-fit:cover;display:block;background:#111827;';
                } else {
                    media.loading = 'lazy';
                    media.style.cssText = 'width:100%;height:130px;object-fit:cover;display:block;';
                }
                const img = media;
                img.onerror = ()=>{
                    // En vez de ocultar la foto silenciosamente (lo que la hacía "desaparecer"
                    // sin aviso), mostramos un placeholder visible de error de carga.
                    img.style.display = 'none';
                    if (!card.querySelector('.ev-error-placeholder')) {
                        const ph = document.createElement('div');
                        ph.className = 'ev-error-placeholder';
                        ph.style.cssText = 'width:100%;height:130px;display:flex;align-items:center;justify-content:center;flex-direction:column;gap:4px;background:#fef2f2;color:#b91c1c;font-size:11px;text-align:center;padding:6px;';
                        ph.innerHTML = `⚠️<br>Error al cargar<br>${esVideo ? 'este video' : 'esta foto'}`;
                        card.insertBefore(ph, card.firstChild);
                    }
                };
                fetchAuth(`/api/evidencias/foto/${f.id}`)
                    .then(r => r.ok ? r.blob() : Promise.reject())
                    .then(blob => { img.src = URL.createObjectURL(blob); })
                    .catch(() => { img.onerror(); });

                const playBadge = document.createElement('div');
                if (esVideo) {
                    playBadge.style.cssText = 'position:absolute;top:6px;right:6px;background:rgba(0,0,0,.55);color:#fff;border-radius:6px;padding:2px 6px;font-size:11px;display:flex;align-items:center;gap:3px;z-index:2;';
                    playBadge.innerHTML = '▶ video';
                }

                const info = document.createElement('div');
                info.style.cssText = 'padding:6px 8px;font-size:11px;color:var(--color-text-secondary);line-height:1.5;';
                info.innerHTML = `<b style="color:var(--color-text-primary);font-size:12px;">${f.nombre.length>22?f.nombre.slice(0,19)+'…':f.nombre}</b><br>
                  👷 ${f.tecnico||'—'}<br>
                  ${f.actividad ? '🛠 '+f.actividad+'<br>' : ''}
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
                if (esVideo) card.appendChild(playBadge);
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

    function evAbrirLightbox(id, nombre, tecnico, fecha, actividad, tipo) {
        const lb  = document.getElementById('ev-lightbox');
        const img = document.getElementById('ev-lb-img');
        const vid = document.getElementById('ev-lb-video');
        const cap = document.getElementById('ev-lb-caption');
        const esVideo = tipo === 'video';
        img.src = ''; img.style.display = 'none';
        vid.pause(); vid.removeAttribute('src'); vid.load(); vid.style.display = 'none';
        cap.textContent = `${nombre}  ·  👷 ${tecnico||'—'}  ${actividad?'·  🛠 '+actividad+'  ':''}·  ${fecha?fecha.slice(0,10):''}`;
        lb.style.display = 'flex';
        if (esVideo) {
            vid.style.display = '';
            fetchAuth(`/api/evidencias/foto/${id}`)
                .then(r => r.ok ? r.blob() : Promise.reject())
                .then(blob => { vid.src = URL.createObjectURL(blob); })
                .catch(() => {
                    vid.style.display = 'none';
                    cap.textContent = `⚠️ No se pudo cargar este video (${nombre}). El archivo podría estar dañado o incompleto.`;
                });
        } else {
            img.style.display = '';
            fetchAuth(`/api/evidencias/foto/${id}`)
                .then(r => r.ok ? r.blob() : Promise.reject())
                .then(blob => { img.src = URL.createObjectURL(blob); })
                .catch(() => {
                    img.style.display = 'none';
                    cap.textContent = `⚠️ No se pudo cargar esta foto (${nombre}). El archivo podría estar dañado o incompleto.`;
                });
        }
    }

    function evCloseLightbox(e) {
        if (e.target.id === 'ev-lightbox' || e.target.id === 'ev-lb-img') {
            document.getElementById('ev-lightbox').style.display = 'none';
            const vid = document.getElementById('ev-lb-video');
            vid.pause(); vid.removeAttribute('src'); vid.load();
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
            ['Evaporador 1', [u.evaporator_model_1, u.evaporator_serial_mjs11].filter(Boolean).join(' — ')],
            ['Evaporador 2', [u.evaporator_model_2, u.evaporator_serial_mjd22].filter(Boolean).join(' — ')],
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
                        btn = `<button class="btn-success" onclick="completarTarea(${t.id}, '${t.unidad}', '${t.actividad_id}', ${t.ticket_id != null ? t.ticket_id : 'null'})">✅ Finalizar</button>`;
                        if (t.actividad_id === 'Corriendo') btn += `<button class="btn-primary" onclick="pausarTarea(${t.id})">⏸️ Pausar</button>`;
                        if (t.actividad_id === 'Toma de Valores') btn += `<button class="btn-primary" onclick="tomarValores(${t.id})">📊 Ingresar Valores</button>`;
                        if (t.actividad_id === 'Toma de Series') btn += `<button class="btn-primary" onclick="tomarSeries(${t.id})">🔢 Ingresar Series</button>`;
                    }
                    html += `<div style="background:white; border-radius:12px; padding:16px; margin-bottom:12px; box-shadow:0 2px 8px rgba(0,0,0,0.05); display:flex; justify-content:space-between; align-items:center;"><div><b>${t.actividad_id}</b> — Unidad: <b>${t.unidad}</b><br><span class="badge" style="background:${t.estado === 'pendiente' ? 'var(--carrier-warn)' : 'var(--carrier-success)'}; color:white;">${t.estado}</span></div><div>${btn}</div></div>`;
                });
            }
            document.getElementById('tareasList').innerHTML = html;
        }

        async function iniciarTarea(id) { const res = await fetchAuth('/api/asignaciones/' + id + '/iniciar', { method: 'PATCH' }); if (res.ok) cargarTareas(); else alert('Error al iniciar la tarea'); }
        async function pausarTarea(id) {
            const res = await fetchAuth('/api/asignaciones/' + id + '/pausar', { method: 'PATCH' });
            if (res.ok) cargarTareas();
            else { const d = await res.json().catch(()=>({})); alert(d.detail || 'Error al pausar la tarea'); }
        }
        // Comprime una imagen con Canvas API (max 1200px, calidad 0.75 JPEG) — compartida
        async function _comprimirImagenCanvas(file) {
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

        async function completarTarea(id, unidad, actividad, ticketId) {
            const prev = document.getElementById('modalFinalizar');
            if (prev) prev.remove();

            const esTicket = !!(actividad && actividad.indexOf('Ticket #') === 0 && ticketId);

            // ¿Ya tiene fotos guardadas esta actividad? (por si se subieron antes o se reintenta)
            let fotosPrevias = 0;
            try {
                const cntRes = await fetchAuth(`/api/evidencias/count-asignacion/${id}`);
                if (cntRes.ok) fotosPrevias = (await cntRes.json()).total || 0;
            } catch(e) {}

            const modal = document.createElement('div');
            modal.id = 'modalFinalizar';
            modal.dataset.unidad = unidad || '';
            modal.dataset.fotosPrevias = fotosPrevias;
            modal.dataset.esTicket = esTicket ? '1' : '0';
            modal.dataset.ticketId = ticketId != null ? ticketId : '';
            modal.style.cssText = 'position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.55);display:flex;justify-content:center;align-items:center;z-index:500;overflow-y:auto;padding:20px 0;';
            modal.innerHTML = `
                <div style="background:white;border-radius:20px;padding:32px;width:90%;max-width:520px;box-shadow:0 20px 60px rgba(0,43,91,0.25);animation:fadeInM 0.2s ease;">
                    <div style="display:flex;align-items:center;gap:12px;margin-bottom:8px;">
                        <div style="background:#f0fdf4;border-radius:12px;width:48px;height:48px;display:flex;align-items:center;justify-content:center;font-size:1.5rem;">✅</div>
                        <div>
                            <h3 style="margin:0;color:var(--carrier-blue);font-size:1.2rem;font-weight:800;">Finalizar Actividad</h3>
                            <p style="margin:2px 0 0;font-size:0.82rem;color:#6b7280;">Agrega evidencia fotográfica y un comentario antes de cerrar esta tarea.</p>
                        </div>
                    </div>
                    <hr style="border:none;border-top:1px solid #e5e7eb;margin:18px 0;">

                    <label style="font-size:0.85rem;font-weight:700;color:var(--carrier-blue);display:block;margin-bottom:6px;">📸 Evidencia fotográfica o de video</label>
                    ${fotosPrevias > 0 ? `<p style="font-size:0.8rem;color:#16a34a;margin:0 0 8px;">✔ Ya tienes ${fotosPrevias} archivo(s) guardado(s) para esta actividad. Puedes agregar más o continuar.</p>` : ''}
                    <input type="file" id="fotosFinalizarInput" multiple accept="image/*,video/*" style="width:100%;margin-bottom:8px;">
                    <p style="font-size:0.75rem;color:#9ca3af;margin:0 0 8px;">Videos hasta 80MB por archivo.</p>
                    <div id="previewFotosFinalizar" style="display:flex; flex-wrap:wrap; gap:8px; margin-bottom:8px;"></div>
                    <div id="compressInfoFinalizar" style="font-size:12px;color:#666;margin-bottom:8px;"></div>

                    <label style="font-size:0.85rem;font-weight:700;color:var(--carrier-blue);display:block;margin-bottom:6px;">📝 Comentario del técnico</label>
                    <textarea id="comentarioTexto" rows="4" placeholder="Describe brevemente el trabajo realizado, observaciones, etc." style="width:100%;border:1.5px solid #d1d5db;border-radius:12px;padding:12px;font-size:0.95rem;resize:vertical;font-family:inherit;transition:border-color 0.2s;"></textarea>
                    ${esTicket ? `
                    <label style="font-size:0.85rem;font-weight:700;color:var(--carrier-blue);display:block;margin:14px 0 6px;">📎 Adjuntar reporte del ticket (Word o PDF) — opcional</label>
                    <input type="file" id="reporteTicketArchivo" accept=".pdf,.doc,.docx,application/pdf,application/msword,application/vnd.openxmlformats-officedocument.wordprocessingml.document" style="width:100%;border:1.5px solid #d1d5db;border-radius:12px;padding:10px;font-size:0.88rem;font-family:inherit;">
                    <p style="margin:4px 0 0;font-size:0.78rem;color:#6b7280;">Formatos permitidos: .pdf, .doc, .docx — máx. 20 MB. Este archivo solo aplica para tickets.</p>
                    ` : ''}
                    <p id="comentarioError" style="color:var(--carrier-danger);font-size:0.82rem;min-height:18px;margin:4px 0 12px;"></p>
                    <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;">
                        <button onclick="document.getElementById('modalFinalizar').remove()" style="background:#f1f5f9;color:#374151;border:none;border-radius:10px;padding:13px;font-weight:600;font-size:0.95rem;cursor:pointer;">✖ Cancelar</button>
                        <button id="btnConfirmarFinalizar" onclick="confirmarFinalizar(${id})" style="background:linear-gradient(135deg,#16a34a,#15803d);color:white;border:none;border-radius:10px;padding:13px;font-weight:700;font-size:0.95rem;cursor:pointer;">✅ Confirmar y Finalizar</button>
                    </div>
                </div>
                <style>@keyframes fadeInM{from{opacity:0;transform:scale(0.95)}to{opacity:1;transform:scale(1)}}</style>`;
            document.body.appendChild(modal);

            document.getElementById('fotosFinalizarInput').addEventListener('change', e => {
                const files = Array.from(e.target.files).slice(0, 100);
                const previewDiv = document.getElementById('previewFotosFinalizar');
                previewDiv.innerHTML = '';
                let totalKB = 0;
                let nFotos = 0, nVideos = 0;
                files.forEach(f => {
                    totalKB += f.size / 1024;
                    const esVideo = f.type.startsWith('video/') || /\.(mp4|mov|webm|m4v|3gp|avi|mkv)$/i.test(f.name);
                    if (esVideo) {
                        nVideos++;
                        const wrap = document.createElement('div');
                        wrap.style.cssText = 'width:70px;height:70px;border-radius:8px;background:#111827;display:flex;align-items:center;justify-content:center;position:relative;';
                        wrap.innerHTML = '<span style="font-size:22px;">🎬</span>';
                        previewDiv.appendChild(wrap);
                    } else {
                        nFotos++;
                        const r = new FileReader();
                        r.onload = ev => {
                            const img = document.createElement('img');
                            img.src = ev.target.result;
                            img.style.cssText = 'width:70px;height:70px;object-fit:cover;border-radius:8px;';
                            previewDiv.appendChild(img);
                        };
                        r.readAsDataURL(f);
                    }
                });
                const partes = [];
                if (nFotos)  partes.push(`${nFotos} foto(s)`);
                if (nVideos) partes.push(`${nVideos} video(s)`);
                document.getElementById('compressInfoFinalizar').textContent =
                    files.length ? `${partes.join(' · ')} · ${(totalKB/1024).toFixed(1)} MB` : '';
            });

            setTimeout(() => document.getElementById('comentarioTexto').focus(), 100);
        }

        async function confirmarFinalizar(id) {
            const comentario = document.getElementById('comentarioTexto').value.trim();
            const errorEl   = document.getElementById('comentarioError');
            if (!comentario) { errorEl.textContent = 'El comentario no puede estar vacío.'; return; }

            const modal = document.getElementById('modalFinalizar');
            const unidad = modal.dataset.unidad;
            const fotosPrevias = parseInt(modal.dataset.fotosPrevias, 10) || 0;
            const esTicket = modal.dataset.esTicket === '1';
            const ticketId = modal.dataset.ticketId;
            const input = document.getElementById('fotosFinalizarInput');
            const archivosNuevos = input && input.files ? Array.from(input.files) : [];

            // Reporte adjunto (solo tickets) — opcional, PDF o Word
            let reporteArchivo = null;
            if (esTicket) {
                const reporteInput = document.getElementById('reporteTicketArchivo');
                reporteArchivo = reporteInput && reporteInput.files ? reporteInput.files[0] : null;
                if (reporteArchivo) {
                    const extPermitidas = ['pdf', 'doc', 'docx'];
                    const ext = reporteArchivo.name.split('.').pop().toLowerCase();
                    if (!extPermitidas.includes(ext)) { errorEl.textContent = 'El reporte del ticket debe ser PDF o Word (.pdf, .doc, .docx).'; return; }
                    if (reporteArchivo.size > 20 * 1024 * 1024) { errorEl.textContent = 'El reporte del ticket no debe superar 20 MB.'; return; }
                }
            }

            if (fotosPrevias === 0 && archivosNuevos.length === 0) {
                errorEl.textContent = 'Debes agregar al menos una foto de evidencia de tu trabajo.';
                return;
            }

            const btn = document.getElementById('btnConfirmarFinalizar');
            btn.disabled = true;

            // 1) Subir evidencia (si hay archivos nuevos), vinculada a esta actividad exacta
            if (archivosNuevos.length > 0) {
                const MAX_VIDEO_MB = 80;
                const videoDemasiadoGrande = archivosNuevos.find(f => {
                    const esVideo = f.type.startsWith('video/') || /\.(mp4|mov|webm|m4v|3gp|avi|mkv)$/i.test(f.name);
                    return esVideo && f.size > MAX_VIDEO_MB * 1024 * 1024;
                });
                if (videoDemasiadoGrande) {
                    errorEl.textContent = `El video "${videoDemasiadoGrande.name}" pesa más de ${MAX_VIDEO_MB}MB. Comprímelo o recorta la duración antes de subirlo.`;
                    btn.disabled = false;
                    return;
                }

                btn.textContent = '⏳ Preparando archivos...';
                const procesados = await Promise.all(archivosNuevos.map(f => {
                    const esVideo = f.type.startsWith('video/') || /\.(mp4|mov|webm|m4v|3gp|avi|mkv)$/i.test(f.name);
                    return esVideo ? Promise.resolve(f) : _comprimirImagenCanvas(f);
                }));
                btn.textContent = '📤 Subiendo evidencia...';
                const fd = new FormData();
                fd.append('unidad', unidad);
                fd.append('tecnico', username);
                fd.append('asignacion_id', id);
                procesados.forEach(f => fd.append('files', f));
                let upRes;
                try {
                    upRes = await fetchAuth('/api/evidencias/upload', { method: 'POST', body: fd });
                } catch (netErr) {
                    errorEl.textContent = 'No se pudo conectar con el servidor. Verifica tu conexión e intenta de nuevo.';
                    btn.textContent = '✅ Confirmar y Finalizar'; btn.disabled = false;
                    return;
                }
                if (!upRes.ok) {
                    const rawText = await upRes.text().catch(()=> '');
                    let detail = '';
                    try { detail = JSON.parse(rawText).detail; } catch(e) {}
                    errorEl.textContent = detail || `No se pudieron subir las fotos (error ${upRes.status}). Intenta de nuevo.`;
                    btn.textContent = '✅ Confirmar y Finalizar'; btn.disabled = false;
                    return;
                }
            }

            // 2) Cerrar la actividad con el comentario
            btn.textContent = 'Guardando...';
            let res;
            if (esTicket && ticketId) {
                // Los tickets se cierran vía /api/tickets (marca atendido + reporte,
                // y esto a su vez cierra la asignación vinculada automáticamente).
                await fetchAuth('/api/tickets/' + ticketId + '/atender', { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ atendido: true }) });
                const fdReporte = new FormData();
                fdReporte.append('reporte', comentario);
                if (reporteArchivo) fdReporte.append('archivo', reporteArchivo);
                res = await fetchAuth('/api/tickets/' + ticketId + '/report', { method: 'PUT', body: fdReporte });
            } else {
                res = await fetchAuth('/api/asignaciones/' + id + '/finalizar', { method: 'PATCH', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ comentario }) });
            }
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
        function toggleSerieNA(i) {
            const modelSel = document.getElementById('serie_model_' + i);
            const input = document.getElementById('serie_' + i);
            if (modelSel.value === 'N/A') { input.value = 'N/A'; input.disabled = true; }
            else { if (input.value === 'N/A') input.value = ''; input.disabled = false; }
        }
        async function tomarSeries(tareaId) {
            const camposSeries = [
                { key: 'vin_number', label: 'VIN Number' },{ key: 'reefer_serial', label: 'Serie del Reefer' },{ key: 'reefer_model', label: 'Modelo del Reefer' },
                { key: 'evaporator_serial_mjs11', label: 'Evaporador 1', na: true, modelKey: 'evaporator_model_1' },
                { key: 'evaporator_serial_mjd22', label: 'Evaporador 2', na: true, modelKey: 'evaporator_model_2' },
                { key: 'engine_serial', label: 'Motor' },{ key: 'compressor_serial', label: 'Compresor' },{ key: 'generator_serial', label: 'Generador' },
                { key: 'battery_charger_serial', label: 'Cargador de Batería' }
            ];
            const opcionesEvap = ['','MJD 1100','MJS 1100','MJD 2200','MJS 2200','N/A']
                .map(o => `<option value="${o}">${o || 'Modelo'}</option>`).join('');
            let inputs = camposSeries.map((c,i) => c.na
                ? `<div style="display:flex; gap:6px; align-items:center; margin-bottom:4px;">
                     <select id="serie_model_${i}" style="width:120px; flex-shrink:0;" onchange="toggleSerieNA(${i})" data-modelkey="${c.modelKey}">${opcionesEvap}</select>
                     <input type="text" id="serie_${i}" placeholder="${c.label}: Nº de serie" style="flex:1;">
                     <input type="hidden" id="serie_key_${i}" value="${c.key}">
                   </div>`
                : `<input type="text" id="serie_${i}" placeholder="${c.label}"><input type="hidden" id="serie_key_${i}" value="${c.key}">`
            ).join('');
            const modal = mostrarModal(`<div class="modal-content"><h3>🔢 Toma de Series</h3><div id="camposSeries">${inputs}</div><button class="btn-primary" id="btnGuardarSeries">💾 Guardar Series</button><button class="btn-danger" onclick="cerrarModal()">Cancelar</button></div>`);
            document.getElementById('btnGuardarSeries').onclick = async () => {
                const tareasRes = await fetchAuth('/api/asignaciones/?tecnico=' + username + '&estado=en_proceso'); const tareas = await tareasRes.json();
                const tarea = Array.isArray(tareas) ? tareas.find(t => t.id == tareaId) : null; if (!tarea) return alert('Tarea no encontrada');
                const keys = [...document.querySelectorAll('[id^="serie_key_"]')].map(el => el.value); const values = { unit_number: tarea.unidad };
                keys.forEach((key,i) => values[key] = document.getElementById('serie_'+i).value);
                document.querySelectorAll('select[data-modelkey]').forEach(sel => { values[sel.dataset.modelkey] = sel.value; });
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
            document.getElementById('actividad').innerHTML = '<option value="">Actividad</option>' + ['Cableado','Programación','Soldadura','Check de fugas','Vacío','Cerrado','Pre-viaje','Horas Corridas','Standby','GPS','Corriendo','Inspección','Accesorios','Toma de Valores','Evidencia','Toma de Series','Extra Eléctrico','Extra Soldador'].map(a => `<option value="${a}">${a}</option>`).join('');
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
                                    ${t.reporte_archivo_url ? `<p style="margin:8px 0 0;"><a href="${t.reporte_archivo_url}" target="_blank" style="color:var(--carrier-blue);font-weight:600;">📎 Ver reporte adjunto</a></p>` : ''}
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
                    <label style="font-size:0.85rem;font-weight:700;color:var(--carrier-blue);display:block;margin:14px 0 6px;">📎 Adjuntar reporte (Word o PDF) — opcional</label>
                    <input type="file" id="reporteArchivo" accept=".pdf,.doc,.docx,application/pdf,application/msword,application/vnd.openxmlformats-officedocument.wordprocessingml.document" style="width:100%;border:1.5px solid #d1d5db;border-radius:12px;padding:10px;font-size:0.88rem;font-family:inherit;">
                    <p style="margin:4px 0 0;font-size:0.78rem;color:#6b7280;">Formatos permitidos: .pdf, .doc, .docx — máx. 20 MB</p>
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

            const fileInput = document.getElementById('reporteArchivo');
            const archivo = fileInput.files[0];
            if (archivo) {
                const extPermitidas = ['pdf', 'doc', 'docx'];
                const ext = archivo.name.split('.').pop().toLowerCase();
                if (!extPermitidas.includes(ext)) { errorEl.textContent = 'El archivo debe ser PDF o Word (.pdf, .doc, .docx).'; return; }
                if (archivo.size > 20 * 1024 * 1024) { errorEl.textContent = 'El archivo no debe superar 20 MB.'; return; }
            }

            const btn = document.getElementById('btnEnviarReporte');
            btn.textContent = 'Enviando...'; btn.disabled = true;

            const formData = new FormData();
            formData.append('reporte', reporte);
            if (archivo) formData.append('archivo', archivo);

            const res = await fetchAuth('/api/tickets/' + id + '/report', { method: 'PUT', body: formData });
            if (res.ok) {
                document.getElementById('modalReporte').remove();
                const toast = document.createElement('div');
                toast.style.cssText = 'position:fixed;bottom:28px;left:50%;transform:translateX(-50%);background:#16a34a;color:white;padding:14px 28px;border-radius:50px;font-weight:700;font-size:0.95rem;box-shadow:0 4px 20px rgba(0,0,0,0.2);z-index:600;';
                toast.textContent = '✅ Reporte enviado. Ticket completado.';
                document.body.appendChild(toast);
                setTimeout(() => toast.remove(), 3000);
                cargarTickets();
            } else {
                const err = await res.json().catch(() => ({}));
                errorEl.textContent = err.detail || 'Error al enviar el reporte. Intenta de nuevo.';
                btn.textContent = '📤 Enviar y Cerrar Ticket'; btn.disabled = false;
            }
        }

        cargarTickets();
    </script>
    """
    return HTMLResponse(content=pagina_con_menu("🎫 Mis Tickets", contenido, "mis-tickets"))

# ------------------------------------------------------------
# JUEGOS (sección de descanso para técnicos: memoria, 2048, trivia)
# ------------------------------------------------------------
@router.get("/app/juegos", response_class=HTMLResponse)
async def pagina_juegos():
    contenido = """
    <style>
        .juegos-tabs { display:flex; gap:10px; margin-bottom:20px; flex-wrap:wrap; }
        .juegos-tab { padding:10px 20px; border-radius:10px; border:none; background:#eef2f7; color:var(--carrier-blue); font-weight:700; cursor:pointer; font-size:0.9rem; }
        .juegos-tab.active { background:var(--carrier-blue); color:white; }
        .juegos-layout { display:grid; grid-template-columns:1fr 260px; gap:20px; align-items:start; }
        @media (max-width:800px) { .juegos-layout { grid-template-columns:1fr; } }
        .juegos-card { background:white; border-radius:16px; padding:20px; box-shadow:0 2px 10px rgba(0,0,0,0.06); }
        .memoria-grid { display:grid; grid-template-columns:repeat(4,1fr); gap:10px; max-width:420px; margin:0 auto; }
        .memoria-celda { aspect-ratio:1; background:var(--carrier-blue); border-radius:10px; display:flex; align-items:center; justify-content:center; font-size:1.8rem; cursor:pointer; user-select:none; transition:transform .15s; }
        .memoria-celda.volteada, .memoria-celda.encontrada { background:#eef2f7; }
        .memoria-celda.encontrada { opacity:0.55; cursor:default; }
        .juegos-stats { display:flex; gap:18px; justify-content:center; margin-bottom:14px; font-weight:700; color:var(--carrier-blue); flex-wrap:wrap; }
        .g2048-grid { display:grid; grid-template-columns:repeat(4,1fr); gap:8px; max-width:340px; margin:0 auto; background:#cbd5e1; padding:8px; border-radius:12px; }
        .g2048-celda { aspect-ratio:1; background:#e2e8f0; border-radius:8px; display:flex; align-items:center; justify-content:center; font-weight:800; font-size:1.3rem; color:#334155; }
        .g2048-controles { display:grid; grid-template-columns:repeat(3,50px); grid-template-rows:repeat(2,44px); gap:6px; justify-content:center; margin-top:14px; }
        .g2048-btn { background:var(--carrier-blue); color:white; border:none; border-radius:8px; font-size:1.1rem; cursor:pointer; }
        .trivia-opcion { display:block; width:100%; text-align:left; padding:12px 16px; margin:8px 0; border-radius:10px; border:1.5px solid #d8dee6; background:white; cursor:pointer; font-size:0.95rem; }
        .trivia-opcion:hover { border-color:var(--carrier-blue); }
        .trivia-opcion.correcta { background:#dcfce7; border-color:#16a34a; }
        .trivia-opcion.incorrecta { background:#fee2e2; border-color:#dc2626; }
        .leaderboard-fila { display:flex; justify-content:space-between; padding:6px 0; border-bottom:1px solid #f1f5f9; font-size:0.85rem; }
        .leaderboard-fila:first-child { font-weight:800; color:#b45309; }
        .gatito-grid { display:grid; grid-template-columns:repeat(3,1fr); gap:8px; max-width:300px; margin:0 auto; }
        .gatito-celda { aspect-ratio:1; background:#eef2f7; border-radius:10px; display:flex; align-items:center; justify-content:center; font-size:2.2rem; font-weight:800; cursor:pointer; }
        .gatito-celda.ocupada { cursor:default; }
        .juegos-canvas { display:block; margin:0 auto; background:#0f172a; border-radius:12px; touch-action:none; }
        .carta-vista { display:inline-flex; align-items:center; justify-content:center; width:52px; height:74px; background:white; border:2px solid #334155; border-radius:8px; font-weight:800; font-size:1.1rem; margin:4px; }
        .carta-roja { color:#dc2626; }
        .carta-negra { color:#0f172a; }
        .juegos-controles-touch { display:flex; gap:10px; justify-content:center; margin-top:12px; }
        .juegos-controles-touch button { flex:1; max-width:110px; padding:14px 0; border-radius:12px; border:none; background:var(--carrier-blue); color:white; font-size:1.3rem; cursor:pointer; user-select:none; }
        .pelea-arena { display:flex; justify-content:space-between; align-items:flex-end; max-width:420px; margin:0 auto 16px; }
        .pelea-personaje { font-size:4.5rem; transition:transform .15s; }
        .pelea-personaje.golpea { transform:translateX(14px) scale(1.08); }
        .pelea-personaje.cpu.golpea { transform:translateX(-14px) scale(1.08); }
        .pelea-personaje.bloquea { filter: drop-shadow(0 0 8px #3b82f6); }
        .pelea-personaje.dañado { filter: drop-shadow(0 0 8px #dc2626); }
        .pelea-barras { max-width:420px; margin:0 auto 14px; }
        .pelea-barra-fila { display:flex; align-items:center; gap:8px; margin:6px 0; font-size:.8rem; font-weight:700; color:var(--carrier-blue); }
        .pelea-barra-fondo { flex:1; height:16px; background:#e2e8f0; border-radius:8px; overflow:hidden; }
        .pelea-barra-relleno { height:100%; background:linear-gradient(90deg,#16a34a,#4ade80); transition:width .2s; }
        .pelea-barra-relleno.cpu { background:linear-gradient(90deg,#dc2626,#f87171); }
        .pelea-botones { display:flex; gap:10px; justify-content:center; flex-wrap:wrap; max-width:420px; margin:0 auto; }
        .pelea-botones button { flex:1; min-width:100px; padding:12px 8px; border-radius:10px; border:none; background:var(--carrier-blue); color:white; font-weight:700; cursor:pointer; font-size:.9rem; }
        .pelea-botones button:disabled { opacity:.4; cursor:not-allowed; }
        .pelea-botones button.btn-bloquear { background:#3b82f6; }
        .pelea-rondas { text-align:center; font-size:.85rem; color:#64748b; margin-bottom:8px; }
    </style>

    <div class="juegos-tabs">
        <button class="juegos-tab active" id="tab-memoria" onclick="cambiarJuego('memoria')">🧠 Memoria</button>
        <button class="juegos-tab" id="tab-2048" onclick="cambiarJuego('2048')">🔢 2048</button>
        <button class="juegos-tab" id="tab-trivia" onclick="cambiarJuego('trivia')">❄️ Trivia Refrigeración</button>
        <button class="juegos-tab" id="tab-gatito" onclick="cambiarJuego('gatito')">❌⭕ Gatito</button>
        <button class="juegos-tab" id="tab-culebra" onclick="cambiarJuego('culebra')">🐍 Culebra</button>
        <button class="juegos-tab" id="tab-billar" onclick="cambiarJuego('billar')">🎱 Billar</button>
        <button class="juegos-tab" id="tab-cartas" onclick="cambiarJuego('cartas')">🃏 21 (Cartas)</button>
        <button class="juegos-tab" id="tab-mario" onclick="cambiarJuego('mario')">🏃 Súper Técnico</button>
        <button class="juegos-tab" id="tab-carreras" onclick="cambiarJuego('carreras')">🏎️ Carreras</button>
        <button class="juegos-tab" id="tab-pelea" onclick="cambiarJuego('pelea')">🥊 Pelea</button>
        <button class="juegos-tab" id="tab-tetris" onclick="cambiarJuego('tetris')">🧩 Tetris</button>
        <button class="juegos-tab" id="tab-simulador" onclick="cambiarJuego('simulador')">🌡️ Simulador de Refrigeración</button>
    </div>

    <div class="juegos-layout">
        <div class="juegos-card" id="juego-contenedor"></div>
        <div class="juegos-card">
            <h4 style="margin:0 0 10px;color:var(--carrier-blue);">🏆 Top 10</h4>
            <div id="leaderboard-body"><p style="color:#94a3b8;font-size:.85rem;">Cargando...</p></div>
            <p style="margin-top:14px;font-size:.8rem;color:#94a3b8;">Tu mejor puntaje: <b id="mi-mejor">–</b></p>
        </div>
    </div>

    <script>
        const fetchAuth = window.fetchAuth;
        const LISTA_JUEGOS = ['memoria','2048','trivia','gatito','culebra','billar','cartas','mario','carreras','pelea','tetris','simulador'];
        let juegoActual = 'memoria';

        // ══════════════ PERSONAJE Y GRÁFICOS COMPARTIDOS (homologados en todos los juegos) ══════════════
        // Dibuja al técnico protagonista con un estilo vectorial consistente en todos los juegos con canvas.
        function dibujarTecnico(ctx, x, yBase, escala, opts) {
            opts = opts || {};
            const dir = opts.dir || 1;               // 1 = mira a la derecha, -1 = mira a la izquierda
            const pose = opts.pose || 'parado';       // parado | correr | salto | golpe | patada | bloqueo | dañado
            const frame = opts.frame || 0;            // 0/1 alterna piernas al correr
            const colorTraje = opts.color || '#1d4ed8';
            const golpeando = pose === 'golpe' || pose === 'patada';
            ctx.save();
            ctx.translate(x, yBase);
            ctx.scale(dir * escala, escala);
            if (opts.dañado) { ctx.filter = 'drop-shadow(0 0 6px #dc2626)'; }
            else if (pose === 'bloqueo') { ctx.filter = 'drop-shadow(0 0 6px #3b82f6)'; }
            // sombra de contacto
            ctx.fillStyle = 'rgba(15,23,42,0.18)';
            ctx.beginPath(); ctx.ellipse(0, 3, 14, 4, 0, 0, Math.PI * 2); ctx.fill();
            // piernas
            let p1 = 0, p2 = 0;
            if (pose === 'correr') { p1 = frame ? 9 : -9; p2 = -p1; }
            else if (pose === 'salto') { p1 = -7; p2 = 5; }
            else if (pose === 'patada') { p1 = 18; p2 = -5; }
            ctx.strokeStyle = '#1e293b'; ctx.lineWidth = 7; ctx.lineCap = 'round';
            ctx.beginPath(); ctx.moveTo(-3, -6); ctx.lineTo(-3 + p1 * 0.55, -26 + Math.abs(p1) * 0.18); ctx.stroke();
            ctx.beginPath(); ctx.moveTo(3, -6); ctx.lineTo(3 + p2 * 0.55, -26 + Math.abs(p2) * 0.18); ctx.stroke();
            ctx.fillStyle = '#111827';
            [[-3 + p1 * 0.55, -26 + Math.abs(p1) * 0.18], [3 + p2 * 0.55, -26 + Math.abs(p2) * 0.18]].forEach(([bx, by]) => {
                ctx.beginPath(); ctx.ellipse(bx, by, 5, 3, 0, 0, Math.PI * 2); ctx.fill();
            });
            // torso con franja reflectante
            ctx.fillStyle = colorTraje;
            _tecRoundRect(ctx, -11, -50, 22, 26, 6); ctx.fill();
            ctx.fillStyle = '#fbbf24';
            ctx.fillRect(-11, -40, 22, 4);
            ctx.fillStyle = '#e2e8f0';
            ctx.beginPath(); ctx.arc(0, -44, 2.6, 0, Math.PI * 2); ctx.fill();
            // brazos
            let brazoAtras = { x: -6, y: -18 }, brazoAdelante = { x: 12, y: -32 };
            if (pose === 'golpe') brazoAdelante = { x: 23, y: -42 };
            else if (pose === 'bloqueo') brazoAdelante = { x: 9, y: -48 };
            else if (pose === 'salto') brazoAdelante = { x: 9, y: -52 };
            else if (pose === 'patada') brazoAdelante = { x: 4, y: -46 };
            ctx.strokeStyle = colorTraje; ctx.lineWidth = 6.5;
            ctx.beginPath(); ctx.moveTo(-8, -46); ctx.lineTo(brazoAtras.x, brazoAtras.y); ctx.stroke();
            ctx.beginPath(); ctx.moveTo(8, -46); ctx.lineTo(brazoAdelante.x, brazoAdelante.y); ctx.stroke();
            ctx.fillStyle = '#f8fafc';
            ctx.beginPath(); ctx.arc(brazoAdelante.x, brazoAdelante.y, golpeando ? 4.6 : 4, 0, Math.PI * 2); ctx.fill();
            // cabeza y casco
            ctx.fillStyle = '#f1c27d';
            ctx.beginPath(); ctx.arc(0, -58, 8, 0, Math.PI * 2); ctx.fill();
            ctx.fillStyle = opts.colorCasco || '#f59e0b';
            ctx.beginPath(); ctx.arc(0, -62, 9, Math.PI, 0); ctx.fill();
            ctx.fillRect(-10, -62, 20, 3);
            ctx.restore();
        }
        // Dibuja el vehículo del técnico (furgón/carrito de servicio) para el juego de Carreras.
        function dibujarVehiculo(ctx, cx, cyBase, ancho, alto, color, opts) {
            opts = opts || {};
            ctx.save();
            ctx.translate(cx, cyBase);
            if (opts.inclinacion) ctx.rotate(opts.inclinacion);
            ctx.fillStyle = 'rgba(15,23,42,0.25)';
            ctx.beginPath(); ctx.ellipse(0, 6, ancho * 0.52, 6, 0, 0, Math.PI * 2); ctx.fill();
            ctx.fillStyle = color;
            _tecRoundRect(ctx, -ancho / 2, -alto, ancho, alto, 10); ctx.fill();
            ctx.fillStyle = 'rgba(226,240,253,0.9)';
            _tecRoundRect(ctx, -ancho / 2 + 6, -alto + 8, ancho - 12, alto * 0.38, 6); ctx.fill();
            ctx.fillStyle = opts.franja || '#fbbf24';
            ctx.fillRect(-ancho / 2, -alto * 0.32, ancho, 5);
            if (opts.conductor) {
                ctx.fillStyle = '#f1c27d';
                ctx.beginPath(); ctx.arc(0, -alto + 15, 6, 0, Math.PI * 2); ctx.fill();
                ctx.fillStyle = '#f59e0b';
                ctx.beginPath(); ctx.arc(0, -alto + 11, 6.5, Math.PI, 0); ctx.fill();
            }
            ctx.fillStyle = '#1f2937';
            ctx.beginPath(); ctx.arc(-ancho / 2 + 7, 1, 6.5, 0, Math.PI * 2); ctx.fill();
            ctx.beginPath(); ctx.arc(ancho / 2 - 7, 1, 6.5, 0, Math.PI * 2); ctx.fill();
            ctx.fillStyle = '#475569';
            ctx.beginPath(); ctx.arc(-ancho / 2 + 7, 1, 2.6, 0, Math.PI * 2); ctx.fill();
            ctx.beginPath(); ctx.arc(ancho / 2 - 7, 1, 2.6, 0, Math.PI * 2); ctx.fill();
            ctx.restore();
        }
        function _tecRoundRect(ctx, x, y, w, h, r) {
            if (ctx.roundRect) { ctx.beginPath(); ctx.roundRect(x, y, w, h, r); return; }
            ctx.beginPath();
            ctx.moveTo(x + r, y);
            ctx.arcTo(x + w, y, x + w, y + h, r);
            ctx.arcTo(x + w, y + h, x, y + h, r);
            ctx.arcTo(x, y + h, x, y, r);
            ctx.arcTo(x, y, x + w, y, r);
            ctx.closePath();
        }

        async function cambiarJuego(juego) {
            juegoActual = juego;
            LISTA_JUEGOS.forEach(j => document.getElementById('tab-'+j).classList.toggle('active', j===juego));
            pararBucleActivo();
            if (juego === 'memoria') iniciarMemoria();
            else if (juego === '2048') iniciar2048();
            else if (juego === 'trivia') iniciarTrivia();
            else if (juego === 'gatito') iniciarGatito();
            else if (juego === 'culebra') iniciarCulebra();
            else if (juego === 'billar') iniciarBillar();
            else if (juego === 'cartas') iniciarCartas();
            else if (juego === 'mario') iniciarMario();
            else if (juego === 'carreras') iniciarCarreras();
            else if (juego === 'pelea') iniciarPelea();
            else if (juego === 'tetris') iniciarTetris();
            else mostrarSimuladorExterno();
            cargarLeaderboard();
        }

        // Controla que solo un requestAnimationFrame/interval esté activo a la vez
        let _rafActivo = null;
        let _intervalosActivos = [];
        function pararBucleActivo() {
            if (_rafActivo) { cancelAnimationFrame(_rafActivo); _rafActivo = null; }
            _intervalosActivos.forEach(id => clearInterval(id));
            _intervalosActivos = [];
            document.removeEventListener('keydown', manejarTecla2048);
            document.removeEventListener('keydown', _marioTeclaDown);
            document.removeEventListener('keyup', _marioTeclaUp);
            document.removeEventListener('keydown', _carrerasTecla);
            document.removeEventListener('keyup', _carrerasTeclaUp);
            document.removeEventListener('keydown', _tetrisTeclaDown);
        }

        function mostrarSimuladorExterno() {
            const cont = document.getElementById('juego-contenedor');
            cont.innerHTML = `
                <h3 style="margin-top:0;color:var(--carrier-blue);">🌡️ Simulador de Ciclo de Refrigeración</h3>
                <p style="color:#475569;">Simulador gratuito y externo (MechSimulator) del ciclo de compresión de vapor: animación del compresor, condensador, válvula de expansión y evaporador, diagrama P-h en tiempo real, cálculo de COP, comparación de refrigerantes (R-134a, R-410A, R-22, R-290) y hasta su propio modo de trivia/quiz.</p>
                <p style="color:#94a3b8;font-size:.85rem;">Se abre en una pestaña nueva — es un sitio externo, no forma parte de esta app.</p>
                <p style="text-align:center;margin-top:18px;">
                    <a href="https://mechsimulator.com/tools/refrigeration-cycle/" target="_blank" rel="noopener noreferrer" class="btn-primary" style="display:inline-block;width:auto;padding:12px 24px;text-decoration:none;">🔗 Abrir simulador de refrigeración</a>
                </p>
            `;
        }

        async function guardarPuntaje(juego, puntaje) {
            try {
                await fetchAuth('/api/juegos/puntajes', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ juego, puntaje })
                });
            } catch(e) { console.error('guardarPuntaje', e); }
            cargarLeaderboard();
        }

        async function cargarLeaderboard() {
            const body = document.getElementById('leaderboard-body');
            const mejorEl = document.getElementById('mi-mejor');
            if (juegoActual === 'simulador') {
                body.innerHTML = '<p style="color:#94a3b8;font-size:.85rem;">Este simulador es externo y no tiene puntajes.</p>';
                mejorEl.textContent = '–';
                return;
            }
            try {
                const [resTop, resMio] = await Promise.all([
                    fetchAuth('/api/juegos/puntajes/' + juegoActual),
                    fetchAuth('/api/juegos/mi-mejor/' + juegoActual)
                ]);
                const top = resTop.ok ? await resTop.json() : [];
                const mio = resMio.ok ? await resMio.json() : { mejor: 0 };
                body.innerHTML = top.length
                    ? top.map((r,i) => `<div class="leaderboard-fila"><span>${i+1}. ${r.nombre}</span><span>${r.puntaje}</span></div>`).join('')
                    : '<p style="color:#94a3b8;font-size:.85rem;">Aún no hay puntajes. ¡Sé el primero!</p>';
                mejorEl.textContent = mio.mejor || 0;
            } catch(e) { console.error('cargarLeaderboard', e); }
        }

        // ══════════════ MEMORIA ══════════════
        let memEstado = null;
        function iniciarMemoria() {
            const emojis = ['❄️','🔧','🚛','⚙️','🔋','🌡️','📦','🛠️'];
            const cartas = [...emojis, ...emojis].sort(() => Math.random() - 0.5);
            memEstado = { cartas, volteadas: [], encontradas: new Set(), movimientos: 0, segundos: 0, activo: true };
            if (memEstado.timer) clearInterval(memEstado.timer);
            memEstado.timer = setInterval(() => { if (memEstado.activo) { memEstado.segundos++; renderMemoriaStats(); } }, 1000);
            renderMemoria();
        }
        function renderMemoriaStats() {
            const el = document.getElementById('mem-stats');
            if (el) el.innerHTML = `<span>🔁 Movimientos: ${memEstado.movimientos}</span><span>⏱ ${memEstado.segundos}s</span>`;
        }
        function renderMemoria() {
            const cont = document.getElementById('juego-contenedor');
            cont.innerHTML = `
                <h3 style="margin-top:0;color:var(--carrier-blue);">🧠 Memoria</h3>
                <div class="juegos-stats" id="mem-stats"></div>
                <div class="memoria-grid" id="mem-grid"></div>
                <p style="text-align:center;margin-top:14px;"><button class="btn-primary" style="width:auto;padding:8px 18px;" onclick="iniciarMemoria()">🔄 Reiniciar</button></p>
            `;
            renderMemoriaStats();
            const grid = document.getElementById('mem-grid');
            grid.innerHTML = memEstado.cartas.map((_, i) => `<div class="memoria-celda" id="mem-c${i}" onclick="voltearCarta(${i})">❓</div>`).join('');
        }
        function voltearCarta(i) {
            const st = memEstado;
            if (!st.activo || st.volteadas.includes(i) || st.encontradas.has(i) || st.volteadas.length === 2) return;
            st.volteadas.push(i);
            const celda = document.getElementById('mem-c'+i);
            celda.textContent = st.cartas[i];
            celda.classList.add('volteada');
            if (st.volteadas.length === 2) {
                st.movimientos++;
                renderMemoriaStats();
                const [a, b] = st.volteadas;
                if (st.cartas[a] === st.cartas[b]) {
                    st.encontradas.add(a); st.encontradas.add(b);
                    document.getElementById('mem-c'+a).classList.add('encontrada');
                    document.getElementById('mem-c'+b).classList.add('encontrada');
                    st.volteadas = [];
                    if (st.encontradas.size === st.cartas.length) {
                        st.activo = false;
                        clearInterval(st.timer);
                        const puntaje = Math.max(0, 1000 - st.movimientos*15 - st.segundos*3);
                        setTimeout(() => {
                            alert(`🎉 ¡Completado! Movimientos: ${st.movimientos}, Tiempo: ${st.segundos}s, Puntaje: ${puntaje}`);
                            guardarPuntaje('memoria', puntaje);
                        }, 200);
                    }
                } else {
                    setTimeout(() => {
                        document.getElementById('mem-c'+a).textContent = '❓';
                        document.getElementById('mem-c'+b).textContent = '❓';
                        document.getElementById('mem-c'+a).classList.remove('volteada');
                        document.getElementById('mem-c'+b).classList.remove('volteada');
                        st.volteadas = [];
                    }, 700);
                }
            }
        }

        // ══════════════ 2048 ══════════════
        let g2048 = null;
        function iniciar2048() {
            g2048 = { grid: Array.from({length:4}, () => Array(4).fill(0)), puntaje: 0, terminado: false };
            agregarFicha2048(); agregarFicha2048();
            render2048();
            document.removeEventListener('keydown', manejarTecla2048);
            document.addEventListener('keydown', manejarTecla2048);
        }
        function agregarFicha2048() {
            const vacias = [];
            g2048.grid.forEach((fila, r) => fila.forEach((v, c) => { if (v === 0) vacias.push([r,c]); }));
            if (!vacias.length) return;
            const [r, c] = vacias[Math.floor(Math.random()*vacias.length)];
            g2048.grid[r][c] = Math.random() < 0.9 ? 2 : 4;
        }
        function render2048() {
            const cont = document.getElementById('juego-contenedor');
            cont.innerHTML = `
                <h3 style="margin-top:0;color:var(--carrier-blue);">🔢 2048</h3>
                <div class="juegos-stats"><span>⭐ Puntaje: <span id="g2048-puntaje">${g2048.puntaje}</span></span></div>
                <div class="g2048-grid" id="g2048-grid"></div>
                <div class="g2048-controles">
                    <span></span><button class="g2048-btn" onclick="mover2048('arriba')">↑</button><span></span>
                    <button class="g2048-btn" onclick="mover2048('izquierda')">←</button>
                    <button class="g2048-btn" onclick="mover2048('abajo')">↓</button>
                    <button class="g2048-btn" onclick="mover2048('derecha')">→</button>
                </div>
                <p style="text-align:center;margin-top:14px;"><button class="btn-primary" style="width:auto;padding:8px 18px;" onclick="iniciar2048()">🔄 Reiniciar</button></p>
            `;
            const colores = {0:'#e2e8f0',2:'#eef2f7',4:'#e0e7ff',8:'#c7d2fe',16:'#a5b4fc',32:'#818cf8',64:'#6366f1',128:'#fbbf24',256:'#f59e0b',512:'#ef4444',1024:'#dc2626',2048:'#16a34a'};
            document.getElementById('g2048-grid').innerHTML = g2048.grid.flat().map(v =>
                `<div class="g2048-celda" style="background:${colores[v]||'#16a34a'};color:${v<=4?'#334155':'white'};">${v||''}</div>`
            ).join('');
        }
        function manejarTecla2048(e) {
            const mapa = { ArrowUp:'arriba', ArrowDown:'abajo', ArrowLeft:'izquierda', ArrowRight:'derecha' };
            if (mapa[e.key]) { e.preventDefault(); mover2048(mapa[e.key]); }
        }
        function _comprimirFila(fila) {
            let vals = fila.filter(v => v !== 0);
            let sumaExtra = 0;
            for (let i = 0; i < vals.length - 1; i++) {
                if (vals[i] === vals[i+1]) { vals[i] *= 2; sumaExtra += vals[i]; vals[i+1] = 0; }
            }
            vals = vals.filter(v => v !== 0);
            while (vals.length < 4) vals.push(0);
            return { vals, sumaExtra };
        }
        function mover2048(dir) {
            if (!g2048 || g2048.terminado) return;
            let cambiado = false;
            let grid = g2048.grid.map(f => [...f]);
            for (let i = 0; i < 4; i++) {
                let linea;
                if (dir === 'izquierda') linea = grid[i];
                else if (dir === 'derecha') linea = [...grid[i]].reverse();
                else if (dir === 'arriba') linea = grid.map(f => f[i]);
                else linea = grid.map(f => f[i]).reverse();

                const { vals, sumaExtra } = _comprimirFila(linea);
                g2048.puntaje += sumaExtra;

                let finalLinea = (dir === 'derecha' || dir === 'abajo') ? [...vals].reverse() : vals;

                if (dir === 'izquierda' || dir === 'derecha') {
                    if (finalLinea.some((v,idx) => v !== grid[i][idx])) cambiado = true;
                    grid[i] = finalLinea;
                } else {
                    for (let r = 0; r < 4; r++) {
                        if (grid[r][i] !== finalLinea[r]) cambiado = true;
                        grid[r][i] = finalLinea[r];
                    }
                }
            }
            if (cambiado) {
                g2048.grid = grid;
                agregarFicha2048();
                render2048();
                if (_sinMovimientos2048()) {
                    g2048.terminado = true;
                    setTimeout(() => {
                        alert(`🎮 Juego terminado. Puntaje final: ${g2048.puntaje}`);
                        guardarPuntaje('2048', g2048.puntaje);
                    }, 200);
                }
            }
        }
        function _sinMovimientos2048() {
            const g = g2048.grid;
            for (let r = 0; r < 4; r++) for (let c = 0; c < 4; c++) {
                if (g[r][c] === 0) return false;
                if (c < 3 && g[r][c] === g[r][c+1]) return false;
                if (r < 3 && g[r][c] === g[r+1][c]) return false;
            }
            return true;
        }

        // ══════════════ TRIVIA ══════════════
        const BANCO_TRIVIA = [
            { p:'¿Qué gas es comúnmente usado como refrigerante en unidades reefer modernas?', o:['R-404A / R-452A','Oxígeno puro','Nitrógeno líquido puro','Dióxido de carbono sólido'], c:0 },
            { p:'¿Qué componente comprime el gas refrigerante para elevar su presión y temperatura?', o:['El evaporador','El compresor','El filtro secador','El termostato'], c:1 },
            { p:'¿Cuál es la función principal del evaporador en un sistema de refrigeración?', o:['Comprimir el gas','Absorber calor del espacio a enfriar','Generar electricidad','Medir la humedad'], c:1 },
            { p:'¿Qué mide un manómetro en un sistema de refrigeración?', o:['Temperatura ambiente','Presión del sistema','Voltaje del motor','Velocidad del ventilador'], c:1 },
            { p:'¿Qué le pasa a un refrigerante cuando pasa por la válvula de expansión?', o:['Se calienta y comprime','Baja su presión y temperatura','Se vuelve sólido','Aumenta su volumen sin cambio de presión'], c:1 },
            { p:'¿Qué es el "subenfriamiento" (subcooling) en un sistema reefer?', o:['Enfriar el refrigerante por debajo de su punto de condensación','Apagar el compresor','Aumentar la presión de succión','Cambiar el filtro de aire'], c:0 },
            { p:'¿Qué componente elimina la humedad y partículas del refrigerante?', o:['El condensador','El filtro secador','El ventilador','El termostato'], c:1 },
            { p:'¿Qué unidad se usa comúnmente para medir la temperatura en unidades reefer en EE.UU./México?', o:['Pascales','Grados Fahrenheit o Celsius','Amperios','Newtons'], c:1 },
            { p:'¿Qué indica una baja presión de succión anormal en el sistema?', o:['Exceso de refrigerante','Posible falta de refrigerante o restricción','Sobrecarga eléctrica','Buen funcionamiento'], c:1 },
            { p:'¿Qué hace el condensador en el ciclo de refrigeración?', o:['Absorbe calor del producto','Libera el calor del refrigerante al ambiente','Genera frío directamente','Almacena el refrigerante'], c:1 },
            { p:'¿Por qué es importante el mantenimiento preventivo en unidades reefer?', o:['Es opcional y no afecta el desempeño','Evita fallas y prolonga la vida útil del equipo','Solo sirve para la garantía','No tiene relación con el consumo de combustible'], c:1 },
            { p:'¿Qué se revisa típicamente en un "pre-trip inspection" de una unidad reefer?', o:['Solo el color de la unidad','Niveles de combustible, alarmas, temperatura y funcionamiento general','El precio de la carga','El historial del conductor'], c:1 },
            { p:'¿Qué significa que una unidad esté en modo "Standby" (Ciclo/Start-Stop)?', o:['El motor está apagado permanentemente','El motor arranca y para automáticamente para mantener temperatura','La unidad está en falla total','El refrigerante se ha agotado'], c:1 },
            { p:'¿Qué herramienta se usa para medir corriente eléctrica en componentes de la unidad?', o:['Termómetro infrarrojo','Multímetro / pinza amperimétrica','Manómetro','Nivel de burbuja'], c:1 },
            { p:'¿Qué tipo de mantenimiento reduce el riesgo de fugas de refrigerante?', o:['Ignorar las conexiones y válvulas','Inspección periódica de conexiones, válvulas y mangueras','Aumentar la presión sin revisar el sistema','Ninguno, las fugas son inevitables'], c:1 },
        ];
        let triviaEstado = null;
        function iniciarTrivia() {
            const preguntas = [...BANCO_TRIVIA].sort(() => Math.random()-0.5).slice(0, 10);
            triviaEstado = { preguntas, indice: 0, correctas: 0 };
            renderTrivia();
        }
        function renderTrivia() {
            const cont = document.getElementById('juego-contenedor');
            const st = triviaEstado;
            if (st.indice >= st.preguntas.length) {
                const puntaje = st.correctas * 10;
                cont.innerHTML = `
                    <h3 style="margin-top:0;color:var(--carrier-blue);">❄️ Trivia Refrigeración</h3>
                    <p style="text-align:center;font-size:1.1rem;">🎉 Terminaste: <b>${st.correctas}/${st.preguntas.length}</b> correctas — Puntaje: <b>${puntaje}</b></p>
                    <p style="text-align:center;"><button class="btn-primary" style="width:auto;padding:8px 18px;" onclick="iniciarTrivia()">🔄 Jugar de nuevo</button></p>
                `;
                guardarPuntaje('trivia', puntaje);
                return;
            }
            const q = st.preguntas[st.indice];
            const opcionesConIndice = q.o.map((texto, i) => ({ texto, esCorrecta: i === q.c }));
            opcionesConIndice.sort(() => Math.random() - 0.5);
            cont.innerHTML = `
                <h3 style="margin-top:0;color:var(--carrier-blue);">❄️ Trivia Refrigeración</h3>
                <div class="juegos-stats"><span>Pregunta ${st.indice+1}/${st.preguntas.length}</span><span>✅ ${st.correctas} correctas</span></div>
                <p style="font-weight:700;font-size:1.05rem;margin-bottom:12px;">${q.p}</p>
                <div id="trivia-opciones"></div>
            `;
            const opcionesDiv = document.getElementById('trivia-opciones');
            opcionesConIndice.forEach(op => {
                const btn = document.createElement('button');
                btn.className = 'trivia-opcion';
                btn.textContent = op.texto;
                btn.dataset.correcta = op.esCorrecta ? '1' : '0';
                btn.onclick = () => responderTrivia(btn, op.esCorrecta, opcionesDiv);
                opcionesDiv.appendChild(btn);
            });
        }
        function responderTrivia(btnClicado, esCorrecta, contenedor) {
            [...contenedor.children].forEach(b => b.onclick = null);
            if (esCorrecta) {
                btnClicado.classList.add('correcta');
                triviaEstado.correctas++;
            } else {
                btnClicado.classList.add('incorrecta');
                const correctaBtn = [...contenedor.children].find(b => b.dataset.correcta === '1');
                if (correctaBtn) correctaBtn.classList.add('correcta');
            }
            setTimeout(() => { triviaEstado.indice++; renderTrivia(); }, 900);
        }

        // ══════════════ GATITO (Tic-Tac-Toe vs CPU) ══════════════
        let gatEstado = null;
        function iniciarGatito() {
            gatEstado = { tablero: Array(9).fill(''), terminado: false, turnoJugador: true };
            renderGatito();
        }
        function renderGatito(mensaje) {
            const cont = document.getElementById('juego-contenedor');
            cont.innerHTML = `
                <h3 style="margin-top:0;color:var(--carrier-blue);">❌⭕ Gatito (vs Computadora)</h3>
                <p style="text-align:center;min-height:24px;font-weight:700;color:var(--carrier-blue);">${mensaje || (gatEstado.turnoJugador ? 'Tu turno (❌)' : 'Pensando...')}</p>
                <div class="gatito-grid" id="gatito-grid"></div>
                <p style="text-align:center;margin-top:14px;"><button class="btn-primary" style="width:auto;padding:8px 18px;" onclick="iniciarGatito()">🔄 Reiniciar</button></p>
            `;
            const grid = document.getElementById('gatito-grid');
            grid.innerHTML = gatEstado.tablero.map((v,i) =>
                `<div class="gatito-celda${v?' ocupada':''}" onclick="jugarGatito(${i})">${v}</div>`
            ).join('');
        }
        function _gatGanador(t) {
            const lineas = [[0,1,2],[3,4,5],[6,7,8],[0,3,6],[1,4,7],[2,5,8],[0,4,8],[2,4,6]];
            for (const [a,b,c] of lineas) if (t[a] && t[a]===t[b] && t[b]===t[c]) return t[a];
            return t.includes('') ? null : 'empate';
        }
        function jugarGatito(i) {
            if (!gatEstado.turnoJugador || gatEstado.tablero[i] || gatEstado.terminado) return;
            gatEstado.tablero[i] = '❌';
            let resultado = _gatGanador(gatEstado.tablero);
            if (resultado) { _finGatito(resultado); return; }
            gatEstado.turnoJugador = false;
            renderGatito();
            setTimeout(() => {
                const i2 = _gatMejorJugada(gatEstado.tablero);
                if (i2 !== -1) gatEstado.tablero[i2] = '⭕';
                resultado = _gatGanador(gatEstado.tablero);
                gatEstado.turnoJugador = true;
                if (resultado) { _finGatito(resultado); return; }
                renderGatito();
            }, 500);
        }
        function _finGatito(resultado) {
            gatEstado.terminado = true;
            let msg, puntaje;
            if (resultado === 'empate') { msg = '🤝 ¡Empate!'; puntaje = 50; }
            else if (resultado === '❌') { msg = '🎉 ¡Ganaste!'; puntaje = 100; }
            else { msg = '😅 Ganó la computadora'; puntaje = 0; }
            renderGatito(msg);
            guardarPuntaje('gatito', puntaje);
        }
        function _gatMejorJugada(t) {
            // Minimax simple (tablero de 9 celdas, muy rápido)
            function minimax(tab, esMax) {
                const res = _gatGanador(tab);
                if (res === '⭕') return { puntaje: 10 };
                if (res === '❌') return { puntaje: -10 };
                if (res === 'empate') return { puntaje: 0 };
                const jugadas = [];
                for (let i = 0; i < 9; i++) {
                    if (!tab[i]) {
                        const copia = [...tab];
                        copia[i] = esMax ? '⭕' : '❌';
                        const r = minimax(copia, !esMax);
                        jugadas.push({ i, puntaje: r.puntaje });
                    }
                }
                if (esMax) return jugadas.reduce((m,j) => j.puntaje > m.puntaje ? j : m);
                return jugadas.reduce((m,j) => j.puntaje < m.puntaje ? j : m);
            }
            const vacias = t.filter(v => v === '').length;
            if (vacias === 9) return 4; // primera jugada: centro (evita cálculo innecesario)
            const mejor = minimax(t, true);
            return mejor.i !== undefined ? mejor.i : -1;
        }

        // ══════════════ CULEBRA (Snake) ══════════════
        let culEstado = null;
        function iniciarCulebra() {
            const cont = document.getElementById('juego-contenedor');
            cont.innerHTML = `
                <h3 style="margin-top:0;color:var(--carrier-blue);">🐍 Culebra</h3>
                <div class="juegos-stats"><span>🍎 Puntaje: <span id="cul-puntaje">0</span></span></div>
                <canvas id="cul-canvas" class="juegos-canvas" width="320" height="320"></canvas>
                <p style="text-align:center;font-size:.8rem;color:#94a3b8;margin-top:8px;">Usa las flechas del teclado. En celular, desliza sobre el tablero.</p>
                <p style="text-align:center;margin-top:10px;"><button class="btn-primary" style="width:auto;padding:8px 18px;" onclick="iniciarCulebra()">🔄 Reiniciar</button></p>
            `;
            const tam = 16, celda = 20;
            culEstado = {
                tam, celda, serpiente: [{x:8,y:8}], dir:{x:1,y:0}, dirSiguiente:{x:1,y:0},
                comida: {x:12,y:8}, puntaje: 0, activo: true
            };
            if (culEstado.loop) clearInterval(culEstado.loop);
            culEstado.loop = setInterval(_culTick, 140);
            document.removeEventListener('keydown', _culTecla);
            document.addEventListener('keydown', _culTecla);
            const canvas = document.getElementById('cul-canvas');
            let touchStart = null;
            canvas.addEventListener('touchstart', e => { touchStart = e.touches[0]; });
            canvas.addEventListener('touchend', e => {
                if (!touchStart) return;
                const dx = e.changedTouches[0].clientX - touchStart.clientX;
                const dy = e.changedTouches[0].clientY - touchStart.clientY;
                if (Math.abs(dx) > Math.abs(dy)) _culSetDir(dx > 0 ? {x:1,y:0} : {x:-1,y:0});
                else _culSetDir(dy > 0 ? {x:0,y:1} : {x:0,y:-1});
            });
            _culRender();
        }
        function _culTecla(e) {
            const mapa = { ArrowUp:{x:0,y:-1}, ArrowDown:{x:0,y:1}, ArrowLeft:{x:-1,y:0}, ArrowRight:{x:1,y:0} };
            if (mapa[e.key]) { e.preventDefault(); _culSetDir(mapa[e.key]); }
        }
        function _culSetDir(d) {
            if (!culEstado || !culEstado.activo) return;
            if (culEstado.dir.x === -d.x && culEstado.dir.y === -d.y) return; // no ir en reversa
            culEstado.dirSiguiente = d;
        }
        function _culTick() {
            const st = culEstado;
            if (!st.activo) return;
            st.dir = st.dirSiguiente;
            const cabeza = { x: st.serpiente[0].x + st.dir.x, y: st.serpiente[0].y + st.dir.y };
            if (cabeza.x < 0 || cabeza.y < 0 || cabeza.x >= st.tam || cabeza.y >= st.tam ||
                st.serpiente.some(s => s.x === cabeza.x && s.y === cabeza.y)) {
                st.activo = false;
                clearInterval(st.loop);
                setTimeout(() => {
                    alert(`🐍 ¡Choque! Puntaje final: ${st.puntaje}`);
                    guardarPuntaje('culebra', st.puntaje);
                }, 100);
                return;
            }
            st.serpiente.unshift(cabeza);
            if (cabeza.x === st.comida.x && cabeza.y === st.comida.y) {
                st.puntaje += 10;
                document.getElementById('cul-puntaje').textContent = st.puntaje;
                do {
                    st.comida = { x: Math.floor(Math.random()*st.tam), y: Math.floor(Math.random()*st.tam) };
                } while (st.serpiente.some(s => s.x === st.comida.x && s.y === st.comida.y));
            } else {
                st.serpiente.pop();
            }
            _culRender();
        }
        function _culRender() {
            const st = culEstado;
            const canvas = document.getElementById('cul-canvas');
            if (!canvas) return;
            const ctx = canvas.getContext('2d');
            ctx.fillStyle = '#0f172a';
            ctx.fillRect(0, 0, canvas.width, canvas.height);
            ctx.fillStyle = '#ef4444';
            ctx.fillRect(st.comida.x*st.celda+2, st.comida.y*st.celda+2, st.celda-4, st.celda-4);
            st.serpiente.forEach((s,i) => {
                ctx.fillStyle = i === 0 ? '#22c55e' : '#4ade80';
                ctx.fillRect(s.x*st.celda+1, s.y*st.celda+1, st.celda-2, st.celda-2);
            });
        }

        // ══════════════ BILLAR (2D simplificado) ══════════════
        let bilEstado = null;
        function iniciarBillar() {
            const cont = document.getElementById('juego-contenedor');
            cont.innerHTML = `
                <h3 style="margin-top:0;color:var(--carrier-blue);">🎱 Billar</h3>
                <div class="juegos-stats"><span>🎯 Puntaje: <span id="bil-puntaje">0</span></span></div>
                <canvas id="bil-canvas" class="juegos-canvas" width="380" height="220"></canvas>
                <p style="text-align:center;font-size:.8rem;color:#94a3b8;margin-top:8px;">Arrastra desde la bola blanca hacia atrás para apuntar y suelta para tirar.</p>
                <p style="text-align:center;margin-top:10px;"><button class="btn-primary" style="width:auto;padding:8px 18px;" onclick="iniciarBillar()">🔄 Reiniciar mesa</button></p>
            `;
            const radio = 9;
            const bolas = [{ x:90, y:110, color:'#f8fafc', esBlanca:true, activa:true }];
            const colores = ['#facc15','#3b82f6','#ef4444','#a855f7','#f97316','#16a34a'];
            let idx = 0;
            for (let fila = 0; fila < 3; fila++) {
                for (let c = 0; c <= fila; c++) {
                    bolas.push({
                        x: 280 + fila*18 + (Math.random()-0.5)*0.6,
                        y: 110 - fila*9 + c*18 + (Math.random()-0.5)*0.6,
                        color: colores[idx % colores.length], esBlanca:false, activa:true
                    });
                    idx++;
                }
            }
            bilEstado = { bolas, puntaje:0, arrastrando:false, inicioArrastre:null, animando:false, terminado:false };
            const canvas = document.getElementById('bil-canvas');
            const getPos = e => {
                const r = canvas.getBoundingClientRect();
                const p = e.touches ? e.touches[0] : e;
                return { x: p.clientX - r.left, y: p.clientY - r.top };
            };
            canvas.onmousedown = canvas.ontouchstart = e => {
                e.preventDefault();
                if (bilEstado.animando || bilEstado.terminado) return;
                const blanca = bilEstado.bolas[0];
                if (!blanca.activa) return;
                bilEstado.arrastrando = true;
                bilEstado.inicioArrastre = getPos(e);
            };
            canvas.onmousemove = canvas.ontouchmove = e => {
                e.preventDefault();
                if (bilEstado.arrastrando) { bilEstado._posActual = getPos(e); _bilRender(); }
            };
            const soltar = e => {
                if (!bilEstado.arrastrando) return;
                bilEstado.arrastrando = false;
                const fin = bilEstado._posActual || bilEstado.inicioArrastre;
                const blanca = bilEstado.bolas[0];
                const dx = blanca.x - fin.x, dy = blanca.y - fin.y;
                const potencia = Math.min(Math.hypot(dx, dy) / 6, 14);
                if (potencia > 0.5) {
                    const ang = Math.atan2(dy, dx);
                    blanca.vx = Math.cos(ang) * potencia;
                    blanca.vy = Math.sin(ang) * potencia;
                    _bilAnimar();
                }
            };
            canvas.onmouseup = canvas.ontouchend = soltar;
            _bilRender();
        }
        function _bilAnimar() {
            const st = bilEstado;
            st.animando = true;
            const canvas = document.getElementById('bil-canvas');
            const radio = 9;
            const pockets = [[10,10],[190,8],[370,10],[10,210],[190,212],[370,210]];
            const SUBPASOS = 8; // varias mini-actualizaciones por frame: evita que las bolas se "brinquen" entre sí a alta velocidad

            function resolverColisionesBolas() {
                for (let i = 0; i < st.bolas.length; i++) {
                    for (let j = i+1; j < st.bolas.length; j++) {
                        const a = st.bolas[i], b = st.bolas[j];
                        if (!a.activa || !b.activa) continue;
                        const dx = b.x-a.x, dy = b.y-a.y;
                        const dist = Math.hypot(dx, dy);
                        if (dist < radio*2 && dist > 0.0001) {
                            const nx = dx/dist, ny = dy/dist;
                            const overlap = radio*2 - dist;
                            a.x -= nx*overlap/2; a.y -= ny*overlap/2;
                            b.x += nx*overlap/2; b.y += ny*overlap/2;
                            const va = a.vx*nx + a.vy*ny, vb = b.vx*nx + b.vy*ny;
                            const dif = va - vb;
                            if (dif > 0) { // solo transferir impulso si realmente se están acercando
                                a.vx -= dif*nx; a.vy -= dif*ny;
                                b.vx += dif*nx; b.vy += dif*ny;
                            }
                        }
                    }
                }
            }
            function revisarBordesYBolsillos() {
                st.bolas.forEach(b => {
                    if (!b.activa) return;
                    if (b.x < radio) { b.x = radio; b.vx = Math.abs(b.vx); }
                    if (b.x > canvas.width-radio) { b.x = canvas.width-radio; b.vx = -Math.abs(b.vx); }
                    if (b.y < radio) { b.y = radio; b.vy = Math.abs(b.vy); }
                    if (b.y > canvas.height-radio) { b.y = canvas.height-radio; b.vy = -Math.abs(b.vy); }
                    pockets.forEach(([px,py]) => {
                        if (b.activa && Math.hypot(b.x-px, b.y-py) < 14) {
                            b.activa = false; b.vx = 0; b.vy = 0;
                            if (b.esBlanca) {
                                st.puntaje = Math.max(0, st.puntaje - 50);
                                setTimeout(() => { b.activa = true; b.x = 90; b.y = 110; b.vx=0; b.vy=0; _bilRender(); }, 400);
                            } else {
                                st.puntaje += 100;
                            }
                            document.getElementById('bil-puntaje').textContent = st.puntaje;
                        }
                    });
                });
            }

            function paso() {
                for (let s = 0; s < SUBPASOS; s++) {
                    st.bolas.forEach(b => {
                        if (!b.activa || (!b.vx && !b.vy)) return;
                        b.x += b.vx / SUBPASOS;
                        b.y += b.vy / SUBPASOS;
                    });
                    revisarBordesYBolsillos();
                    resolverColisionesBolas();
                }
                let algoMoviendose = false;
                st.bolas.forEach(b => {
                    if (!b.activa) return;
                    b.vx *= 0.985; b.vy *= 0.985;
                    if (Math.hypot(b.vx, b.vy) < 0.08) { b.vx = 0; b.vy = 0; }
                    else algoMoviendose = true;
                });
                _bilRender();
                if (algoMoviendose) requestAnimationFrame(paso);
                else {
                    st.animando = false;
                    const objetivos = st.bolas.slice(1);
                    if (objetivos.every(b => !b.activa) && !st.terminado) {
                        st.terminado = true;
                        setTimeout(() => {
                            alert(`🎱 ¡Mesa limpia! Puntaje final: ${st.puntaje}`);
                            guardarPuntaje('billar', st.puntaje);
                        }, 150);
                    }
                }
            }
            requestAnimationFrame(paso);
        }
        function _bilRender() {
            const st = bilEstado;
            const canvas = document.getElementById('bil-canvas');
            if (!canvas || !st) return;
            const ctx = canvas.getContext('2d');
            ctx.fillStyle = '#0b6e4f';
            ctx.fillRect(0, 0, canvas.width, canvas.height);
            const pockets = [[10,10],[190,8],[370,10],[10,210],[190,212],[370,210]];
            ctx.fillStyle = '#0f172a';
            pockets.forEach(([px,py]) => { ctx.beginPath(); ctx.arc(px,py,12,0,7); ctx.fill(); });
            st.bolas.forEach(b => {
                if (!b.activa) return;
                ctx.beginPath();
                ctx.arc(b.x, b.y, 9, 0, 7);
                ctx.fillStyle = b.color;
                ctx.fill();
                ctx.strokeStyle = '#00000033'; ctx.stroke();
            });
            if (st.arrastrando && st._posActual) {
                const blanca = st.bolas[0];
                ctx.beginPath();
                ctx.moveTo(blanca.x, blanca.y);
                ctx.lineTo(2*blanca.x - st._posActual.x, 2*blanca.y - st._posActual.y);
                ctx.strokeStyle = '#facc15'; ctx.lineWidth = 2; ctx.stroke(); ctx.lineWidth = 1;
            }
        }

        // ══════════════ CARTAS (21 / Blackjack simplificado) ══════════════
        let cartEstado = null;
        function _cartBaraja() {
            const palos = [{s:'♥',color:'roja'},{s:'♦',color:'roja'},{s:'♣',color:'negra'},{s:'♠',color:'negra'}];
            const valores = ['A','2','3','4','5','6','7','8','9','10','J','Q','K'];
            const baraja = [];
            palos.forEach(p => valores.forEach(v => baraja.push({ v, s: p.s, color: p.color })));
            return baraja.sort(() => Math.random() - 0.5);
        }
        function _cartValor(cartas) {
            let total = 0, ases = 0;
            cartas.forEach(c => {
                if (c.v === 'A') { total += 11; ases++; }
                else if (['J','Q','K'].includes(c.v)) total += 10;
                else total += parseInt(c.v);
            });
            while (total > 21 && ases > 0) { total -= 10; ases--; }
            return total;
        }
        function iniciarCartas() {
            cartEstado = { fichas: 500, apuesta: 50, mano: 0, manosTotales: 5, terminado: false };
            _cartNuevaMano();
        }
        function _cartNuevaMano() {
            const st = cartEstado;
            st.baraja = _cartBaraja();
            st.jugador = [st.baraja.pop(), st.baraja.pop()];
            st.crupier = [st.baraja.pop(), st.baraja.pop()];
            st.rondaTerminada = false;
            st.fichas -= st.apuesta;
            _renderCartas();
            if (_cartValor(st.jugador) === 21) _cartPlantarse();
        }
        function _cartaHTML(c, oculta) {
            if (oculta) return `<div class="carta-vista" style="background:#334155;color:#334155;">🂠</div>`;
            return `<div class="carta-vista carta-${c.color}">${c.v}${c.s}</div>`;
        }
        function _renderCartas(mensaje) {
            const st = cartEstado;
            const cont = document.getElementById('juego-contenedor');
            cont.innerHTML = `
                <h3 style="margin-top:0;color:var(--carrier-blue);">🃏 21 (Blackjack)</h3>
                <div class="juegos-stats"><span>💰 Fichas: ${st.fichas}</span><span>Mano ${st.mano+1}/${st.manosTotales}</span><span>Apuesta: ${st.apuesta}</span></div>
                <p style="text-align:center;font-weight:700;">Crupier (${st.rondaTerminada ? _cartValor(st.crupier) : '?'})</p>
                <div style="text-align:center;">${st.crupier.map((c,i) => _cartaHTML(c, i===1 && !st.rondaTerminada)).join('')}</div>
                <p style="text-align:center;font-weight:700;margin-top:14px;">Tú (${_cartValor(st.jugador)})</p>
                <div style="text-align:center;">${st.jugador.map(c => _cartaHTML(c)).join('')}</div>
                <p style="text-align:center;min-height:24px;font-weight:700;color:var(--carrier-blue);">${mensaje || ''}</p>
                <div style="text-align:center;margin-top:10px;">
                    ${st.rondaTerminada
                        ? `<button class="btn-primary" style="width:auto;padding:8px 18px;" onclick="_cartSiguiente()">${st.mano+1 >= st.manosTotales ? '🏁 Ver resultado final' : '➡️ Siguiente mano'}</button>`
                        : `<button class="btn-primary" style="width:auto;padding:8px 18px;margin-right:8px;" onclick="_cartPedir()">🃏 Pedir</button>
                           <button class="btn-primary" style="width:auto;padding:8px 18px;" onclick="_cartPlantarse()">✋ Plantarse</button>`
                    }
                </div>
            `;
        }
        function _cartPedir() {
            const st = cartEstado;
            st.jugador.push(st.baraja.pop());
            if (_cartValor(st.jugador) > 21) { _cartResolver('pierde'); return; }
            _renderCartas();
        }
        function _cartPlantarse() {
            const st = cartEstado;
            while (_cartValor(st.crupier) < 17) st.crupier.push(st.baraja.pop());
            const vj = _cartValor(st.jugador), vc = _cartValor(st.crupier);
            if (vj > 21) _cartResolver('pierde');
            else if (vc > 21 || vj > vc) _cartResolver('gana');
            else if (vj === vc) _cartResolver('empata');
            else _cartResolver('pierde');
        }
        function _cartResolver(resultado) {
            const st = cartEstado;
            st.rondaTerminada = true;
            let msg;
            if (resultado === 'gana') { st.fichas += st.apuesta * 2; msg = '🎉 ¡Ganaste esta mano!'; }
            else if (resultado === 'empata') { st.fichas += st.apuesta; msg = '🤝 Empate (push)'; }
            else msg = '😅 Perdiste esta mano';
            _renderCartas(msg);
        }
        function _cartSiguiente() {
            const st = cartEstado;
            st.mano++;
            if (st.mano >= st.manosTotales || st.fichas < st.apuesta) {
                setTimeout(() => {
                    alert(`🃏 Sesión terminada. Fichas finales: ${st.fichas}`);
                    guardarPuntaje('cartas', st.fichas);
                }, 100);
                return;
            }
            _cartNuevaMano();
        }

        // ══════════════ SÚPER TÉCNICO (plataformas estilo Mario) — 3D con Three.js ══════════════
        let marioEstado = null;
        let _mario3D = null;
        function crearGoomba3D() {
            const grupo = new THREE.Group();
            const matCuerpo = new THREE.MeshStandardMaterial({ color: 0x92400e, roughness: 0.75 });
            const cuerpo = new THREE.Mesh(new THREE.SphereGeometry(0.24, 12, 10), matCuerpo);
            cuerpo.position.y = 0.22; cuerpo.scale.y = 0.85; cuerpo.castShadow = true;
            grupo.add(cuerpo);
            const matPie = new THREE.MeshStandardMaterial({ color: 0x451a03, roughness: 0.85 });
            [-0.12, 0.12].forEach(x => {
                const pie = new THREE.Mesh(new THREE.BoxGeometry(0.14, 0.08, 0.16), matPie);
                pie.position.set(x, 0.04, 0.02); grupo.add(pie);
            });
            const matOjo = new THREE.MeshStandardMaterial({ color: 0xfef3c7 });
            const matPupila = new THREE.MeshStandardMaterial({ color: 0x1f2937 });
            [-0.08, 0.08].forEach(x => {
                const ojo = new THREE.Mesh(new THREE.SphereGeometry(0.05, 8, 8), matOjo);
                ojo.position.set(x, 0.28, 0.19); grupo.add(ojo);
                const pupila = new THREE.Mesh(new THREE.SphereGeometry(0.022, 6, 6), matPupila);
                pupila.position.set(x, 0.27, 0.235); grupo.add(pupila);
            });
            return grupo;
        }
        function crearTuberia3D() {
            const grupo = new THREE.Group();
            const mat = new THREE.MeshStandardMaterial({ color: 0x0e7490, roughness: 0.4, metalness: 0.2 });
            const cuerpo = new THREE.Mesh(new THREE.CylinderGeometry(0.22, 0.22, 0.7, 14), mat);
            cuerpo.position.y = 0.35; cuerpo.castShadow = true; grupo.add(cuerpo);
            const borde = new THREE.Mesh(new THREE.CylinderGeometry(0.27, 0.27, 0.14, 14), mat);
            borde.position.y = 0.66; grupo.add(borde);
            return grupo;
        }
        function crearMoneda3D() {
            const mat = new THREE.MeshStandardMaterial({ color: 0xfbbf24, roughness: 0.25, metalness: 0.85, emissive: 0x774d00, emissiveIntensity: 0.15 });
            const moneda = new THREE.Mesh(new THREE.CylinderGeometry(0.16, 0.16, 0.045, 20), mat);
            moneda.rotation.x = Math.PI / 2;
            moneda.castShadow = true;
            return moneda;
        }
        function _marioTeclaDown(e) {
            if (['ArrowUp', ' ', 'Spacebar', 'Space'].includes(e.key) || e.code === 'Space') {
                e.preventDefault();
                _marioSaltar();
            }
        }
        function _marioTeclaUp(e) {
            const st = marioEstado;
            if (st && st.vy > 2.6 && (['ArrowUp', ' ', 'Spacebar', 'Space'].includes(e.key) || e.code === 'Space')) {
                st.vy = 2.6;
            }
        }
        function _marioSaltar() {
            const st = marioEstado;
            if (!st || !st.activo) return;
            if (st.enSuelo) { st.vy = 6.0; st.enSuelo = false; st.saltosDisponibles = 1; }
            else if (st.saltosDisponibles > 0) { st.vy = 5.2; st.saltosDisponibles--; }
        }
        function iniciarMario() {
            const cont = document.getElementById('juego-contenedor');
            cont.innerHTML = `
                <h3 style="margin-top:0;color:var(--carrier-blue);">🏃 Súper Técnico 3D</h3>
                <div class="juegos-stats"><span>⭐ Puntaje: <span id="mario-puntaje">0</span></span><span>🪙 Monedas: <span id="mario-monedas">0</span></span></div>
                <div id="mario-3d-contenedor" style="width:100%;max-width:420px;height:260px;margin:0 auto;border-radius:12px;overflow:hidden;background:#8ecbf0;"></div>
                <div class="juegos-controles-touch"><button id="mario-salto-btn">⬆️ Saltar (doble salto disponible)</button></div>
                <p style="text-align:center;font-size:.8rem;color:#94a3b8;margin-top:8px;">Flecha arriba / Espacio / botón para saltar — puedes saltar dos veces seguidas en el aire. Esquiva hongos, salta sobre ellos para eliminarlos y junta monedas. Personaje 3D en tercera persona.</p>
                <p style="text-align:center;margin-top:10px;"><button class="btn-primary" style="width:auto;padding:8px 18px;" onclick="iniciarMario()">🔄 Reiniciar</button></p>
            `;
            marioEstado = {
                y: 0, vy: 0, enSuelo: true, saltosDisponibles: 1,
                obstaculos: [], monedas: [],
                distancia: 0, velocidad: 4.6, monedasN: 0, puntaje: 0, activo: true,
                proximoSpawn: 2.2, fundido: 0, faseCarrera: 0
            };
            const contenedor3D = document.getElementById('mario-3d-contenedor');
            if (typeof THREE === 'undefined') {
                contenedor3D.innerHTML = '<p style="color:#fff;text-align:center;padding-top:110px;">No se pudo cargar el motor 3D (revisa tu conexión a internet).</p>';
                return;
            }
            if (_mario3D && _mario3D.renderer) { try { _mario3D.renderer.dispose(); } catch (e) {} }
            const ancho = contenedor3D.clientWidth || 380, alto = 260;
            const scene = new THREE.Scene();
            scene.background = new THREE.Color(0x8ecbf0);
            scene.fog = new THREE.Fog(0x8ecbf0, 10, 34);
            const camera = new THREE.PerspectiveCamera(48, ancho / alto, 0.1, 60);
            const renderer = new THREE.WebGLRenderer({ antialias: true });
            renderer.setSize(ancho, alto);
            renderer.shadowMap.enabled = true;
            contenedor3D.innerHTML = '';
            contenedor3D.appendChild(renderer.domElement);
            scene.add(new THREE.HemisphereLight(0xbfe3ff, 0x3f6b34, 0.85));
            const sol = new THREE.DirectionalLight(0xfff4d6, 1.1);
            sol.position.set(-4, 8, 5);
            sol.castShadow = true; sol.shadow.mapSize.set(512, 512);
            scene.add(sol);
            const piso = new THREE.Mesh(new THREE.PlaneGeometry(14, 80), new THREE.MeshStandardMaterial({ color: 0x6fae52, roughness: 0.95 }));
            piso.rotation.x = -Math.PI / 2; piso.position.z = -20; piso.receiveShadow = true;
            scene.add(piso);
            const tablones = [];
            for (let i = 0; i < 10; i++) {
                const t = new THREE.Mesh(new THREE.BoxGeometry(1.6, 0.03, 0.25), new THREE.MeshStandardMaterial({ color: 0x557a3d, roughness: 0.9 }));
                t.position.set(0, 0.016, -i * 4);
                t.receiveShadow = true;
                scene.add(t); tablones.push(t);
            }
            const tecnico = crearTecnico3D(0x1d4ed8);
            tecnico.position.set(0, 0, 2);
            scene.add(tecnico);
            _mario3D = { scene, camera, renderer, tecnico, tablones, ultimoTiempo: performance.now() };
            document.getElementById('mario-salto-btn').onclick = _marioSaltar;
            contenedor3D.onpointerdown = _marioSaltar;
            document.removeEventListener('keydown', _marioTeclaDown);
            document.addEventListener('keydown', _marioTeclaDown);
            document.removeEventListener('keyup', _marioTeclaUp);
            document.addEventListener('keyup', _marioTeclaUp);
            _rafActivo = requestAnimationFrame(_marioLoop);
        }
        function _animarCorrerSalto(grupo, st, dt) {
            const p = grupo.userData.partes;
            if (st.enSuelo && st.activo) st.faseCarrera += dt * (7 + st.velocidad * 0.6);
            const fase = st.faseCarrera;
            const amp = st.enSuelo ? 0.75 : 0;
            const suav = 1 - Math.pow(0.001, dt);
            const objCaderaDer = st.enSuelo ? Math.sin(fase) * amp : -0.55;
            const objCaderaIzq = st.enSuelo ? Math.sin(fase + Math.PI) * amp : 0.35;
            const objRodillaDer = st.enSuelo ? Math.max(0, Math.sin(fase - 0.5)) * 1.0 : 0.9;
            const objRodillaIzq = st.enSuelo ? Math.max(0, Math.sin(fase + Math.PI - 0.5)) * 1.0 : 0.5;
            const objHombroDer = st.enSuelo ? Math.sin(fase + Math.PI) * 0.5 : -0.3;
            const objHombroIzq = st.enSuelo ? Math.sin(fase) * 0.5 : -0.3;
            p.piernaDer.cadera.rotation.x += (objCaderaDer - p.piernaDer.cadera.rotation.x) * suav;
            p.piernaIzq.cadera.rotation.x += (objCaderaIzq - p.piernaIzq.cadera.rotation.x) * suav;
            p.piernaDer.rodilla.rotation.x += (objRodillaDer - p.piernaDer.rodilla.rotation.x) * suav;
            p.piernaIzq.rodilla.rotation.x += (objRodillaIzq - p.piernaIzq.rodilla.rotation.x) * suav;
            p.brazoDer.hombro.rotation.x += (objHombroDer - p.brazoDer.hombro.rotation.x) * suav;
            p.brazoIzq.hombro.rotation.x += (objHombroIzq - p.brazoIzq.hombro.rotation.x) * suav;
            p.torso.rotation.x += ((st.enSuelo ? -0.06 : -0.14) - p.torso.rotation.x) * suav;
            grupo.position.y = st.y;
        }
        function _marioLoop() {
            const st = marioEstado;
            if (!st || !_mario3D || juegoActual !== 'mario') return;
            const ahora = performance.now();
            const dt = Math.min(0.05, (ahora - _mario3D.ultimoTiempo) / 1000);
            _mario3D.ultimoTiempo = ahora;
            if (st.activo) {
                st.distancia += st.velocidad * dt;
                st.velocidad = Math.min(9.5, 4.6 + st.distancia / 60);
                st.vy -= 15 * dt;
                st.y += st.vy * dt;
                if (st.y <= 0) { st.y = 0; st.vy = 0; st.enSuelo = true; st.saltosDisponibles = 1; }
                else st.enSuelo = false;
                st.proximoSpawn -= st.velocidad * dt;
                if (st.proximoSpawn <= 0) {
                    st.proximoSpawn = 2.6 + Math.random() * 2.2;
                    const esGoomba = Math.random() < 0.65;
                    const mesh = esGoomba ? crearGoomba3D() : crearTuberia3D();
                    mesh.position.set(0, 0, -32 - Math.random() * 6);
                    _mario3D.scene.add(mesh);
                    st.obstaculos.push({ mesh, tipo: esGoomba ? 'goomba' : 'tuberia', alto: esGoomba ? 0.46 : 0.7, vivo: true });
                    if (Math.random() < 0.55) {
                        const moneda = crearMoneda3D();
                        moneda.position.set(0, 0.85 + Math.random() * 0.5, -30 - Math.random() * 6);
                        _mario3D.scene.add(moneda);
                        st.monedas.push({ mesh: moneda, tomada: false });
                    }
                }
                st.obstaculos.forEach(o => o.mesh.position.z += st.velocidad * dt);
                st.monedas.forEach(m => { m.mesh.position.z += st.velocidad * dt; m.mesh.rotation.z += dt * 4; });
                _mario3D.tablones.forEach(t => { t.position.z += st.velocidad * dt; if (t.position.z > 6) t.position.z -= 40; });
                st.obstaculos.forEach(o => {
                    if (!o.vivo) return;
                    const dz = Math.abs(o.mesh.position.z - 2);
                    if (dz < 0.42) {
                        const cayendoEncima = o.tipo === 'goomba' && st.vy < 0 && st.y > o.alto * 0.4;
                        if (cayendoEncima) {
                            o.vivo = false; st.vy = 6.2; st.saltosDisponibles = 1; st.puntaje += 50;
                        } else if (st.y < o.alto - 0.05) { st.activo = false; _marioFin(); }
                    }
                });
                st.monedas.forEach(m => {
                    if (m.tomada) return;
                    const dz = Math.abs(m.mesh.position.z - 2);
                    const dy = Math.abs(m.mesh.position.y - (st.y + 1.1));
                    if (dz < 0.4 && dy < 0.55) { m.tomada = true; st.monedasN++; st.puntaje += 10; }
                });
                st.obstaculos = st.obstaculos.filter(o => {
                    if (!o.vivo || o.mesh.position.z > 5) { _mario3D.scene.remove(o.mesh); return false; }
                    return true;
                });
                st.monedas = st.monedas.filter(m => {
                    if (m.tomada || m.mesh.position.z > 5) { _mario3D.scene.remove(m.mesh); return false; }
                    return true;
                });
                st.puntaje = Math.floor(st.distancia * 3) + st.monedasN * 10;
                document.getElementById('mario-puntaje').textContent = st.puntaje;
                document.getElementById('mario-monedas').textContent = st.monedasN;
            } else {
                st.fundido = Math.min(1, st.fundido + dt * 2.2);
            }
            _animarCorrerSalto(_mario3D.tecnico, st, dt);
            _mario3D.camera.position.set(0, 2.2 + st.y * 0.15, 6.4);
            _mario3D.camera.lookAt(0, 1.15 + st.y * 0.4, -1);
            _mario3D.renderer.render(_mario3D.scene, _mario3D.camera);
            if (st.activo || st.fundido < 1) _rafActivo = requestAnimationFrame(_marioLoop);
        }
        function _marioFin() {
            const st = marioEstado;
            setTimeout(() => {
                alert(`🏃 ¡Chocaste! Puntaje final: ${st.puntaje} (🪙 ${st.monedasN} monedas)`);
                guardarPuntaje('mario', st.puntaje);
            }, 450);
        }

        // ══════════════ CARRERAS — 3D con Three.js ══════════════
        let carEstado = null;
        let _car3D = null;
        function crearVehiculo3D(color, conductor) {
            const grupo = new THREE.Group();
            const DS = THREE.DoubleSide;
            const matCuerpo = new THREE.MeshStandardMaterial({ color, roughness: 0.35, metalness: 0.3, side: DS });
            const matVidrio = new THREE.MeshStandardMaterial({ color: 0xbfe3ff, roughness: 0.1, metalness: 0.1, transparent: true, opacity: 0.75, side: DS });
            const matLlanta = new THREE.MeshStandardMaterial({ color: 0x111827, roughness: 0.85, side: DS });
            const matFranja = new THREE.MeshStandardMaterial({ color: 0xfbbf24, roughness: 0.4, side: DS });
            const cuerpo = new THREE.Mesh(new THREE.BoxGeometry(0.9, 0.55, 1.9), matCuerpo);
            cuerpo.position.y = 0.5; cuerpo.castShadow = true; grupo.add(cuerpo);
            const cabina = new THREE.Mesh(new THREE.BoxGeometry(0.82, 0.4, 0.9), matVidrio);
            cabina.position.set(0, 0.92, 0.15); grupo.add(cabina);
            const franja = new THREE.Mesh(new THREE.BoxGeometry(0.92, 0.1, 0.3), matFranja);
            franja.position.set(0, 0.35, 0.55); grupo.add(franja);
            [[-0.42, -0.65], [0.42, -0.65], [-0.42, 0.65], [0.42, 0.65]].forEach(([x, z]) => {
                const llanta = new THREE.Mesh(new THREE.CylinderGeometry(0.22, 0.22, 0.22, 14), matLlanta);
                llanta.rotation.z = Math.PI / 2;
                llanta.position.set(x, 0.22, z); llanta.castShadow = true;
                grupo.add(llanta);
            });
            if (conductor) {
                const cabeza = new THREE.Mesh(new THREE.SphereGeometry(0.14, 10, 10), new THREE.MeshStandardMaterial({ color: 0xf1c27d }));
                cabeza.position.set(0, 1.0, 0.05); grupo.add(cabeza);
                const casco = new THREE.Mesh(new THREE.SphereGeometry(0.155, 10, 10, 0, Math.PI * 2, 0, Math.PI * 0.55), new THREE.MeshStandardMaterial({ color: 0xf59e0b, roughness: 0.3 }));
                casco.position.set(0, 1.05, 0.05); grupo.add(casco);
            }
            return grupo;
        }
        function _carrerasTecla(e) {
            if (!carEstado || !carEstado.activo) return;
            if (e.key === 'ArrowLeft') _carrerasCambiarCarril(-1);
            else if (e.key === 'ArrowRight') _carrerasCambiarCarril(1);
            else if (e.key === 'ArrowUp') carEstado.acelerando = true;
            else if (e.key === 'ArrowDown') carEstado.frenando = true;
        }
        function _carrerasTeclaUp(e) {
            if (!carEstado) return;
            if (e.key === 'ArrowUp') carEstado.acelerando = false;
            else if (e.key === 'ArrowDown') carEstado.frenando = false;
        }
        function _carrerasCambiarCarril(delta) {
            const st = carEstado;
            if (!st) return;
            st.carril = Math.max(0, Math.min(2, st.carril + delta));
        }
        function iniciarCarreras() {
            const cont = document.getElementById('juego-contenedor');
            cont.innerHTML = `
                <h3 style="margin-top:0;color:var(--carrier-blue);">🏎️ Carreras 3D — Unidad Móvil</h3>
                <div class="juegos-stats"><span>⭐ Puntaje: <span id="car-puntaje">0</span></span><span>🏁 Velocidad: <span id="car-velocidad">1.0x</span></span></div>
                <div id="car-3d-contenedor" style="width:100%;max-width:420px;height:280px;margin:0 auto;border-radius:12px;overflow:hidden;background:#1e293b;"></div>
                <div class="juegos-controles-touch">
                    <button id="car-izq-btn">⬅️</button>
                    <button id="car-freno-btn">🐢 Frenar</button>
                    <button id="car-acel-btn">🚀 Acelerar</button>
                    <button id="car-der-btn">➡️</button>
                </div>
                <p style="text-align:center;font-size:.8rem;color:#94a3b8;margin-top:8px;">Flechas ← → o botones para cambiar de carril. ↑/Acelerar suma más puntos (más riesgo), ↓/Frenar te da más control. Vehículo 3D con cámara en tercera persona.</p>
                <p style="text-align:center;margin-top:10px;"><button class="btn-primary" style="width:auto;padding:8px 18px;" onclick="iniciarCarreras()">🔄 Reiniciar</button></p>
            `;
            carEstado = {
                carril: 1, xVisual: 0, inclinacion: 0, enemigos: [], puntaje: 0, activo: true,
                velocidad: 7, proximoSpawn: 1.4, acelerando: false, frenando: false, fundido: 0
            };
            const contenedor3D = document.getElementById('car-3d-contenedor');
            if (typeof THREE === 'undefined') {
                contenedor3D.innerHTML = '<p style="color:#fff;text-align:center;padding-top:120px;">No se pudo cargar el motor 3D (revisa tu conexión a internet).</p>';
                return;
            }
            if (_car3D && _car3D.renderer) { try { _car3D.renderer.dispose(); } catch (e) {} }
            const ancho = contenedor3D.clientWidth || 380, alto = 280;
            const scene = new THREE.Scene();
            scene.background = new THREE.Color(0x1e293b);
            scene.fog = new THREE.Fog(0x1e293b, 10, 34);
            const camera = new THREE.PerspectiveCamera(50, ancho / alto, 0.1, 60);
            const renderer = new THREE.WebGLRenderer({ antialias: true });
            renderer.setSize(ancho, alto);
            renderer.shadowMap.enabled = true;
            contenedor3D.innerHTML = '';
            contenedor3D.appendChild(renderer.domElement);
            scene.add(new THREE.HemisphereLight(0x8fa8c8, 0x0f172a, 0.75));
            const luzDireccional = new THREE.DirectionalLight(0xfff4d6, 1.0);
            luzDireccional.position.set(3, 8, 4);
            luzDireccional.castShadow = true; luzDireccional.shadow.mapSize.set(512, 512);
            scene.add(luzDireccional);
            const pista = new THREE.Mesh(new THREE.PlaneGeometry(6.2, 80), new THREE.MeshStandardMaterial({ color: 0x334155, roughness: 0.95 }));
            pista.rotation.x = -Math.PI / 2; pista.position.z = -20; pista.receiveShadow = true;
            scene.add(pista);
            const matPasto = new THREE.MeshStandardMaterial({ color: 0x14532d, roughness: 0.95 });
            [-1, 1].forEach(lado => {
                const pasto = new THREE.Mesh(new THREE.PlaneGeometry(3, 80), matPasto);
                pasto.rotation.x = -Math.PI / 2; pasto.position.set(lado * 4.6, -0.01, -20); pasto.receiveShadow = true;
                scene.add(pasto);
            });
            const marcas = [];
            for (let i = 0; i < 12; i++) {
                [-1.7, 1.7].forEach(x => {
                    const marca = new THREE.Mesh(new THREE.BoxGeometry(0.12, 0.02, 1.2), new THREE.MeshStandardMaterial({ color: 0xf8fafc }));
                    marca.position.set(x, 0.011, -i * 6);
                    scene.add(marca); marcas.push(marca);
                });
            }
            const vehiculo = crearVehiculo3D(0x1d4ed8, true);
            vehiculo.position.set(0, 0, 2);
            scene.add(vehiculo);
            _car3D = { scene, camera, renderer, vehiculo, marcas, ultimoTiempo: performance.now() };
            document.getElementById('car-izq-btn').onclick = () => _carrerasCambiarCarril(-1);
            document.getElementById('car-der-btn').onclick = () => _carrerasCambiarCarril(1);
            const acelBtn = document.getElementById('car-acel-btn'), frenoBtn = document.getElementById('car-freno-btn');
            acelBtn.onpointerdown = () => carEstado.acelerando = true;
            acelBtn.onpointerup = acelBtn.onpointerleave = () => carEstado.acelerando = false;
            frenoBtn.onpointerdown = () => carEstado.frenando = true;
            frenoBtn.onpointerup = frenoBtn.onpointerleave = () => carEstado.frenando = false;
            document.removeEventListener('keydown', _carrerasTecla);
            document.addEventListener('keydown', _carrerasTecla);
            document.removeEventListener('keyup', _carrerasTeclaUp);
            document.addEventListener('keyup', _carrerasTeclaUp);
            _rafActivo = requestAnimationFrame(_carrerasLoop);
        }
        function _carrerasLoop() {
            const st = carEstado;
            if (!st || !_car3D || juegoActual !== 'carreras') return;
            const ahora = performance.now();
            const dt = Math.min(0.05, (ahora - _car3D.ultimoTiempo) / 1000);
            _car3D.ultimoTiempo = ahora;
            const laneW = 1.7;
            if (st.activo) {
                const factor = st.acelerando ? 1.5 : (st.frenando ? 0.55 : 1);
                st.puntaje += Math.round(12 * factor * dt);
                st.velocidad = Math.min(15, (7 + st.puntaje / 140) * factor);
                const xObjetivo = (st.carril - 1) * laneW;
                const xAnterior = st.xVisual;
                st.xVisual += (xObjetivo - st.xVisual) * Math.min(1, 8 * dt);
                const velLateral = (st.xVisual - xAnterior) / Math.max(dt, 0.001);
                st.inclinacion += (Math.max(-0.32, Math.min(0.32, velLateral * -0.045)) - st.inclinacion) * Math.min(1, 6 * dt);
                st.proximoSpawn -= dt;
                if (st.proximoSpawn <= 0) {
                    st.proximoSpawn = Math.max(0.55, 1.5 - st.puntaje / 3500);
                    const mesh = crearVehiculo3D(0xdc2626, false);
                    const carril = Math.floor(Math.random() * 3);
                    mesh.position.set((carril - 1) * laneW, 0, -34 - Math.random() * 6);
                    _car3D.scene.add(mesh);
                    st.enemigos.push({ mesh, carril });
                }
                st.enemigos.forEach(en => en.mesh.position.z += st.velocidad * dt);
                _car3D.marcas.forEach(m => { m.position.z += st.velocidad * dt; if (m.position.z > 6) m.position.z -= 72; });
                for (const en of st.enemigos) {
                    const dz = Math.abs(en.mesh.position.z - 2);
                    const dx = Math.abs(en.mesh.position.x - st.xVisual);
                    if (dz < 1.05 && dx < 0.82) { st.activo = false; _carrerasFin(); }
                }
                st.enemigos = st.enemigos.filter(en => {
                    if (en.mesh.position.z > 5) { _car3D.scene.remove(en.mesh); return false; }
                    return true;
                });
                document.getElementById('car-puntaje').textContent = st.puntaje;
                document.getElementById('car-velocidad').textContent = (st.velocidad / 7).toFixed(1) + 'x';
            } else {
                st.fundido = Math.min(1, st.fundido + dt * 2.2);
            }
            _car3D.vehiculo.position.x = st.xVisual;
            _car3D.vehiculo.rotation.z = st.inclinacion;
            _car3D.camera.position.set(st.xVisual * 0.4, 2.4, 6.6);
            _car3D.camera.lookAt(st.xVisual * 0.4, 0.9, -3);
            _car3D.renderer.render(_car3D.scene, _car3D.camera);
            if (st.activo || st.fundido < 1) _rafActivo = requestAnimationFrame(_carrerasLoop);
        }
        function _carrerasFin() {
            const st = carEstado;
            setTimeout(() => {
                alert(`🏎️ ¡Choque! Puntaje final: ${st.puntaje}`);
                guardarPuntaje('carreras', st.puntaje);
            }, 450);
        }

        // ══════════════ PELEA (1 vs CPU) — 3D con Three.js ══════════════
        let peleaEstado = null;
        let _pelea3D = null;
        function crearTecnico3D(colorTraje) {
            const grupo = new THREE.Group();
            const DS = THREE.DoubleSide;
            const matPiel = new THREE.MeshStandardMaterial({ color: 0xf1c27d, roughness: 0.75, side: DS });
            const matTraje = new THREE.MeshStandardMaterial({ color: colorTraje || 0x1d4ed8, roughness: 0.6, side: DS });
            const matFranja = new THREE.MeshStandardMaterial({ color: 0xfbbf24, roughness: 0.4, side: DS });
            const matCasco = new THREE.MeshStandardMaterial({ color: 0xf59e0b, roughness: 0.35, metalness: 0.15, side: DS });
            const matGuante = new THREE.MeshStandardMaterial({ color: 0xf8fafc, roughness: 0.5, side: DS });
            const matBota = new THREE.MeshStandardMaterial({ color: 0x111827, roughness: 0.6, side: DS });
            const torso = new THREE.Mesh(new THREE.BoxGeometry(0.46, 0.6, 0.28), matTraje);
            torso.position.y = 1.15; torso.castShadow = true; grupo.add(torso);
            const franja = new THREE.Mesh(new THREE.BoxGeometry(0.47, 0.08, 0.29), matFranja);
            franja.position.y = 1.27; grupo.add(franja);
            const cabeza = new THREE.Mesh(new THREE.SphereGeometry(0.17, 14, 12), matPiel);
            cabeza.position.y = 1.62; cabeza.castShadow = true; grupo.add(cabeza);
            const casco = new THREE.Mesh(new THREE.SphereGeometry(0.19, 14, 12, 0, Math.PI * 2, 0, Math.PI * 0.55), matCasco);
            casco.position.y = 1.68; grupo.add(casco);
            function crearBrazo(signo) {
                const hombro = new THREE.Group(); hombro.position.set(0.27 * signo, 1.4, 0);
                const sup = new THREE.Mesh(new THREE.CylinderGeometry(0.065, 0.06, 0.32, 8), matTraje);
                sup.position.y = -0.16; sup.castShadow = true; hombro.add(sup);
                const codo = new THREE.Group(); codo.position.y = -0.32; hombro.add(codo);
                const ante = new THREE.Mesh(new THREE.CylinderGeometry(0.055, 0.05, 0.28, 8), matTraje);
                ante.position.y = -0.14; ante.castShadow = true; codo.add(ante);
                const mano = new THREE.Mesh(new THREE.SphereGeometry(0.08, 8, 8), matGuante);
                mano.position.y = -0.30; codo.add(mano);
                return { hombro, codo };
            }
            const brazoIzq = crearBrazo(-1), brazoDer = crearBrazo(1);
            grupo.add(brazoIzq.hombro, brazoDer.hombro);
            function crearPierna(signo) {
                const cadera = new THREE.Group(); cadera.position.set(0.13 * signo, 0.84, 0);
                const muslo = new THREE.Mesh(new THREE.CylinderGeometry(0.08, 0.075, 0.38, 8), matTraje);
                muslo.position.y = -0.19; muslo.castShadow = true; cadera.add(muslo);
                const rodilla = new THREE.Group(); rodilla.position.y = -0.38; cadera.add(rodilla);
                const pantorrilla = new THREE.Mesh(new THREE.CylinderGeometry(0.07, 0.06, 0.36, 8), matTraje);
                pantorrilla.position.y = -0.18; pantorrilla.castShadow = true; rodilla.add(pantorrilla);
                const bota = new THREE.Mesh(new THREE.BoxGeometry(0.15, 0.09, 0.24), matBota);
                bota.position.set(0, -0.37, 0.04); bota.castShadow = true; rodilla.add(bota);
                return { cadera, rodilla };
            }
            const piernaIzq = crearPierna(-1), piernaDer = crearPierna(1);
            grupo.add(piernaIzq.cadera, piernaDer.cadera);
            grupo.userData.partes = { torso, cabeza, brazoIzq, brazoDer, piernaIzq, piernaDer };
            return grupo;
        }
        function crearRobot3D() {
            const grupo = new THREE.Group();
            const DS = THREE.DoubleSide;
            const matCuerpo = new THREE.MeshStandardMaterial({ color: 0x64748b, roughness: 0.4, metalness: 0.5, side: DS });
            const matOscuro = new THREE.MeshStandardMaterial({ color: 0x334155, roughness: 0.5, metalness: 0.4, side: DS });
            const matPanel = new THREE.MeshStandardMaterial({ color: 0x38bdf8, emissive: 0x0369a1, emissiveIntensity: 0.55, roughness: 0.3, side: DS });
            const matOjo = new THREE.MeshStandardMaterial({ color: 0x0ea5e9, emissive: 0x0ea5e9, emissiveIntensity: 1, side: DS });
            const torso = new THREE.Mesh(new THREE.BoxGeometry(0.5, 0.62, 0.32), matCuerpo);
            torso.position.y = 1.15; torso.castShadow = true; grupo.add(torso);
            const panel = new THREE.Mesh(new THREE.BoxGeometry(0.3, 0.12, 0.02), matPanel);
            panel.position.set(0, 1.25, 0.17); grupo.add(panel);
            const cabeza = new THREE.Mesh(new THREE.BoxGeometry(0.28, 0.24, 0.26), matCuerpo);
            cabeza.position.y = 1.62; cabeza.castShadow = true; grupo.add(cabeza);
            const ojo = new THREE.Mesh(new THREE.SphereGeometry(0.045, 8, 8), matOjo);
            ojo.position.set(0.05, 1.62, 0.14); grupo.add(ojo);
            const antena = new THREE.Mesh(new THREE.CylinderGeometry(0.012, 0.012, 0.16, 6), matOscuro);
            antena.position.set(0, 1.82, 0); grupo.add(antena);
            const antenaPunta = new THREE.Mesh(new THREE.SphereGeometry(0.035, 8, 8), matOjo);
            antenaPunta.position.set(0, 1.9, 0); grupo.add(antenaPunta);
            function crearBrazo(signo) {
                const hombro = new THREE.Group(); hombro.position.set(0.3 * signo, 1.4, 0);
                const sup = new THREE.Mesh(new THREE.BoxGeometry(0.12, 0.32, 0.12), matOscuro);
                sup.position.y = -0.16; sup.castShadow = true; hombro.add(sup);
                const codo = new THREE.Group(); codo.position.y = -0.32; hombro.add(codo);
                const ante = new THREE.Mesh(new THREE.BoxGeometry(0.1, 0.28, 0.1), matCuerpo);
                ante.position.y = -0.14; ante.castShadow = true; codo.add(ante);
                const puno = new THREE.Mesh(new THREE.BoxGeometry(0.14, 0.14, 0.14), matOscuro);
                puno.position.y = -0.3; codo.add(puno);
                return { hombro, codo };
            }
            const brazoIzq = crearBrazo(-1), brazoDer = crearBrazo(1);
            grupo.add(brazoIzq.hombro, brazoDer.hombro);
            function crearPierna(signo) {
                const cadera = new THREE.Group(); cadera.position.set(0.15 * signo, 0.84, 0);
                const muslo = new THREE.Mesh(new THREE.BoxGeometry(0.16, 0.38, 0.16), matOscuro);
                muslo.position.y = -0.19; muslo.castShadow = true; cadera.add(muslo);
                const rodilla = new THREE.Group(); rodilla.position.y = -0.38; cadera.add(rodilla);
                const pantorrilla = new THREE.Mesh(new THREE.BoxGeometry(0.14, 0.36, 0.14), matCuerpo);
                pantorrilla.position.y = -0.18; pantorrilla.castShadow = true; rodilla.add(pantorrilla);
                const pie = new THREE.Mesh(new THREE.BoxGeometry(0.18, 0.08, 0.26), matOscuro);
                pie.position.set(0, -0.37, 0.05); pie.castShadow = true; rodilla.add(pie);
                return { cadera, rodilla };
            }
            const piernaIzq = crearPierna(-1), piernaDer = crearPierna(1);
            grupo.add(piernaIzq.cadera, piernaDer.cadera);
            grupo.userData.partes = { torso, cabeza, brazoIzq, brazoDer, piernaIzq, piernaDer, panel, ojo };
            return grupo;
        }
        function _animarPersonaje3D(grupo, est, dt, frente, sentido) {
            const p = grupo.userData.partes;
            est.t += dt;
            const trasero = frente === 'Der' ? 'Izq' : 'Der';
            const brazoFrente = p['brazo' + frente], brazoTrasero = p['brazo' + trasero];
            const piernaFrente = p['pierna' + frente];
            let zFrente = 0.1 * sentido, zTrasero = -0.08 * sentido, cFrenteZ = 0, rodFrenteZ = 0.12 * sentido, torsoY = 0, torsoX = 0;
            if (est.pose === 'golpe') { zFrente = 1.3 * sentido; zTrasero = -0.3 * sentido; torsoY = 0.15 * sentido; }
            else if (est.pose === 'patada') { cFrenteZ = 1.05 * sentido; rodFrenteZ = -0.55 * sentido; zTrasero = -0.35 * sentido; zFrente = 0.2 * sentido; torsoX = -0.08; }
            else if (est.pose === 'bloqueo') { zFrente = 0.9 * sentido; zTrasero = 0.9 * sentido; torsoX = 0.05; }
            let impactoOffset = 0;
            if (est.impacto > 0) { impactoOffset = est.impacto * 0.1; est.impacto = Math.max(0, est.impacto - dt * 3); }
            const bob = est.pose === 'parado' ? Math.sin(est.t * 2.2) * 0.02 : 0;
            const suav = 1 - Math.pow(0.0008, dt);
            brazoFrente.hombro.rotation.z += (zFrente - brazoFrente.hombro.rotation.z) * suav;
            brazoTrasero.hombro.rotation.z += (zTrasero - brazoTrasero.hombro.rotation.z) * suav;
            piernaFrente.cadera.rotation.z += (cFrenteZ - piernaFrente.cadera.rotation.z) * suav;
            piernaFrente.rodilla.rotation.z += (rodFrenteZ - piernaFrente.rodilla.rotation.z) * suav;
            p.torso.rotation.y += (torsoY - p.torso.rotation.y) * suav;
            p.torso.rotation.x += (torsoX - p.torso.rotation.x) * suav;
            grupo.position.y = bob;
            grupo.position.x = grupo.userData.xBase - sentido * impactoOffset;
            if (p.panel) p.panel.material.emissiveIntensity = est.dañado ? 0.95 : 0.55;
            if (p.ojo) { const col = est.dañado ? 0xef4444 : 0x0ea5e9; p.ojo.material.color.setHex(col); p.ojo.material.emissive.setHex(col); }
        }
        function iniciarPelea() {
            const cont = document.getElementById('juego-contenedor');
            cont.innerHTML = `
                <h3 style="margin-top:0;color:var(--carrier-blue);">🥊 Pelea 3D — Técnico vs Robot Averiado</h3>
                <div class="pelea-rondas" id="pelea-rondas">Ronda 1 — Rondas ganadas: Tú 0 · CPU 0</div>
                <div class="pelea-barras">
                    <div class="pelea-barra-fila">🧑‍🔧 <div class="pelea-barra-fondo"><div class="pelea-barra-relleno" id="pelea-vida-jugador" style="width:100%"></div></div></div>
                    <div class="pelea-barra-fila">🤖 <div class="pelea-barra-fondo"><div class="pelea-barra-relleno cpu" id="pelea-vida-cpu" style="width:100%"></div></div></div>
                </div>
                <div id="pelea-3d-contenedor" style="width:100%;max-width:420px;height:230px;margin:0 auto;border-radius:12px;overflow:hidden;background:#0f172a;"></div>
                <div class="pelea-botones" style="margin-top:14px;">
                    <button id="pelea-golpe-btn">👊 Golpe</button>
                    <button id="pelea-patada-btn">🦵 Patada</button>
                    <button class="btn-bloquear" id="pelea-bloquear-btn">🛡️ Bloquear</button>
                </div>
                <p style="text-align:center;font-size:.8rem;color:#94a3b8;margin-top:10px;">Gana 2 de 3 rondas. Bloquear reduce mucho el daño del siguiente golpe del robot. Personajes 3D low-poly renderizados en tiempo real.</p>
                <p style="text-align:center;margin-top:10px;"><button class="btn-primary" style="width:auto;padding:8px 18px;" onclick="iniciarPelea()">🔄 Reiniciar pelea</button></p>
            `;
            peleaEstado = {
                vidaJ: 100, vidaC: 100, rondasJ: 0, rondasC: 0, ronda: 1,
                bloqueandoJ: false, cooldownJ: false, activo: true, terminado: false
            };
            const contenedor3D = document.getElementById('pelea-3d-contenedor');
            if (typeof THREE === 'undefined') {
                contenedor3D.innerHTML = '<p style="color:#f8fafc;text-align:center;padding-top:95px;">No se pudo cargar el motor 3D (revisa tu conexión a internet).</p>';
                return;
            }
            if (_pelea3D && _pelea3D.renderer) { try { _pelea3D.renderer.dispose(); } catch (e) {} }
            const ancho = contenedor3D.clientWidth || 380, alto = 230;
            const scene = new THREE.Scene();
            scene.background = new THREE.Color(0x0f172a);
            scene.fog = new THREE.Fog(0x0f172a, 4, 9);
            const camera = new THREE.PerspectiveCamera(38, ancho / alto, 0.1, 20);
            camera.position.set(0, 1.55, 3.4);
            camera.lookAt(0, 1.15, 0);
            const renderer = new THREE.WebGLRenderer({ antialias: true });
            renderer.setSize(ancho, alto);
            renderer.shadowMap.enabled = true;
            contenedor3D.innerHTML = '';
            contenedor3D.appendChild(renderer.domElement);
            scene.add(new THREE.HemisphereLight(0x8fb8ff, 0x1a2130, 0.7));
            const luzDireccional = new THREE.DirectionalLight(0xfff2d9, 1.05);
            luzDireccional.position.set(2.5, 4, 2);
            luzDireccional.castShadow = true;
            luzDireccional.shadow.mapSize.set(512, 512);
            scene.add(luzDireccional);
            const piso = new THREE.Mesh(new THREE.PlaneGeometry(10, 10), new THREE.MeshStandardMaterial({ color: 0x1e293b, roughness: 0.9 }));
            piso.rotation.x = -Math.PI / 2;
            piso.receiveShadow = true;
            scene.add(piso);
            const tecnico = crearTecnico3D(0x1d4ed8);
            tecnico.position.set(-1, 0, 0);
            tecnico.userData.xBase = -1;
            scene.add(tecnico);
            const robot = crearRobot3D();
            robot.position.set(1, 0, 0);
            robot.userData.xBase = 1;
            scene.add(robot);
            _pelea3D = {
                scene, camera, renderer, tecnico, robot,
                estJ: { pose: 'parado', t: 0, impacto: 0, dañado: false },
                estC: { pose: 'parado', t: Math.random() * 10, impacto: 0, dañado: false },
                temblorCamara: 0, ultimoTiempo: performance.now()
            };
            document.getElementById('pelea-golpe-btn').onclick = () => _peleaAccionJugador('golpe');
            document.getElementById('pelea-patada-btn').onclick = () => _peleaAccionJugador('patada');
            document.getElementById('pelea-bloquear-btn').onclick = () => _peleaAccionJugador('bloquear');
            const cpuInterval = setInterval(_peleaTurnoCPU, 1400);
            _intervalosActivos.push(cpuInterval);
            _rafActivo = requestAnimationFrame(_peleaLoop);
        }
        function _peleaAccionJugador(accion) {
            const st = peleaEstado;
            if (!st || !st.activo || st.cooldownJ || juegoActual !== 'pelea' || !_pelea3D) return;
            if (accion === 'golpe') {
                st.vidaC = Math.max(0, st.vidaC - 8);
                _pelea3D.estJ.pose = 'golpe';
                _pelea3D.estC.dañado = true; _pelea3D.estC.impacto = 1;
                _pelea3D.temblorCamara = 0.05;
                setTimeout(() => { _pelea3D.estJ.pose = 'parado'; _pelea3D.estC.dañado = false; }, 220);
            } else if (accion === 'patada') {
                st.vidaC = Math.max(0, st.vidaC - 14);
                _pelea3D.estJ.pose = 'patada';
                _pelea3D.estC.dañado = true; _pelea3D.estC.impacto = 1.6;
                _pelea3D.temblorCamara = 0.08;
                setTimeout(() => { _pelea3D.estJ.pose = 'parado'; _pelea3D.estC.dañado = false; }, 280);
            } else if (accion === 'bloquear') {
                st.bloqueandoJ = true;
                _pelea3D.estJ.pose = 'bloqueo';
                setTimeout(() => { st.bloqueandoJ = false; _pelea3D.estJ.pose = 'parado'; }, 1300);
            }
            st.cooldownJ = true;
            setTimeout(() => { st.cooldownJ = false; }, accion === 'patada' ? 850 : 400);
            _peleaActualizarUI();
            _peleaCheckFinRonda();
        }
        function _peleaTurnoCPU() {
            const st = peleaEstado;
            if (!st || !st.activo || st.terminado || juegoActual !== 'pelea' || !_pelea3D) return;
            const dado = Math.random();
            const accion = dado < 0.55 ? 'golpe' : (dado < 0.85 ? 'patada' : 'nada');
            if (accion === 'nada') return;
            let daño = accion === 'golpe' ? (7 + Math.random() * 4) : (12 + Math.random() * 6);
            if (st.bloqueandoJ) daño *= 0.25;
            st.vidaJ = Math.max(0, st.vidaJ - daño);
            _pelea3D.estC.pose = accion;
            _pelea3D.temblorCamara = accion === 'patada' ? 0.08 : 0.05;
            setTimeout(() => { _pelea3D.estC.pose = 'parado'; }, 240);
            if (!st.bloqueandoJ) {
                _pelea3D.estJ.dañado = true; _pelea3D.estJ.impacto = accion === 'patada' ? 1.6 : 1;
                setTimeout(() => { _pelea3D.estJ.dañado = false; }, 220);
            }
            _peleaActualizarUI();
            _peleaCheckFinRonda();
        }
        function _peleaActualizarUI() {
            const st = peleaEstado;
            document.getElementById('pelea-vida-jugador').style.width = st.vidaJ + '%';
            document.getElementById('pelea-vida-cpu').style.width = st.vidaC + '%';
            document.getElementById('pelea-rondas').textContent = `Ronda ${st.ronda} — Rondas ganadas: Tú ${st.rondasJ} · CPU ${st.rondasC}`;
        }
        function _peleaCheckFinRonda() {
            const st = peleaEstado;
            if (st.terminado) return;
            if (st.vidaJ <= 0 || st.vidaC <= 0) {
                st.terminado = true;
                if (st.vidaC <= 0) st.rondasJ++; else st.rondasC++;
                const ganoMatch = st.rondasJ >= 2 || st.rondasC >= 2;
                setTimeout(() => {
                    if (ganoMatch) {
                        st.activo = false;
                        const puntaje = st.rondasJ * 100 + Math.round(st.vidaJ);
                        alert(st.rondasJ > st.rondasC ? `🏆 ¡Ganaste la pelea! Puntaje: ${puntaje}` : `😵 Perdiste la pelea. Puntaje: ${puntaje}`);
                        guardarPuntaje('pelea', puntaje);
                    } else {
                        st.ronda++;
                        st.vidaJ = 100; st.vidaC = 100; st.terminado = false;
                        _peleaActualizarUI();
                    }
                }, 400);
            }
        }
        function _peleaLoop() {
            const st = peleaEstado;
            if (!st || !_pelea3D || juegoActual !== 'pelea') return;
            const ahora = performance.now();
            const dt = Math.min(0.05, (ahora - _pelea3D.ultimoTiempo) / 1000);
            _pelea3D.ultimoTiempo = ahora;
            _animarPersonaje3D(_pelea3D.tecnico, _pelea3D.estJ, dt, 'Der', 1);
            _animarPersonaje3D(_pelea3D.robot, _pelea3D.estC, dt, 'Izq', -1);
            if (_pelea3D.temblorCamara > 0.001) {
                _pelea3D.camera.position.x = (Math.random() - 0.5) * _pelea3D.temblorCamara;
                _pelea3D.camera.position.y = 1.55 + (Math.random() - 0.5) * _pelea3D.temblorCamara;
                _pelea3D.temblorCamara *= 0.85;
            } else {
                _pelea3D.camera.position.x = 0; _pelea3D.camera.position.y = 1.55;
            }
            _pelea3D.camera.lookAt(0, 1.15, 0);
            _pelea3D.renderer.render(_pelea3D.scene, _pelea3D.camera);
            _rafActivo = requestAnimationFrame(_peleaLoop);
        }

        // ══════════════ TETRIS ══════════════
        const TET_PIEZAS = {
            I: { bloques: [[0,1],[1,1],[2,1],[3,1]], color: '#22d3ee' },
            O: { bloques: [[1,0],[2,0],[1,1],[2,1]], color: '#facc15' },
            T: { bloques: [[1,0],[0,1],[1,1],[2,1]], color: '#a78bfa' },
            S: { bloques: [[1,0],[2,0],[0,1],[1,1]], color: '#4ade80' },
            Z: { bloques: [[0,0],[1,0],[1,1],[2,1]], color: '#f87171' },
            J: { bloques: [[0,0],[0,1],[1,1],[2,1]], color: '#60a5fa' },
            L: { bloques: [[2,0],[0,1],[1,1],[2,1]], color: '#fb923c' }
        };
        const TET_COLS = 10, TET_FILAS = 20, TET_CELDA = 18;
        let tetEstado = null;
        function _tetrisTeclaDown(e) {
            const st = tetEstado;
            if (!st || !st.activo || juegoActual !== 'tetris') return;
            if (e.key === 'ArrowLeft') { e.preventDefault(); _tetMover(-1); }
            else if (e.key === 'ArrowRight') { e.preventDefault(); _tetMover(1); }
            else if (e.key === 'ArrowDown') { e.preventDefault(); _tetCaida(); }
            else if (e.key === 'ArrowUp') { e.preventDefault(); _tetRotar(); }
            else if (e.key === ' ' || e.code === 'Space') { e.preventDefault(); _tetHardDrop(); }
        }
        function iniciarTetris() {
            const cont = document.getElementById('juego-contenedor');
            cont.innerHTML = `
                <h3 style="margin-top:0;color:var(--carrier-blue);">🧩 Tetris</h3>
                <div class="juegos-stats"><span>⭐ Puntaje: <span id="tet-puntaje">0</span></span><span>📶 Nivel: <span id="tet-nivel">1</span></span><span>📏 Líneas: <span id="tet-lineas">0</span></span></div>
                <div style="display:flex;gap:14px;justify-content:center;align-items:flex-start;flex-wrap:wrap;">
                    <canvas id="tet-canvas" class="juegos-canvas" width="${TET_COLS*TET_CELDA}" height="${TET_FILAS*TET_CELDA}"></canvas>
                    <div style="text-align:center;">
                        <p style="font-size:.75rem;color:#94a3b8;margin:0 0 4px;font-weight:700;">Siguiente</p>
                        <canvas id="tet-siguiente-canvas" class="juegos-canvas" width="72" height="72"></canvas>
                    </div>
                </div>
                <div class="juegos-controles-touch">
                    <button id="tet-izq-btn">⬅️</button><button id="tet-rot-btn">🔄</button><button id="tet-der-btn">➡️</button><button id="tet-baja-btn">⬇️</button>
                </div>
                <p style="text-align:center;font-size:.8rem;color:#94a3b8;margin-top:8px;">Flechas para mover/rotar, Espacio para caída rápida. La silueta punteada muestra dónde caerá la pieza.</p>
                <p style="text-align:center;margin-top:10px;"><button class="btn-primary" style="width:auto;padding:8px 18px;" onclick="iniciarTetris()">🔄 Reiniciar</button></p>
            `;
            tetEstado = {
                tablero: Array.from({length: TET_FILAS}, () => Array(TET_COLS).fill(null)),
                puntaje: 0, lineas: 0, nivel: 1, activo: true, velocidad: 750, siguienteTipo: null
            };
            document.getElementById('tet-izq-btn').onclick = () => _tetMover(-1);
            document.getElementById('tet-der-btn').onclick = () => _tetMover(1);
            document.getElementById('tet-rot-btn').onclick = () => _tetRotar();
            document.getElementById('tet-baja-btn').onclick = () => _tetCaida();
            document.removeEventListener('keydown', _tetrisTeclaDown);
            document.addEventListener('keydown', _tetrisTeclaDown);
            _tetNuevaPieza();
            const dropInterval = setInterval(() => _tetCaida(), tetEstado.velocidad);
            tetEstado._intervaloId = dropInterval;
            _intervalosActivos.push(dropInterval);
            _tetRender();
        }
        function _tetNuevaPieza() {
            const st = tetEstado;
            const tipos = Object.keys(TET_PIEZAS);
            const tipo = st.siguienteTipo || tipos[Math.floor(Math.random() * tipos.length)];
            const def = TET_PIEZAS[tipo];
            st.pieza = { tipo, color: def.color, bloques: def.bloques.map(b => [...b]), x: 3, y: -1 };
            st.siguienteTipo = tipos[Math.floor(Math.random() * tipos.length)];
            _tetRenderSiguiente();
            if (_tetColisiona(st.pieza.bloques, st.pieza.x, st.pieza.y)) {
                st.activo = false;
                clearInterval(st._intervaloId);
                setTimeout(() => {
                    alert(`🧩 Juego terminado. Puntaje final: ${st.puntaje}`);
                    guardarPuntaje('tetris', st.puntaje);
                }, 80);
            }
        }
        function _tetRenderSiguiente() {
            const st = tetEstado;
            const canvas = document.getElementById('tet-siguiente-canvas');
            if (!canvas || !st.siguienteTipo) return;
            const ctx = canvas.getContext('2d');
            ctx.fillStyle = '#0f172a';
            ctx.fillRect(0, 0, canvas.width, canvas.height);
            const def = TET_PIEZAS[st.siguienteTipo];
            const cel = 15;
            def.bloques.forEach(([bx, by]) => _tetDibujarBloque(ctx, 8 + bx * cel, 8 + by * cel, cel, def.color));
        }
        function _tetDibujarBloque(ctx, px, py, tam, color, alpha) {
            ctx.globalAlpha = alpha === undefined ? 1 : alpha;
            ctx.fillStyle = color;
            ctx.fillRect(px + 1, py + 1, tam - 2, tam - 2);
            ctx.fillStyle = 'rgba(255,255,255,0.35)';
            ctx.fillRect(px + 1, py + 1, tam - 2, 3);
            ctx.fillRect(px + 1, py + 1, 3, tam - 2);
            ctx.fillStyle = 'rgba(0,0,0,0.28)';
            ctx.fillRect(px + 1, py + tam - 4, tam - 2, 3);
            ctx.fillRect(px + tam - 4, py + 1, 3, tam - 2);
            ctx.globalAlpha = 1;
        }
        function _tetColisiona(bloques, px, py) {
            const st = tetEstado;
            for (const [bx, by] of bloques) {
                const x = px + bx, y = py + by;
                if (x < 0 || x >= TET_COLS || y >= TET_FILAS) return true;
                if (y >= 0 && st.tablero[y][x]) return true;
            }
            return false;
        }
        function _tetMover(dx) {
            const st = tetEstado;
            if (!st || !st.activo) return;
            if (!_tetColisiona(st.pieza.bloques, st.pieza.x + dx, st.pieza.y)) {
                st.pieza.x += dx;
                _tetRender();
            }
        }
        function _tetRotar() {
            const st = tetEstado;
            if (!st || !st.activo || st.pieza.tipo === 'O') { _tetRender(); return; }
            const rotados = st.pieza.bloques.map(([x, y]) => [3 - y, x]);
            for (const dx of [0, -1, 1, -2, 2]) {
                if (!_tetColisiona(rotados, st.pieza.x + dx, st.pieza.y)) {
                    st.pieza.bloques = rotados;
                    st.pieza.x += dx;
                    _tetRender();
                    return;
                }
            }
        }
        function _tetCaida() {
            const st = tetEstado;
            if (!st || !st.activo) return;
            if (!_tetColisiona(st.pieza.bloques, st.pieza.x, st.pieza.y + 1)) {
                st.pieza.y += 1;
            } else {
                _tetFijarPieza();
            }
            _tetRender();
        }
        function _tetHardDrop() {
            const st = tetEstado;
            if (!st || !st.activo) return;
            while (!_tetColisiona(st.pieza.bloques, st.pieza.x, st.pieza.y + 1)) st.pieza.y += 1;
            _tetFijarPieza();
            _tetRender();
        }
        function _tetFijarPieza() {
            const st = tetEstado;
            st.pieza.bloques.forEach(([bx, by]) => {
                const x = st.pieza.x + bx, y = st.pieza.y + by;
                if (y >= 0) st.tablero[y][x] = st.pieza.color;
            });
            let lineasLimpiadas = 0;
            for (let y = TET_FILAS - 1; y >= 0; y--) {
                if (st.tablero[y].every(c => c)) {
                    st.tablero.splice(y, 1);
                    st.tablero.unshift(Array(TET_COLS).fill(null));
                    lineasLimpiadas++;
                    y++;
                }
            }
            if (lineasLimpiadas > 0) {
                const puntosBase = [0, 100, 300, 500, 800][lineasLimpiadas] || 800;
                st.puntaje += puntosBase * st.nivel;
                st.lineas += lineasLimpiadas;
                const nuevoNivel = 1 + Math.floor(st.lineas / 10);
                if (nuevoNivel !== st.nivel) {
                    st.nivel = nuevoNivel;
                    clearInterval(st._intervaloId);
                    st.velocidad = Math.max(120, 750 - (st.nivel - 1) * 60);
                    const idx = _intervalosActivos.indexOf(st._intervaloId);
                    if (idx >= 0) _intervalosActivos.splice(idx, 1);
                    st._intervaloId = setInterval(() => _tetCaida(), st.velocidad);
                    _intervalosActivos.push(st._intervaloId);
                }
                document.getElementById('tet-puntaje').textContent = st.puntaje;
                document.getElementById('tet-nivel').textContent = st.nivel;
                document.getElementById('tet-lineas').textContent = st.lineas;
            }
            _tetNuevaPieza();
        }
        function _tetPosicionFantasma() {
            const st = tetEstado;
            let y = st.pieza.y;
            while (!_tetColisiona(st.pieza.bloques, st.pieza.x, y + 1)) y++;
            return y;
        }
        function _tetRender() {
            const st = tetEstado;
            if (!st) return;
            const canvas = document.getElementById('tet-canvas');
            if (!canvas) return;
            const ctx = canvas.getContext('2d');
            const fondo = ctx.createLinearGradient(0, 0, 0, canvas.height);
            fondo.addColorStop(0, '#0f172a'); fondo.addColorStop(1, '#1e293b');
            ctx.fillStyle = fondo;
            ctx.fillRect(0, 0, canvas.width, canvas.height);
            ctx.strokeStyle = 'rgba(148,163,184,0.08)';
            for (let x = 1; x < TET_COLS; x++) { ctx.beginPath(); ctx.moveTo(x*TET_CELDA,0); ctx.lineTo(x*TET_CELDA,canvas.height); ctx.stroke(); }
            for (let y = 1; y < TET_FILAS; y++) { ctx.beginPath(); ctx.moveTo(0,y*TET_CELDA); ctx.lineTo(canvas.width,y*TET_CELDA); ctx.stroke(); }
            for (let y = 0; y < TET_FILAS; y++) {
                for (let x = 0; x < TET_COLS; x++) {
                    if (st.tablero[y][x]) _tetDibujarBloque(ctx, x * TET_CELDA, y * TET_CELDA, TET_CELDA, st.tablero[y][x]);
                }
            }
            if (st.activo && st.pieza) {
                const yFantasma = _tetPosicionFantasma();
                st.pieza.bloques.forEach(([bx, by]) => {
                    const x = st.pieza.x + bx, y = yFantasma + by;
                    if (y >= 0) {
                        ctx.strokeStyle = st.pieza.color; ctx.lineWidth = 2; ctx.globalAlpha = 0.55;
                        ctx.strokeRect(x * TET_CELDA + 2, y * TET_CELDA + 2, TET_CELDA - 4, TET_CELDA - 4);
                        ctx.globalAlpha = 1;
                    }
                });
                st.pieza.bloques.forEach(([bx, by]) => {
                    const x = st.pieza.x + bx, y = st.pieza.y + by;
                    if (y >= 0) _tetDibujarBloque(ctx, x * TET_CELDA, y * TET_CELDA, TET_CELDA, st.pieza.color);
                });
            }
        }

        cambiarJuego('memoria');
    </script>
    """
    return HTMLResponse(content=pagina_con_menu("🎮 Juegos", contenido, "juegos", extra_scripts='<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>'))

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
        .hor-input.dirty { border-color:#f59e0b !important; background:#fffbeb; }
        .hor-skel { border-radius:12px; overflow:hidden; background:white; box-shadow:0 2px 12px rgba(0,43,91,0.08); padding:16px; }
        .hor-skel-row { display:flex; gap:8px; margin-bottom:10px; }
        .hor-skel-cell { height:34px; border-radius:6px; background:linear-gradient(90deg,#eef1f5 25%,#e2e6ec 37%,#eef1f5 63%); background-size:400% 100%; animation:hor-shimmer 1.3s ease infinite; }
        @keyframes hor-shimmer { 0%{background-position:100% 0} 100%{background-position:0 0} }
        .hor-save-bar { display:flex; align-items:center; gap:10px; font-size:.82rem; color:#6b7280; }
        .hor-save-bar.dirty { color:#d97706; font-weight:600; }
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
            <input type="date" id="semanaInput" style="width:auto; margin-bottom:0;" onchange="onCambioSemana()">
            <button class="btn-primary" id="btnGuardarHorarios" style="width:auto; padding:10px 22px;" onclick="guardarHorarios()">💾 Guardar Horarios</button>
            <button class="btn-success" style="width:auto; padding:10px 22px;" onclick="abrirModalImportacion()">📂 Importar Excel</button>
            <span id="horDirtyIndicator" class="hor-save-bar"></span>
        </div>
        <div id="tablaHorarios" style="overflow-x:auto;"></div>

        <div style="display:flex; align-items:center; justify-content:space-between; margin-top:32px; flex-wrap:wrap; gap:10px;">
            <div class="section-title" style="margin:0;">📊 Resumen Semanal de Asistencia</div>
            <button class="btn-primary" style="width:auto; padding:8px 18px; font-size:.85rem;" onclick="exportarResumenSemanalExcel()">📊 Exportar Excel</button>
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

        // -- Horarios Semanales: estado (debe declararse antes de las llamadas
        //    de abajo, ya que cargarHorarios() usa estas variables `let` de
        //    inmediato y de lo contrario cae en su temporal dead zone) --------
        let tecnicosData = [];
        let horariosData = {};
        const diasSemana = ['Lunes','Martes','Miércoles','Jueves','Viernes','Sábado'];

        // Cache en memoria por semana: evita re-descargar todo al ir y venir
        // entre semanas ya visitadas -> la tabla aparece instantánea y de
        // fondo se refresca por si hubo cambios (stale-while-revalidate).
        let horCache = {};
        let horSemanaActual = null;
        let horDirty = false;
        let horCargaId = 0; // evita que una respuesta vieja pise una más nueva

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
        // (declaraciones movidas arriba, antes de cargarHorarios())

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

        function onCambioSemana() {
            if (horDirty && !confirm('Tienes cambios de horario sin guardar. Si cambias de semana se perderán. ¿Continuar de todos modos?')) {
                document.getElementById('semanaInput').value = horSemanaActual || document.getElementById('semanaInput').value;
                return;
            }
            cargarHorarios();
        }

        function marcarHorDirty(inputEl) {
            if (inputEl) inputEl.classList.add('dirty');
            if (horDirty) return;
            horDirty = true;
            const ind = document.getElementById('horDirtyIndicator');
            if (ind) { ind.textContent = '● Cambios sin guardar'; ind.classList.add('dirty'); }
        }

        function limpiarHorDirty() {
            horDirty = false;
            const ind = document.getElementById('horDirtyIndicator');
            if (ind) { ind.textContent = ''; ind.classList.remove('dirty'); }
            document.querySelectorAll('.hor-input.dirty').forEach(el => el.classList.remove('dirty'));
        }

        function mostrarSkeletonHorarios() {
            let filas = '';
            for (let i = 0; i < 5; i++) {
                filas += '<div class="hor-skel-row"><div class="hor-skel-cell" style="width:140px;"></div>'
                    + Array.from({length:6}).map(() => '<div class="hor-skel-cell" style="flex:1;"></div>').join('')
                    + '</div>';
            }
            document.getElementById('tablaHorarios').innerHTML = `<div class="hor-skel">${filas}</div>`;
        }

        async function cargarHorarios() {
            const semana = document.getElementById('semanaInput').value;
            if (!semana) return;
            horSemanaActual = semana;
            limpiarHorDirty();
            const miCargaId = ++horCargaId;

            // 1. Si ya tenemos esta semana en cache, renderizar de inmediato
            //    (percepción de carga instantánea) y refrescar en segundo plano.
            const cacheado = horCache[semana];
            if (cacheado) {
                renderHorarios(semana, cacheado);
            } else {
                mostrarSkeletonHorarios();
            }

            try {
                const [tecRes, horRes, resRes, comRes] = await Promise.all([
                    fetchAuth('/api/usuarios/'),
                    fetchAuth(`/api/horarios/?semana=${semana}`),
                    fetchAuth(`/api/horarios/resumen?semana=${semana}`),
                    fetchAuth(`/api/horarios/comentarios?semana=${semana}`)
                ]);
                const tecRaw = await tecRes.json();
                const horarios = await horRes.json();
                const resumen = await resRes.json();
                const comentarios = comRes.ok ? await comRes.json() : {};

                // Si el usuario ya cambió de semana mientras esto cargaba, descartar.
                if (miCargaId !== horCargaId) return;

                const datos = {
                    tecnicos: (Array.isArray(tecRaw) ? tecRaw : []).filter(u => u.role === 'tecnico' || u.role === 'lider'),
                    horarios, resumen, comentarios
                };
                horCache[semana] = datos;
                renderHorarios(semana, datos);
            } catch(e) {
                console.error('Error cargando horarios:', e);
                if (miCargaId === horCargaId && !cacheado) {
                    document.getElementById('tablaHorarios').innerHTML = '<p style="color:#dc2626;">Error al cargar horarios.</p>';
                }
            }
        }

        function renderHorarios(semana, datos) {
            tecnicosData = datos.tecnicos;
            horariosData = {};
            datos.horarios.forEach(h => { horariosData[h.username+'_'+h.fecha] = h; });

            const fechas = fechasDeSemana(semana);

            // Tabla editable de horarios
            let html = '<table class="horario-tbl"><thead><tr><th>Técnico</th>';
            fechas.forEach((f,i) => { html += `<th>${diasSemana[i]}<br><small style="font-weight:400;opacity:.8;">${f.slice(5)}</small></th>`; });
            html += '</tr></thead><tbody>';
            tecnicosData.forEach(tec => {
                html += `<tr><td>${tec.nombre_completo || tec.username}</td>`;
                fechas.forEach(f => {
                    const h = horariosData[tec.username+'_'+f] || {};
                    html += `<td>
                        <div style="display:flex;flex-direction:column;gap:4px;align-items:center;">
                            <input type="time" class="hor-input" data-user="${tec.username}" data-fecha="${f}" data-tipo="entrada" value="${h.hora_entrada||''}" title="Entrada" oninput="marcarHorDirty(this)">
                            <input type="time" class="hor-input" data-user="${tec.username}" data-fecha="${f}" data-tipo="salida"  value="${h.hora_salida||''}"  title="Salida" oninput="marcarHorDirty(this)">
                        </div>
                    </td>`;
                });
                html += '</tr>';
            });
            html += '</tbody></table>';
            document.getElementById('tablaHorarios').innerHTML = html;

            // Tabla de resumen de asistencia real
            const nombreMap = {};
            tecnicosData.forEach(t => { nombreMap[t.username] = t.nombre_completo || t.username; });
            renderResumen(datos.resumen, fechas, datos.comentarios, semana, nombreMap);
        }

        function renderResumen(resumen, fechas, comentarios, semana, nombreMap) {
            comentarios = comentarios || {};
            nombreMap = nombreMap || {};
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
                html += `<tr><td>${nombreMap[tec] || tec}</td>`;
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

        async function exportarResumenSemanalExcel() {
            const el = document.getElementById('resumenSemanalWrap');
            if (!el || !el.querySelector('table')) {
                alert('No hay datos de resumen semanal para exportar.');
                return;
            }
            const semana = document.getElementById('semanaInput').value;
            if (!semana) {
                alert('Selecciona primero la semana.');
                return;
            }
            const btn = event && event.target ? event.target.closest('button') : null;
            const textoOriginal = btn ? btn.innerHTML : null;
            if (btn) { btn.disabled = true; btn.innerHTML = '⏳ Generando...'; }
            try {
                const res = await fetchAuth(`/api/horarios/resumen/excel?semana=${semana}`);
                if (!res.ok) throw new Error('Respuesta no exitosa del servidor');
                const blob = await res.blob();
                const url = window.URL.createObjectURL(blob);
                const link = document.createElement('a');
                link.href = url;
                link.download = `resumen_semanal_asistencia_${semana}.xlsx`;
                document.body.appendChild(link);
                link.click();
                link.remove();
                window.URL.revokeObjectURL(url);
            } catch (e) {
                console.error('Error exportando Excel del resumen semanal:', e);
                alert('No se pudo generar el Excel. Intenta nuevamente.');
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

        function _horarioToast(texto, tipo) {
            const t = document.createElement('div');
            const bg = tipo === 'error' ? '#dc2626' : '#16a34a';
            t.style.cssText = `position:fixed;bottom:28px;left:50%;transform:translateX(-50%);background:${bg};color:white;padding:14px 28px;border-radius:50px;font-weight:700;font-size:0.95rem;box-shadow:0 4px 20px rgba(0,0,0,0.2);z-index:600;`;
            t.textContent = texto;
            document.body.appendChild(t);
            setTimeout(() => t.remove(), 4000);
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

            const btn = document.getElementById('btnGuardarHorarios');
            const textoOriginal = btn ? btn.innerHTML : null;
            if (btn) { btn.disabled = true; btn.innerHTML = '⏳ Guardando...'; }

            try {
                const res = await fetchAuth('/api/horarios/', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({registros})});
                const data = await res.json();
                if (data.ok) {
                    delete horCache[semana]; // invalidar cache: hay cambios reales
                    limpiarHorDirty();
                    let msg = `✅ Guardado: ${data.guardados} horarios, ${data.eliminados} días libres.`;
                    if (data.notificados > 0) {
                        msg += ` 📅 Se notificó a ${data.notificados} técnico${data.notificados === 1 ? '' : 's'}.`;
                    }
                    _horarioToast(msg, 'ok');
                    cargarHorarios();
                } else {
                    _horarioToast('❌ Error al guardar el horario.', 'error');
                }
            } catch(e) {
                _horarioToast('❌ Error al guardar horarios.', 'error');
            } finally {
                if (btn) { btn.disabled = false; btn.innerHTML = textoOriginal; }
            }
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
                    delete horCache[semana]; // invalidar cache: hay cambios reales
                    const el = document.getElementById('impResultado');
                    let msg = `✅ Importación exitosa: ${data.guardados} horarios guardados, ${data.eliminados} eliminados.`;
                    if (data.notificados > 0) {
                        msg += ` 📅 Se notificó a ${data.notificados} técnico${data.notificados === 1 ? '' : 's'}.`;
                    }
                    el.textContent = msg;
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
    <script>if (window.role !== 'tecnico' && window.role !== 'admin' && window.role !== 'lider') { window.location.href = '/app/dashboard'; }</script>

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

      /* Banner de alerta de horario actualizado */
      .ct-horario-banner {
        display:none;
        align-items:center; gap:12px;
        background:#eff6ff; border:1px solid #bfdbfe; color:#1e40af;
        border-radius:14px; padding:14px 16px; margin-bottom:16px;
        font-size:14px; line-height:1.4;
      }
      .ct-horario-banner.show { display:flex; }
      .ct-horario-banner .ct-hb-icon { font-size:22px; flex-shrink:0; }
      .ct-horario-banner .ct-hb-text { flex:1; }
      .ct-horario-banner .ct-hb-close {
        background:none; border:none; color:#1e40af; font-size:18px;
        cursor:pointer; padding:4px 8px; flex-shrink:0; opacity:.7;
      }
      .ct-horario-banner .ct-hb-close:hover { opacity:1; }
    </style>

    <div class="ct-wrap">

      <!-- Alerta: tu horario cambió -->
      <div class="ct-horario-banner" id="ctHorarioBanner">
        <span class="ct-hb-icon">📅</span>
        <span class="ct-hb-text" id="ctHorarioBannerTexto">Tu horario fue actualizado.</span>
        <button class="ct-hb-close" onclick="_ctCerrarAlertaHorario()" title="Entendido">✕</button>
      </div>


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

    // ── Alerta de horario actualizado (in-app, persiste hasta que se cierre) ──
    var _ctAlertasHorarioIds = [];

    async function _ctCargarAlertaHorario() {
      try {
        var res = await window.fetchAuth('/api/horarios/alertas');
        var alertas = await res.json();
        if (!alertas || !alertas.length) return;
        _ctAlertasHorarioIds = alertas.map(function(a){ return a.id; });
        var semanas = alertas.map(function(a){ return a.semana; })
          .filter(function(v,i,arr){ return arr.indexOf(v)===i; });
        var texto = semanas.length === 1
          ? 'Tu horario para la semana del ' + semanas[0] + ' fue actualizado.'
          : 'Tu horario fue actualizado para ' + semanas.length + ' semanas.';
        document.getElementById('ctHorarioBannerTexto').textContent = texto;
        document.getElementById('ctHorarioBanner').classList.add('show');
      } catch(e) {}
    }

    async function _ctCerrarAlertaHorario() {
      document.getElementById('ctHorarioBanner').classList.remove('show');
      if (!_ctAlertasHorarioIds.length) return;
      try {
        await window.fetchAuth('/api/horarios/alertas/marcar-visto', {
          method: 'POST',
          headers: {'Content-Type':'application/json'},
          body: JSON.stringify({ ids: _ctAlertasHorarioIds })
        });
      } catch(e) {}
      _ctAlertasHorarioIds = [];
    }

    _ctCargarAlertaHorario();

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

# ============================================================
# PÁGINAS PÚBLICAS (sin login) — para solicitar Google AdSense
# ------------------------------------------------------------
# Cómo usar:
#   1. Copia el bloque completo (los 3 @router.get) y pégalo
#      dentro de tu archivo web_router.py, junto a las demás rutas.
#   2. Reemplaza "ca-pub-5166749876470166" por tu ID real de
#      AdSense cuando lo tengas (Anuncios → Configuración → ID de editor).
#   3. Cuando solicites la revisión en Google AdSense, usa la URL
#      pública de tu dominio, por ejemplo: https://tu-dominio.com/
#      (esta ruta "/" es la que Google va a rastrear).
#   4. Ajusta los textos de contacto, teléfono, etc. con tus datos reales.
# ============================================================

PUBLIC_STYLE = """
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<style>
    * { box-sizing: border-box; font-family: 'Inter', sans-serif; margin:0; padding:0; }
    body { background:#f7f9fc; color:#1f2937; line-height:1.7; }
    header.pub-header {
        background: linear-gradient(135deg,#002B5B 0%,#0057A8 100%);
        color:white; padding: 20px 24px; display:flex; align-items:center;
        justify-content:space-between; flex-wrap:wrap; gap:12px;
    }
    header.pub-header .brand { display:flex; align-items:center; gap:12px; font-weight:800; font-size:1.15rem; }
    header.pub-header .brand img { height:40px; border-radius:6px; }
    header.pub-header nav a {
        color:white; text-decoration:none; font-weight:600; font-size:0.92rem;
        margin-left:20px; opacity:0.9;
    }
    header.pub-header nav a:hover { opacity:1; text-decoration:underline; }
    .pub-hero {
        max-width: 960px; margin: 0 auto; padding: 56px 24px 32px; text-align:center;
    }
    .pub-hero h1 { font-size:2.1rem; font-weight:800; color:#002B5B; margin-bottom:14px; }
    .pub-hero p.lead { font-size:1.05rem; color:#4b5563; max-width:680px; margin:0 auto 24px; }
    .pub-hero .cta {
        display:inline-block; background:linear-gradient(135deg,#002B5B,#0057A8); color:white;
        padding:14px 32px; border-radius:10px; font-weight:700; text-decoration:none;
        box-shadow:0 6px 18px rgba(0,43,91,0.25);
    }
    .pub-section { max-width: 860px; margin: 0 auto; padding: 32px 24px; }
    .pub-section h2 { font-size:1.4rem; font-weight:800; color:#002B5B; margin-bottom:14px; }
    .pub-section p { color:#374151; margin-bottom:14px; font-size:0.98rem; }
    .pub-grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(230px,1fr)); gap:20px; margin-top:20px; }
    .pub-card {
        background:white; border-radius:14px; padding:22px; box-shadow:0 4px 16px rgba(0,43,91,0.07);
        border-top:4px solid #0057A8;
    }
    .pub-card h3 { font-size:1.02rem; color:#002B5B; margin-bottom:8px; }
    .pub-card p { font-size:0.9rem; color:#6b7280; margin:0; }
    .ad-slot { max-width:860px; margin:24px auto; padding:0 24px; }
    footer.pub-footer {
        background:#002B5B; color:#cfe0ff; text-align:center; padding:28px 16px; margin-top:40px; font-size:0.85rem;
    }
    footer.pub-footer a { color:#9dc0ff; text-decoration:none; margin:0 10px; }
    footer.pub-footer a:hover { text-decoration:underline; }
</style>
"""

ADSENSE_HEAD_SCRIPT = """
<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-5166749876470166"
        crossorigin="anonymous"></script>
"""

ADSENSE_UNIT = """
<ins class="adsbygoogle"
     style="display:block;"
     data-ad-client="ca-pub-5166749876470166"
     data-ad-slot="5183636349"
     data-ad-format="auto"
     data-full-width-responsive="true"></ins>
<script>(adsbygoogle = window.adsbygoogle || []).push({});</script>
"""


@router.get("/ads.txt", response_class=PlainTextResponse)
async def ads_txt():
    return "google.com, pub-5166749876470166, DIRECT, f08c47fec0942fa0\n"


@router.get("/", response_class=HTMLResponse)
async def landing_publica():
    return f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Carrier Transicold – Sistema de Gestión de Flota Refrigerada</title>
        <meta name="description" content="Plataforma de gestión operativa para flotas de transporte refrigerado: control de mantenimiento, inventario, asignaciones técnicas y diagnóstico de alarmas Carrier Transicold.">
        {PUBLIC_STYLE}
        {ADSENSE_HEAD_SCRIPT}
    </head>
    <body>
        <header class="pub-header">
            <div class="brand">
                <img src="https://raw.githubusercontent.com/Jesusalan0102/app-escaneo-series/main/carrierlogo.jpg" alt="Carrier Transicold">
                Sistema Operativo Carrier Transicold
            </div>
            <nav>
                <a href="/">Inicio</a>
                <a href="/nosotros">Nosotros</a>
                <a href="/guia-mantenimiento">Guías</a>
                <a href="/privacidad">Privacidad</a>
                <a href="/app">Iniciar sesión</a>
            </nav>
        </header>

        <section class="pub-hero">
            <h1>Gestión inteligente de flotas de transporte refrigerado</h1>
            <p class="lead">
                Coordinamos el mantenimiento, la asignación de técnicos y el control de calidad de
                unidades reefer Carrier Transicold desde una sola plataforma: menos tiempo muerto,
                más trazabilidad y decisiones basadas en datos reales de campo.
            </p>
            <a class="cta" href="/app">Acceder al sistema</a>
        </section>

        <section class="pub-section">
            <h2>¿Qué hace esta plataforma?</h2>
            <p>
                Nuestro sistema centraliza el ciclo completo de mantenimiento de unidades de
                refrigeración transportable: desde el registro de series y componentes (VIN,
                compresor, motor, evaporadores) hasta la asignación de actividades a técnicos en
                campo, pasando por el control de tickets de servicio, evidencias fotográficas y
                reportes ejecutivos de avance por lote.
            </p>
            <p>
                Está pensado para equipos de operaciones que necesitan visibilidad en tiempo real
                sobre el estado de cada unidad — pendiente, en proceso o completada — sin depender
                de hojas de cálculo dispersas ni reportes manuales.
            </p>

            <div class="pub-grid">
                <div class="pub-card">
                    <h3>📋 Control de asignaciones</h3>
                    <p>Distribuye actividades de mantenimiento entre técnicos y da seguimiento a cada tarea hasta su cierre.</p>
                </div>
                <div class="pub-card">
                    <h3>🎫 Gestión de tickets</h3>
                    <p>Registra incidencias por unidad, asigna responsables y documenta el reporte final de cada caso.</p>
                </div>
                <div class="pub-card">
                    <h3>📦 Inventario y series</h3>
                    <p>Lleva control detallado de componentes clave: VIN, compresores, motores, evaporadores y generadores.</p>
                </div>
                <div class="pub-card">
                    <h3>📍 Asistencia con geolocalización</h3>
                    <p>Registro de entrada y salida de técnicos con verificación de ubicación y foto de confirmación.</p>
                </div>
                <div class="pub-card">
                    <h3>🔔 Diagnóstico de alarmas</h3>
                    <p>Consulta rápida de códigos de alarma Carrier Transicold con causas, reset y acciones correctivas.</p>
                </div>
                <div class="pub-card">
                    <h3>📊 Reportes ejecutivos</h3>
                    <p>Dashboards con avance por lote, distribución de carga técnica y exportación a Excel.</p>
                </div>
            </div>
        </section>

        <div class="ad-slot">
            {ADSENSE_UNIT}
        </div>

        <section class="pub-section">
            <h2>Sobre este proyecto</h2>
            <p>
                Este sistema nació de la necesidad real de digitalizar procesos de mantenimiento
                que antes se gestionaban de forma manual, con el objetivo de reducir errores,
                acelerar la entrega de unidades y dar trazabilidad completa a cada intervención
                técnica sobre equipos de refrigeración transportable.
            </p>
        </section>

        <section class="pub-section">
            <h2>Preguntas frecuentes</h2>
            <div class="pub-grid">
                <div class="pub-card">
                    <h3>¿Qué es una unidad reefer?</h3>
                    <p>
                        Es el equipo de refrigeración instalado en un remolque o contenedor de
                        transporte, encargado de mantener la temperatura de la carga dentro de
                        un rango controlado durante todo el trayecto. Su falla puede significar
                        la pérdida completa de un embarque, por eso el mantenimiento preventivo
                        es tan importante como la reparación misma.
                    </p>
                </div>
                <div class="pub-card">
                    <h3>¿Por qué centralizar el mantenimiento en una plataforma?</h3>
                    <p>
                        Cuando la información vive en hojas de cálculo separadas o en mensajes
                        sueltos, es fácil perder trazabilidad: nadie sabe con certeza qué unidad
                        fue atendida, por quién ni con qué resultado. Centralizar el registro
                        permite auditar cada intervención y detectar patrones de falla recurrentes
                        por lote o por modelo de unidad.
                    </p>
                </div>
                <div class="pub-card">
                    <h3>¿Cómo se organiza el trabajo de los técnicos?</h3>
                    <p>
                        Cada actividad se asigna a un técnico específico y queda ligada a la
                        unidad correspondiente. El técnico documenta su avance con evidencia
                        fotográfica y notas de campo, lo que permite a los supervisores validar
                        el cierre de cada caso sin necesidad de estar presentes físicamente.
                    </p>
                </div>
                <div class="pub-card">
                    <h3>¿Qué se gana con el diagnóstico temprano de alarmas?</h3>
                    <p>
                        Detectar una alarma en sus primeras etapas evita que una unidad quede
                        fuera de servicio en plena ruta. Interpretar correctamente el código y
                        actuar a tiempo reduce tanto el tiempo de inactividad como el riesgo de
                        daño a la carga transportada.
                    </p>
                </div>
            </div>
        </section>

        <footer class="pub-footer">
            <p>© 2026 Carrier Transicold — Sistema Operativo</p>
            <p><a href="/privacidad">Política de privacidad</a> · <a href="/nosotros">Nosotros</a> · <a href="/app">Iniciar sesión</a></p>
        </footer>
    </body>
    </html>
    """


@router.get("/nosotros", response_class=HTMLResponse)
async def pagina_nosotros():
    return f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Nosotros – Carrier Transicold</title>
        {PUBLIC_STYLE}
        {ADSENSE_HEAD_SCRIPT}
    </head>
    <body>
        <header class="pub-header">
            <div class="brand">
                <img src="https://raw.githubusercontent.com/Jesusalan0102/app-escaneo-series/main/carrierlogo.jpg" alt="Carrier Transicold">
                Sistema Operativo Carrier Transicold
            </div>
            <nav>
                <a href="/">Inicio</a>
                <a href="/nosotros">Nosotros</a>
                <a href="/guia-mantenimiento">Guías</a>
                <a href="/privacidad">Privacidad</a>
                <a href="/app">Iniciar sesión</a>
            </nav>
        </header>

        <section class="pub-section" style="padding-top:48px;">
            <h2>Quiénes somos</h2>
            <p>
                Somos un equipo de operaciones dedicado al mantenimiento de unidades de
                refrigeración transportable Carrier Transicold. Esta plataforma es una
                herramienta interna que hemos abierto parcialmente al público para explicar
                nuestro proceso de trabajo y las buenas prácticas que aplicamos en el
                mantenimiento de equipos reefer.
            </p>
            <p>
                Trabajamos con lotes de unidades organizadas por número económico, dando
                seguimiento a cada actividad —desde el cableado inicial hasta la revisión
                final de fugas y vacío— con técnicos certificados en campo.
            </p>

            <h2 style="margin-top:32px;">Buenas prácticas de mantenimiento reefer</h2>
            <p>
                El mantenimiento preventivo de unidades de refrigeración transportable reduce
                significativamente las fallas en ruta. Algunas prácticas que seguimos:
            </p>
            <div class="pub-grid">
                <div class="pub-card">
                    <h3>🔍 Inspección de fugas</h3>
                    <p>Revisión periódica del sistema de refrigerante para detectar fugas antes de que afecten el rendimiento térmico.</p>
                </div>
                <div class="pub-card">
                    <h3>🌡 Verificación de vacío</h3>
                    <p>Comprobación del vacío del sistema tras cualquier intervención, evitando humedad residual en el circuito.</p>
                </div>
                <div class="pub-card">
                    <h3>🔌 Cableado y conexiones</h3>
                    <p>Revisión de arneses y conexiones eléctricas, puntos frecuentes de falla por vibración en ruta.</p>
                </div>
                <div class="pub-card">
                    <h3>📟 Diagnóstico de alarmas</h3>
                    <p>Interpretación temprana de códigos de alarma para actuar antes de que la unidad quede fuera de servicio.</p>
                </div>
            </div>
        </section>

        <section class="pub-section">
            <h2>Preguntas frecuentes sobre nuestro equipo</h2>
            <div class="pub-grid">
                <div class="pub-card">
                    <h3>¿Con qué frecuencia se revisan las unidades?</h3>
                    <p>
                        La frecuencia depende del uso de cada unidad, pero como práctica general
                        recomendamos una inspección visual en cada rotación de ruta y una revisión
                        técnica completa —incluyendo fugas, vacío y conexiones— de forma periódica
                        programada, sin esperar a que aparezca una falla evidente.
                    </p>
                </div>
                <div class="pub-card">
                    <h3>¿Qué certificaciones tienen los técnicos?</h3>
                    <p>
                        Nuestros técnicos de campo cuentan con formación específica en sistemas de
                        refrigeración transportable, incluyendo manejo seguro de refrigerantes y
                        procedimientos de vacío, además de capacitación continua conforme se
                        actualizan los equipos que damos mantenimiento.
                    </p>
                </div>
                <div class="pub-card">
                    <h3>¿Cómo se documenta cada intervención?</h3>
                    <p>
                        Cada visita técnica queda registrada con evidencia fotográfica, notas del
                        procedimiento realizado y el estado final de la unidad. Esto crea un
                        historial consultable que ayuda a anticipar fallas repetidas en una misma
                        unidad o en unidades del mismo lote.
                    </p>
                </div>
                <div class="pub-card">
                    <h3>¿Por qué compartimos estas prácticas públicamente?</h3>
                    <p>
                        Creemos que el mantenimiento preventivo bien hecho beneficia a toda la
                        industria del transporte refrigerado, no solo a nuestros clientes directos.
                        Por eso documentamos aquí nuestro enfoque de trabajo, aunque la plataforma
                        de gestión en sí sea una herramienta interna.
                    </p>
                </div>
            </div>
        </section>

        <div class="ad-slot">
            {ADSENSE_UNIT}
        </div>

        <footer class="pub-footer">
            <p>© 2026 Carrier Transicold — Sistema Operativo</p>
            <p><a href="/privacidad">Política de privacidad</a> · <a href="/">Inicio</a> · <a href="/app">Iniciar sesión</a></p>
        </footer>
    </body>
    </html>
    """


@router.get("/privacidad", response_class=HTMLResponse)
async def politica_privacidad():
    return f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Política de Privacidad – Carrier Transicold</title>
        {PUBLIC_STYLE}
    </head>
    <body>
        <header class="pub-header">
            <div class="brand">
                <img src="https://raw.githubusercontent.com/Jesusalan0102/app-escaneo-series/main/carrierlogo.jpg" alt="Carrier Transicold">
                Sistema Operativo Carrier Transicold
            </div>
            <nav>
                <a href="/">Inicio</a>
                <a href="/nosotros">Nosotros</a>
                <a href="/guia-mantenimiento">Guías</a>
                <a href="/privacidad">Privacidad</a>
                <a href="/app">Iniciar sesión</a>
            </nav>
        </header>

        <section class="pub-section" style="padding-top:48px;">
            <h2>Política de Privacidad</h2>
            <p><em>Última actualización: julio de 2026</em></p>

            <p>
                Esta política describe cómo se recopila y utiliza la información en el sitio web
                y sistema operativo de Carrier Transicold ("nosotros", "el sistema").
            </p>

            <h2 style="margin-top:28px;font-size:1.15rem;">Información que recopilamos</h2>
            <p>
                El acceso a las páginas públicas de este sitio (inicio, nosotros) no requiere
                registro ni recopila datos personales más allá de los generados automáticamente
                por tu navegador (como dirección IP y tipo de dispositivo) con fines estadísticos
                y de seguridad.
            </p>
            <p>
                El sistema operativo interno (accesible mediante inicio de sesión) recopila datos
                estrictamente necesarios para su funcionamiento: nombre de usuario, registros de
                actividad, asignaciones de mantenimiento y, en el módulo de asistencia, ubicación
                geográfica aproximada y fotografía de verificación al momento de registrar entrada
                o salida. Estos datos se usan únicamente para fines operativos internos y no se
                comparten con terceros.
            </p>

            <h2 style="margin-top:28px;font-size:1.15rem;">Cookies y publicidad</h2>
            <p>
                Este sitio puede mostrar anuncios provistos por Google AdSense. Google, como
                proveedor externo, utiliza cookies para publicar anuncios basados en visitas
                previas de un usuario a este u otros sitios web. El uso de la cookie de
                publicidad de Google permite a Google y sus socios publicar anuncios basados en
                la visita de los usuarios a este sitio y/o a otros sitios de Internet.
            </p>
            <p>
                Los usuarios pueden inhabilitar la publicidad personalizada visitando la
                <a href="https://adssettings.google.com/" target="_blank" rel="noopener">
                    Configuración de anuncios de Google</a>.
            </p>

            <h2 style="margin-top:28px;font-size:1.15rem;">Contacto</h2>
            <p>
                Si tienes dudas sobre esta política de privacidad, puedes contactarnos a través
                de los canales indicados en la sección "Nosotros" de este sitio.
            </p>
        </section>

        <footer class="pub-footer">
            <p>© 2026 Carrier Transicold — Sistema Operativo</p>
            <p><a href="/">Inicio</a> · <a href="/nosotros">Nosotros</a> · <a href="/app">Iniciar sesión</a></p>
        </footer>
    </body>
    </html>
    """


@router.get("/guia-mantenimiento", response_class=HTMLResponse)
async def guia_mantenimiento():
    return f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Guía de mantenimiento preventivo para unidades reefer | Carrier Transicold</title>
        <meta name="description" content="Guía práctica de mantenimiento preventivo para unidades de refrigeración transportable: qué revisar antes de cada ruta, señales de alerta tempranas y buenas prácticas de campo.">
        {PUBLIC_STYLE}
        {ADSENSE_HEAD_SCRIPT}
    </head>
    <body>
        <header class="pub-header">
            <div class="brand">
                <img src="https://raw.githubusercontent.com/Jesusalan0102/app-escaneo-series/main/carrierlogo.jpg" alt="Carrier Transicold">
                Sistema Operativo Carrier Transicold
            </div>
            <nav>
                <a href="/">Inicio</a>
                <a href="/nosotros">Nosotros</a>
                <a href="/guia-mantenimiento">Guías</a>
                <a href="/privacidad">Privacidad</a>
                <a href="/app">Iniciar sesión</a>
            </nav>
        </header>

        <section class="pub-hero">
            <h1>Guía de mantenimiento preventivo para unidades reefer</h1>
            <p class="lead">
                Qué revisar antes de cada ruta para reducir fallas en carretera y proteger la carga.
            </p>
        </section>

        <section class="pub-section">
            <h2>Por qué el mantenimiento preventivo importa más que la reparación</h2>
            <p>
                Cuando una unidad reefer falla en plena ruta, el costo casi nunca es solo el de la
                reparación. Es el tiempo que el vehículo pasa detenido, el reacomodo de la ruta, y en
                el peor de los casos, la pérdida parcial o total de la carga por pérdida de cadena de
                frío. La mayoría de esas fallas no aparecen de la nada: dan señales días o semanas
                antes, y se pueden anticipar con una rutina de revisión simple pero consistente.
            </p>
            <p>
                A continuación compartimos los puntos que, en nuestra experiencia operando flotas de
                transporte refrigerado, más impacto tienen para evitar paros no programados.
            </p>
        </section>

        <section class="pub-section">
            <h2>Antes de cada salida</h2>
            <div class="pub-grid">
                <div class="pub-card">
                    <h3>1. Revisión visual del compartimento del motor diésel</h3>
                    <p>
                        Busca fugas de aceite o refrigerante en el suelo bajo la unidad, correas con
                        signos de desgaste o grietas, y conexiones eléctricas sueltas. Una fuga pequeña
                        detectada a tiempo es una reparación menor; ignorada, puede dejar la unidad sin
                        motor auxiliar a mitad de ruta.
                    </p>
                </div>
                <div class="pub-card">
                    <h3>2. Niveles de combustible y refrigerante</h3>
                    <p>
                        Confirma que el tanque de diésel del motor auxiliar tenga suficiente autonomía
                        para la duración estimada del viaje, considerando que el consumo aumenta con
                        temperaturas exteriores altas o cuando la unidad trabaja en modo de enfriamiento
                        continuo (pull-down) al inicio de la carga.
                    </p>
                </div>
                <div class="pub-card">
                    <h3>3. Estado de puertas y empaques</h3>
                    <p>
                        Un empaque de puerta deteriorado permite fuga de aire frío constante, obligando
                        al equipo a trabajar más de lo necesario para mantener la temperatura, lo que
                        acelera el desgaste del compresor y dispara el consumo de combustible.
                    </p>
                </div>
                <div class="pub-card">
                    <h3>4. Panel de control y códigos de alarma activos</h3>
                    <p>
                        Antes de salir, revisa si el panel muestra alguna alarma activa o reciente. Una
                        alarma que se "borra sola" sin haberse atendido no significa que el problema
                        desapareció — muchas veces vuelve a aparecer bajo carga, ya en ruta.
                    </p>
                </div>
            </div>
        </section>

        <div class="ad-slot">
            {ADSENSE_UNIT}
        </div>

        <section class="pub-section">
            <h2>Señales de alerta que no deberían ignorarse</h2>
            <p>
                Hay ciertos comportamientos que, aunque no generan una alarma formal en el panel,
                anticipan una falla mayor: ciclos de encendido y apagado del compresor más frecuentes
                de lo normal, ruido metálico nuevo durante el arranque, tiempo de recuperación de
                temperatura más lento tras abrir la puerta de carga, o vibración inusual en el chasis
                del motor auxiliar. Documentar estos síntomas —aunque parezcan menores— ayuda a que el
                taller diagnostique la causa real más rápido, en vez de reaccionar solo cuando ya hay
                una falla total.
            </p>
        </section>

        <section class="pub-section">
            <h2>Por qué documentar cada revisión, no solo las reparaciones</h2>
            <p>
                Es común que las flotas solo registren cuando algo se rompe. El problema es que sin un
                historial de las revisiones "normales", es imposible distinguir una falla aislada de
                un patrón que se repite en una unidad específica o en un lote completo del mismo
                modelo. Llevar un registro sistemático de todas las inspecciones —no solo de las
                reparaciones— es lo que permite anticipar fallas antes de que detengan una ruta.
            </p>
        </section>

        <footer class="pub-footer">
            <p>© 2026 Carrier Transicold — Sistema Operativo</p>
            <p><a href="/">Inicio</a> · <a href="/nosotros">Nosotros</a> · <a href="/app">Iniciar sesión</a></p>
        </footer>
    </body>
    </html>
    """


# ------------------------------------------------------------
# API: ASIGNACIÓN POR CLUSTER
# (movido desde cluster_router.py para consolidar en web_router.py)
# ------------------------------------------------------------
ACTIVIDADES_CARRIER = [
    "Cableado", "Programación", "Soldadura", "Check de fugas",
    "Vacío", "Cerrado", "Pre-viaje", "Horas Corridas",
    "Standby", "GPS", "Corriendo", "Inspección",
    "Accesorios", "Toma de Valores", "Evidencia", "Toma de Series",
    "Extra Eléctrico", "Extra Soldador",
]

class ClusterAsignacion(BaseModel):
    tecnicos: List[str]
    actividades: List[str]
    unidades: List[str]

@router.get("/api/cluster/tecnicos", tags=["cluster"])
def listar_tecnicos_cluster(current_user=Depends(verify_token)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Solo administradores")
    return execute_read("SELECT username FROM users WHERE role='tecnico' ORDER BY username")

@router.get("/api/cluster/unidades", tags=["cluster"])
def listar_unidades_cluster(current_user=Depends(verify_token)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Solo administradores")
    # Excluye unidades de lotes ocultos, igual que el dashboard
    return execute_read("SELECT unit_number, id_lote FROM unidades WHERE oculto=0 ORDER BY id_lote, unit_number")

@router.get("/api/cluster/actividades", tags=["cluster"])
def listar_actividades_cluster(current_user=Depends(verify_token)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Solo administradores")
    return [{"nombre": a} for a in ACTIVIDADES_CARRIER]

@router.post("/api/cluster/asignar", tags=["cluster"])
def asignar_cluster(data: ClusterAsignacion, current_user=Depends(verify_token)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Solo administradores")
    if not data.tecnicos or not data.actividades or not data.unidades:
        raise HTTPException(status_code=400, detail="Debes seleccionar técnicos, actividades y unidades")

    creadas = 0
    omitidas = 0

    for unidad in data.unidades:
        for actividad in data.actividades:
            for tecnico in data.tecnicos:
                existe = execute_read(
                    "SELECT id FROM asignaciones WHERE unidad=%s AND actividad_id=%s AND tecnico=%s",
                    (unidad, actividad, tecnico)
                )
                if existe:
                    omitidas += 1
                    continue
                execute_write(
                    "INSERT INTO asignaciones (unidad, actividad_id, tecnico, estado) VALUES (%s,%s,%s,'pendiente')",
                    (unidad, actividad, tecnico)
                )
                creadas += 1

    return {
        "mensaje": f"{creadas} asignaciones creadas, {omitidas} omitidas (ya existían)",
        "creadas": creadas,
        "omitidas": omitidas
    }
