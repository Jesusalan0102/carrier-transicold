"""
Contenido HTML de /app/reporte-mensual (Reporte final mensual · Indicadores por técnico).
Se inserta dentro de pagina_con_menu(), por eso comparte sidebar, sesión y tema claro/oscuro.
Los datos salen de GET /api/reporte-mensual/datos?mes=AAAA-MM.
"""

CONTENIDO_REPORTE_MENSUAL = r"""
<script>
    if (window.role !== 'admin' && window.role !== 'lider' && window.role !== 'visor') {
        window.location.href = '/app/mis-tareas';
    }
</script>
<style>
    @page { size: A4 landscape; margin: 7mm; }

    .rm-toolbar { display:flex; align-items:center; gap:10px; flex-wrap:wrap; margin-bottom:16px; }
    .rm-toolbar label { font-size:.82rem; font-weight:600; color:var(--text-secondary); }
    .rm-toolbar input[type=month] { width:auto; margin:0; padding:9px 12px; font-size:.9rem; border-radius:8px; }
    .rm-btn { display:inline-flex; align-items:center; gap:8px; border:1px solid var(--carrier-blue); background:var(--carrier-blue);
              color:#fff; border-radius:8px; padding:9px 16px; font-size:.86rem; font-weight:600; cursor:pointer; }
    .rm-btn.sec { background:transparent; color:var(--carrier-blue); }
    body.theme-dark .rm-btn.sec { color:#cfe0ff; border-color:#3b5a8c; }
    .rm-btn:hover { filter:brightness(1.12); }
    .rm-btn:focus-visible, .rm-toolbar input:focus-visible { outline:3px solid #7fb2ff; outline-offset:2px; }

    .rm-kpis { display:grid; grid-template-columns:repeat(var(--rm-cols-d, 9), minmax(0,1fr)); gap:10px; margin-bottom:16px; }
    .rm-kpi { background:var(--bg-surface-2); border:1px solid var(--rm-line); border-radius:10px; padding:14px 12px;
              display:flex; align-items:center; gap:10px; min-width:0; box-shadow:0 1px 3px var(--shadow-soft); }
    .rm-kpi-ico { flex:0 0 42px; height:42px; border-radius:50%; background:var(--carrier-blue); color:#fff;
                  display:flex; align-items:center; justify-content:center; font-size:21px; }
    .rm-kpi-txt { min-width:0; }
    .rm-kpis.compact .rm-kpi { padding:12px 8px; gap:7px; }
    .rm-kpis.compact .rm-kpi-ico { flex-basis:34px; height:34px; font-size:18px; }
    .rm-kpis.compact .rm-kpi-lbl { font-size:.67rem; }
    .rm-kpis.compact .rm-kpi-num { font-size:1.7rem; }
    .rm-kpi-lbl { overflow-wrap:anywhere; font-size:.74rem; font-weight:600; color:var(--text-primary); line-height:1.15; min-height:2.3em;
                  display:flex; align-items:flex-end; }
    .rm-kpi-num { font-size:1.9rem; font-weight:700; line-height:1.05; color:var(--carrier-blue); letter-spacing:-.02em; }
    body.theme-dark .rm-kpi-num { color:#cfe0ff; }

    .rm-grid { display:grid; gap:16px; margin-bottom:16px; }
    .rm-grid.g1 { grid-template-columns:minmax(0,1.62fr) minmax(0,1fr); }
    .rm-grid.wide { grid-template-columns:1fr; }
    .rm-grid.wide .rm-sum { grid-template-columns:repeat(4, 1fr); }
    .rm-grid.wide .rm-sum-i, .rm-grid.wide .rm-sum-i:nth-child(odd), .rm-grid.wide .rm-sum-i:nth-child(-n+2) { border:none; border-right:1px solid var(--border-color-soft); }
    .rm-grid.wide .rm-sum-i:last-child { border-right:none; }
    .rm-grid.wide .rm-note { margin:4px 14px 6px; }
    .rm-panel { background:var(--bg-surface); border:1px solid var(--rm-line); border-radius:10px; overflow:hidden;
                box-shadow:0 1px 3px var(--shadow-soft); min-width:0; display:flex; flex-direction:column; }
    .rm-panel-h { background:var(--carrier-blue); color:#fff; font-weight:700; font-size:1.02rem; padding:9px 14px; }
    body.theme-dark .rm-panel-h { background:#12305f; }
    .rm-panel-b { padding:10px 12px 12px; flex:1; min-height:0; }

    .rm-cell { min-width:0; }
    .rm-print-img { display:none; }
    .rm-legend { display:flex; flex-wrap:wrap; gap:4px 9px; justify-content:center; font-size:.68rem; color:var(--text-primary); margin:4px 0 2px; }
    .rm-legend span { display:inline-flex; align-items:center; gap:6px; }
    .rm-sw { width:10px; height:10px; border-radius:2px; display:inline-block; flex:0 0 11px; }

    .rm-donut { display:grid; grid-template-columns:minmax(0,1.15fr) minmax(0,1fr); gap:6px; align-items:center; }
    .rm-dlegend { list-style:none; margin:0; padding:0; font-size:.78rem; }
    .rm-dlegend li { display:flex; align-items:center; gap:9px; padding:7px 4px; border-bottom:1px solid var(--border-color-soft); }
    .rm-dlegend li:last-child { border-bottom:none; }
    .rm-dlegend .dot { width:14px; height:14px; border-radius:50%; flex:0 0 14px; }
    .rm-dlegend .nm { flex:1; color:var(--text-primary); }
    .rm-dlegend .pc { font-weight:700; color:var(--text-primary); font-variant-numeric:tabular-nums; }

    .rm-tblwrap { overflow-x:auto; }
    table.rm-tbl { width:100%; border-collapse:collapse; background:transparent; border-radius:0; border:none; box-shadow:none; font-size:.7rem; }
    .rm-tbl thead th { background:var(--carrier-blue); color:#fff; padding:7px 3px; text-align:center; font-weight:700;
                       font-size:.66rem; border:none; border-right:1px solid rgba(255,255,255,.18); line-height:1.15; }
    body.theme-dark .rm-tbl thead th { background:#12305f; }
    .rm-tbl thead th:first-child { text-align:left; padding-left:10px; }
    .rm-tbl tbody td { padding:5px 3px; text-align:center; border-bottom:1px solid var(--border-color-soft);
                       font-variant-numeric:tabular-nums; color:var(--text-primary); }
    .rm-tbl tbody td:first-child { text-align:left; padding-left:10px; font-weight:600; white-space:nowrap; font-size:.68rem; }
    .rm-tbl tbody tr:nth-child(even) td { background:var(--rm-zebra); }
    .rm-tbl.dense { font-size:.6rem; }
    .rm-tbl.dense thead th { font-size:.56rem; padding:6px 2px; }
    .rm-tbl.dense tbody td, .rm-tbl.dense tfoot td { padding:4px 2px; }
    .rm-tbl.dense tbody td:first-child { font-size:.62rem; }
    .rm-tbl td.z { color:var(--text-secondary); opacity:.7; }
    .rm-tbl td.tot, .rm-tbl th.tot { font-weight:700; border-left:2px solid var(--rm-line); }
    .rm-tbl tfoot td { padding:7px 3px; text-align:center; font-weight:700; border-top:2px solid var(--carrier-blue);
                       background:var(--rm-zebra); font-variant-numeric:tabular-nums; color:var(--text-primary); }
    .rm-tbl tfoot td:first-child { text-align:left; padding-left:10px; }

    .rm-sum { display:grid; grid-template-columns:1fr 1fr; }
    .rm-sum-i { display:flex; align-items:center; gap:14px; padding:18px 14px; min-width:0; }
    .rm-sum-i:nth-child(odd) { border-right:1px solid var(--border-color-soft); }
    .rm-sum-i:nth-child(-n+2) { border-bottom:1px solid var(--border-color-soft); }
    .rm-sum-ico { flex:0 0 50px; height:50px; border-radius:50%; background:var(--carrier-light); color:var(--carrier-blue);
                  display:flex; align-items:center; justify-content:center; font-size:26px; }
    body.theme-dark .rm-sum-ico { color:#cfe0ff; }
    .rm-sum-l { font-size:.78rem; color:var(--text-primary); line-height:1.2; }
    .rm-sum-v { font-size:1.9rem; font-weight:700; color:var(--carrier-blue); line-height:1.1; }
    body.theme-dark .rm-sum-v { color:#cfe0ff; }
    .rm-sum-s { font-size:1rem; font-weight:600; color:var(--text-primary); margin-top:3px; }
    .rm-sum-name { font-size:.98rem; font-weight:700; color:var(--carrier-blue); margin:3px 0 2px; line-height:1.15; }
    body.theme-dark .rm-sum-name { color:#cfe0ff; }
    .rm-note { display:flex; gap:12px; background:var(--carrier-light); border:1px solid var(--rm-line); border-radius:8px;
               padding:14px 16px; margin:12px 4px 2px; font-size:.78rem; color:var(--text-primary); line-height:1.5; }
    .rm-note i { font-size:30px; color:var(--carrier-accent); flex:0 0 auto; }
    .rm-note b { display:block; margin-bottom:2px; }
    .rm-foot { font-size:.72rem; color:var(--text-secondary); margin:4px 2px 0; display:flex; justify-content:space-between; gap:12px; flex-wrap:wrap; }

    .rm-empty { text-align:center; padding:60px 20px; color:var(--text-secondary); }
    .rm-empty i { font-size:46px; display:block; margin-bottom:10px; opacity:.6; }

    @media (max-width: 1280px) { .rm-kpis { grid-template-columns:repeat(5, minmax(0,1fr)); } }
    @media (max-width: 1100px) { .rm-grid.g1 { grid-template-columns:1fr; } }
    @media (max-width: 900px)  { .rm-grid.wide .rm-sum { grid-template-columns:1fr 1fr; } .rm-grid.wide .rm-sum-i { border-bottom:1px solid var(--border-color-soft); } }
    @media (max-width: 640px)  { .rm-kpis { grid-template-columns:repeat(2, minmax(0,1fr)); } .rm-donut { grid-template-columns:1fr; } .rm-sum { grid-template-columns:1fr; }
        .rm-sum-i:nth-child(odd) { border-right:none; } .rm-sum-i:nth-child(-n+3) { border-bottom:1px solid var(--border-color-soft); } }

    @media print {
        html, body { background:#fff !important; -webkit-print-color-adjust:exact; print-color-adjust:exact; }
        .sidebar, .hamburger, .overlay, .rm-toolbar, .global-search-trigger, #globalSearchOverlay, #visorBanner, #liveClock { display:none !important; }
        .main-content { margin:0 !important; padding:0 !important; }
        .app-body { padding:8px 0 0 !important; }
        .rm-kpis { grid-template-columns:repeat(var(--rm-cols-d, 9), minmax(0,1fr)); gap:6px; }
        .rm-kpi { padding:8px 6px; gap:6px; }
        .rm-kpi-ico { flex-basis:30px; height:30px; font-size:16px; }
        .rm-kpi-num { font-size:1.35rem; }
        .rm-grid.g1 { grid-template-columns:minmax(0,1.62fr) minmax(0,1fr); gap:10px; }
        .rm-grid.g1.wide { grid-template-columns:1fr; }
        .rm-panel, .rm-kpi, .rm-grid { break-inside:avoid; page-break-inside:avoid; }
        .rm-sum-i { padding:10px 10px; }
        .app-header, .app-body { zoom:.85; }   /* A4 horizontal: hoja 1 = indicadores y gráficas, hoja 2 = detalle y resumen */
        .app-header { break-after:avoid; }
        #rmBar, #rmPie { display:none !important; }
        .rm-print-img { display:block; width:100%; height:auto; }
    }
</style>

<div class="rm-toolbar">
    <label for="rmMes">Mes del reporte</label>
    <input type="month" id="rmMes" aria-label="Mes del reporte">
    <button class="rm-btn sec" id="rmPrev" type="button" title="Mes anterior"><i class="ti ti-chevron-left"></i> Anterior</button>
    <button class="rm-btn sec" id="rmNext" type="button" title="Mes siguiente">Siguiente <i class="ti ti-chevron-right"></i></button>
    <span style="flex:1"></span>
    <button class="rm-btn" id="rmPrint" type="button"><i class="ti ti-printer"></i> Imprimir / Guardar PDF</button>
</div>

<div id="rmRoot"><div class="rm-empty"><i class="ti ti-loader-2"></i>Cargando reporte…</div></div>

<script>
(function () {
    // Las categorías vienen del catálogo real de actividades (cambian si el admin agrega o quita alguna).
    // Las actividades del tablero de referencia conservan su color; el resto toma uno de la paleta
    // según su posición en el catálogo, así cada actividad mantiene siempre el mismo color entre meses.
    const COLOR_FIJO = {
        cableado:'#3B82F6', cerrado:'#0EA5E9', accesorios:'#7CC4CF', soldadura:'#F4A259', vacio:'#8B6FD6',
        horas_corridas:'#F5C542', toma_de_series:'#4F5FD9', evidencia:'#0F9FA8', video_liberacion:'#0B2A63'
    };
    const PALETA = ['#E85D75','#2DBE8A','#94A3B8','#B45309','#EC4899','#84CC16','#166534','#9F1239','#78716C','#CA8A04','#6B7F2A','#C2410C'];
    const ICONOS = {
        cableado:'plug', programacion:'code', soldadura:'flame', check_de_fugas:'droplet', vacio:'wind', cerrado:'clipboard-check',
        pre_viaje:'truck', horas_corridas:'run', standby:'player-pause', gps:'map-pin', corriendo:'run', inspeccion:'search',
        accesorios:'settings', toma_de_valores:'gauge', evidencia:'camera', toma_de_series:'barcode', extra_electrico:'bolt',
        extra_soldador:'flame', retrabajo_electrico:'refresh', retrabajo_soldador:'refresh', tickets:'ticket', video_liberacion:'video'
    };
    const colorDe = c => COLOR_FIJO[c.clave] || PALETA[(c.orden || 0) % PALETA.length];
    const iconoDe = c => ICONOS[c.clave] || 'checklist';
    const MESES = ['enero','febrero','marzo','abril','mayo','junio','julio','agosto','septiembre','octubre','noviembre','diciembre'];

    const $ = id => document.getElementById(id);
    const esc = s => String(s == null ? '' : s).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
    const fmt = n => Number(n || 0).toLocaleString('es-MX');
    const pct = n => Number(n || 0).toLocaleString('es-MX', {minimumFractionDigits:1, maximumFractionDigits:1}) + '%';

    // Tema de la app → variables propias del reporte (se recalculan al cambiar claro/oscuro)
    function aplicarVars() {
        const dark = document.body.classList.contains('theme-dark');
        const r = $('rmRoot').parentElement.style;
        r.setProperty('--rm-line',  dark ? '#283854' : '#D5E4F8');
        r.setProperty('--rm-zebra', dark ? '#182338' : '#F4F7FD');
        COLOR_FIJO.video_liberacion = dark ? '#5B8DD9' : '#0B2A63';   // el azul marino no se distingue sobre fondo oscuro
    }
    function colorTexto() { return getComputedStyle(document.body).getPropertyValue('--text-primary').trim() || '#1f2937'; }

    function mesActual() {
        const p = new Intl.DateTimeFormat('en-CA', {timeZone:'America/Tijuana', year:'numeric', month:'2-digit'}).formatToParts(new Date());
        return p.find(x => x.type === 'year').value + '-' + p.find(x => x.type === 'month').value;
    }
    function moverMes(mes, d) {
        let [y, m] = mes.split('-').map(Number); m += d;
        while (m < 1) { m += 12; y--; } while (m > 12) { m -= 12; y++; }
        return y + '-' + String(m).padStart(2, '0');
    }

    let ultimo = null;

    async function cargar(mes) {
        $('rmRoot').innerHTML = '<div class="rm-empty"><i class="ti ti-loader-2"></i>Cargando reporte…</div>';
        try {
            const res = await window.fetchAuth('/api/reporte-mensual/datos?mes=' + encodeURIComponent(mes));
            if (!res.ok) {
                const e = await res.json().catch(() => ({}));
                throw new Error(e.detail || ('Error ' + res.status));
            }
            ultimo = await res.json();
            pintar(ultimo);
        } catch (e) {
            $('rmRoot').innerHTML = '<div class="rm-empty"><i class="ti ti-alert-triangle"></i>No se pudo cargar el reporte. ' + esc(e.message) + '</div>';
        }
    }

    function pintar(d) {
        // Encabezado de la página (subtítulo + total) — los pone el layout compartido
        const sub = $('appHeaderSub'), tot = $('appHeaderTotal');
        if (sub) sub.textContent = 'Reporte final mensual · ' + d.mes_nombre + ' ' + d.anio;
        if (tot) tot.textContent = fmt(d.total);
        document.title = 'Reporte final ' + d.mes_nombre + ' ' + d.anio + ' – Carrier Transicold';

        if (!d.total) {
            $('rmRoot').innerHTML = '<div class="rm-empty"><i class="ti ti-calendar-off"></i>' +
                'No hay actividades completadas ni videos de evidencia en ' + esc(d.mes_nombre) + ' ' + d.anio + '.</div>';
            return;
        }

        const cats = d.categorias;
        const kpis = cats.map(c =>
            '<div class="rm-kpi"><div class="rm-kpi-ico" aria-hidden="true"><i class="ti ti-' + iconoDe(c) + '"></i></div>' +
            '<div class="rm-kpi-txt"><div class="rm-kpi-lbl">' + esc(c.etiqueta) + '</div><div class="rm-kpi-num">' + fmt(c.total) + '</div></div></div>'
        ).join('');

        const leyendaBarras = cats.map(c => '<span><i class="rm-sw" style="background:' + colorDe(c) + '"></i>' + esc(c.etiqueta) + '</span>').join('');

        const leyendaDona = cats.map(c =>
            '<li><span class="dot" style="background:' + colorDe(c) + '"></span><span class="nm">' + esc(c.etiqueta) +
            '</span><span class="pc">' + pct(c.porcentaje) + '</span></li>').join('');

        const head = '<th>Técnico</th>' + cats.map(c => '<th>' + esc(c.etiqueta) + '</th>').join('') + '<th class="tot">Total</th>';
        const filas = d.tecnicos.map(t =>
            '<tr><td>' + esc(t.nombre) + '</td>' +
            cats.map(c => '<td class="' + (t[c.clave] ? '' : 'z') + '">' + fmt(t[c.clave]) + '</td>').join('') +
            '<td class="tot ' + (t.total ? '' : 'z') + '">' + fmt(t.total) + '</td></tr>').join('');
        const pie = '<tr><td>Total</td>' + cats.map(c => '<td>' + fmt(c.total) + '</td>').join('') + '<td class="tot">' + fmt(d.total) + '</td></tr>';

        const am = d.actividad_mayor, tm = d.tecnico_mayor, cn = d.concentracion;
        let nota = 'La actividad “' + esc(am.etiqueta) + '” es la de mayor volumen (' + pct(cats.find(c => c.etiqueta === am.etiqueta).porcentaje) +
            ' de los registros del mes). ' + (cn.n_tecnicos_mitad === 1 ? 'Un solo técnico concentra' : cn.n_tecnicos_mitad + ' técnicos concentran') +
            ' más de la mitad de los registros.';
        const sinReg = (d.sin_registros || []).join(', ');

        const hoy = new Date().toLocaleString('es-MX', {timeZone:'America/Tijuana', dateStyle:'long', timeStyle:'short'});

        $('rmRoot').innerHTML =
            '<div class="rm-kpis' + (cats.length > 9 ? ' compact' : '') + '" style="--rm-cols-d:' + Math.min(cats.length, 9) + '">' + kpis + '</div>' +
            '<div class="rm-grid g1">' +
                '<section class="rm-panel"><div class="rm-panel-h">Actividades por Técnico</div><div class="rm-panel-b">' +
                    '<div class="rm-legend">' + leyendaBarras + '</div><div class="rm-cell"><div id="rmBar" style="height:' + (window.innerWidth < 640 ? 420 : 370) + 'px"></div></div></div></section>' +
                '<section class="rm-panel"><div class="rm-panel-h">Distribución general de actividades</div><div class="rm-panel-b">' +
                    '<div class="rm-donut"><div class="rm-cell"><div id="rmPie" style="height:330px"></div></div><ul class="rm-dlegend">' + leyendaDona + '</ul></div></div></section>' +
            '</div>' +
            '<div class="rm-grid g1' + (cats.length > 9 ? ' wide' : '') + '">' +
                '<section class="rm-panel"><div class="rm-panel-h">Detalle por Técnico</div><div class="rm-panel-b" style="padding:0">' +
                    '<div class="rm-tblwrap"><table class="rm-tbl' + (cats.length > 12 ? ' dense' : '') + '"><thead><tr>' + head + '</tr></thead><tbody>' + filas + '</tbody><tfoot>' + pie + '</tfoot></table></div></div></section>' +
                '<section class="rm-panel"><div class="rm-panel-h">Resumen</div><div class="rm-panel-b" style="padding:0 10px 12px">' +
                    '<div class="rm-sum">' +
                        '<div class="rm-sum-i"><div class="rm-sum-ico"><i class="ti ti-users"></i></div><div><div class="rm-sum-l">Técnicos</div><div class="rm-sum-v">' + fmt(d.n_tecnicos) + '</div></div></div>' +
                        '<div class="rm-sum-i"><div class="rm-sum-ico"><i class="ti ti-file-text"></i></div><div><div class="rm-sum-l">Total de registros</div><div class="rm-sum-v">' + fmt(d.total) + '</div></div></div>' +
                        '<div class="rm-sum-i"><div class="rm-sum-ico"><i class="ti ti-list-details"></i></div><div><div class="rm-sum-l">Actividad con mayor registro</div><div class="rm-sum-name">' + esc(am.etiqueta) + '</div><div class="rm-sum-s">' + fmt(am.total) + '</div></div></div>' +
                        '<div class="rm-sum-i"><div class="rm-sum-ico"><i class="ti ti-user"></i></div><div><div class="rm-sum-l">Técnico con mayor actividad</div><div class="rm-sum-name">' + esc(tm.nombre) + '</div><div class="rm-sum-v" style="font-size:1.6rem">' + fmt(tm.total) + '</div></div></div>' +
                    '</div>' +
                    '<div class="rm-note"><i class="ti ti-bulb"></i><div><b>Nota:</b>' + esc(nota) + '</div></div>' +
                '</div></section>' +
            '</div>' +
            '<div class="rm-foot"><span>Registro = tarea completada por el técnico en el mes (catálogo de actividades y tickets) o video de evidencia subido.' +
                (sinReg ? ' Sin registros este mes: ' + esc(sinReg) + '.' : '') + '</span><span>Generado el ' + esc(hoy) + '</span></div>';

        dibujar(d);
    }

    function dibujar(d) {
        const txt = colorTexto();
        const cats = d.categorias;
        const nombres = d.tecnicos.map(t => t.nombre);
        const maxCar = window.innerWidth < 640 ? 18 : 32;
        const etiquetas = nombres.map(n => n.length > maxCar ? n.slice(0, maxCar - 1) + '…' : n);

        const trazas = cats.map(c => ({
            type:'bar', name:c.etiqueta, x:nombres, y:d.tecnicos.map(t => t[c.clave]),
            marker:{color:colorDe(c)}, hovertemplate:'%{x}<br>' + c.etiqueta + ': %{y}<extra></extra>'
        }));
        trazas.push({   // total sobre cada barra (también el 0, como en el tablero de referencia)
            type:'scatter', mode:'text', x:nombres, y:d.tecnicos.map(t => t.total),
            text:d.tecnicos.map(t => String(t.total)), textposition:'top center', showlegend:false, hoverinfo:'skip',
            textfont:{size:11, color:txt}, cliponaxis:false
        });
        const ymax = Math.max(...d.tecnicos.map(t => t.total), 1);
        const p1 = Plotly.newPlot('rmBar', trazas, {
            barmode:'stack', showlegend:false, paper_bgcolor:'rgba(0,0,0,0)', plot_bgcolor:'rgba(0,0,0,0)',
            margin:{l:36, r:8, t:18, b:120}, font:{family:'Inter, system-ui, sans-serif', size:10, color:txt},
            xaxis:{tickangle:-45, automargin:true, tickfont:{size:9}, tickmode:'array', tickvals:nombres, ticktext:etiquetas}, yaxis:{range:[0, ymax * 1.12], gridcolor:'rgba(120,140,170,.25)', zeroline:false}
        }, {displayModeBar:false, responsive:true});

        const con = cats.filter(c => c.total > 0);
        const p2 = Plotly.newPlot('rmPie', [{
            type:'pie', hole:.6, sort:false, direction:'clockwise', rotation:90,
            labels:con.map(c => c.etiqueta), values:con.map(c => c.total),
            marker:{colors:con.map(colorDe), line:{color:'#fff', width:1.5}},
            text:con.map(c => pct(c.porcentaje)), textinfo:'text', textposition:'inside', insidetextorientation:'horizontal',
            textfont:{size:11, color:'#fff'}, hovertemplate:'%{label}: %{value} registros<extra></extra>', showlegend:false
        }], {
            paper_bgcolor:'rgba(0,0,0,0)', margin:{l:6, r:6, t:6, b:6}, font:{family:'Inter, system-ui, sans-serif', color:txt},
            annotations:[
                {text:'<b>' + fmt(d.total) + '</b>', x:.5, y:.54, showarrow:false, font:{size:30, color:txt}},
                {text:'Total de registros', x:.5, y:.43, showarrow:false, font:{size:11, color:txt}}
            ]
        }, {displayModeBar:false, responsive:true});
        Promise.all([p1, p2]).then(prepararImpresion);
    }

    // ── Eventos ────────────────────────────────────────────────
    const inp = $('rmMes');
    inp.value = mesActual();
    inp.addEventListener('change', () => { if (inp.value) cargar(inp.value); });
    $('rmPrev').addEventListener('click', () => { inp.value = moverMes(inp.value || mesActual(), -1); cargar(inp.value); });
    $('rmNext').addEventListener('click', () => { inp.value = moverMes(inp.value || mesActual(), 1);  cargar(inp.value); });
    $('rmPrint').addEventListener('click', imprimir);

    // Impresión: los gráficos se convierten a imagen (así salen completos y nítidos en cualquier tamaño de hoja).
    async function prepararImpresion() {
        for (const id of ['rmBar', 'rmPie']) {
            const el = $(id);
            if (!el || !el.data || !el.clientWidth) continue;
            try {
                const url = await Plotly.toImage(el, {format:'png', width:el.clientWidth, height:el.clientHeight, scale:2});
                let img = $(id + 'Img');
                if (!img) {
                    img = document.createElement('img');
                    img.id = id + 'Img'; img.className = 'rm-print-img'; img.alt = '';
                    el.parentNode.appendChild(img);
                }
                img.src = url;
            } catch (e) { /* si falla, se imprime sin ese gráfico */ }
        }
    }
    let _volverAOscuro = false;
    async function imprimir() {
        if (document.body.classList.contains('theme-dark')) {   // el papel siempre va en tema claro
            _volverAOscuro = true;
            document.body.classList.remove('theme-dark');
            await new Promise(r => setTimeout(r, 500));          // el observador repinta con colores claros
        }
        await prepararImpresion();
        window.print();
    }
    window.addEventListener('afterprint', () => {
        if (_volverAOscuro) { _volverAOscuro = false; document.body.classList.add('theme-dark'); }
    });

    // Cambio de tema claro/oscuro: se repinta con los colores nuevos
    new MutationObserver(() => { aplicarVars(); if (ultimo) pintar(ultimo); })
        .observe(document.body, {attributes:true, attributeFilter:['class']});

    aplicarVars();
    cargar(inp.value);
})();
</script>
"""
