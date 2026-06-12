diff --git a/backend/auth.py b/backend/auth.py
index 19970f3..b8cfc43 100644
--- a/backend/auth.py
+++ b/backend/auth.py
@@ -8,7 +8,7 @@ import os
 
 SECRET_KEY = os.getenv("SECRET_KEY", "carrier_secret_key_2024_change_in_production")
 ALGORITHM  = os.getenv("ALGORITHM", "HS256")
-ACCESS_TOKEN_EXPIRE_MINUTES = 30
+ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 480))  # 8 horas
 
 oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
 
diff --git a/backend/routers/evidencias_router.py b/backend/routers/evidencias_router.py
index b1f893e..fa4630d 100644
--- a/backend/routers/evidencias_router.py
+++ b/backend/routers/evidencias_router.py
@@ -349,3 +349,21 @@ def ver_foto(foto_id: int, current_user=Depends(require_admin_or_visor)):
         media_type=media_type,
         headers={"Cache-Control": "private, max-age=3600"},
     )
+
+
+# ── ELIMINAR FOTOS SELECCIONADAS — solo admin ─────────────────────────────
+@router.post("/eliminar")
+def eliminar_evidencias(data: dict, current_user=Depends(verify_token)):
+    if current_user["role"] != "admin":
+        raise HTTPException(status_code=403, detail="Solo administradores pueden eliminar evidencias")
+
+    ids = data.get("ids") or []
+    ids = [int(i) for i in ids if str(i).isdigit()]
+    if not ids:
+        raise HTTPException(status_code=400, detail="No se proporcionaron IDs válidos")
+
+    placeholders = ",".join(["%s"] * len(ids))
+    eliminadas = execute_write(
+        f"DELETE FROM evidencias WHERE id IN ({placeholders})", tuple(ids)
+    )
+    return {"mensaje": f"{len(ids)} foto(s) eliminada(s)", "ids": ids}
diff --git a/backend/routers/web_router.py b/backend/routers/web_router.py
index 59fed6e..7bfc6e1 100644
--- a/backend/routers/web_router.py
+++ b/backend/routers/web_router.py
@@ -273,204 +273,150 @@ def pagina_con_menu(titulo: str, contenido: str, pagina_activa: str = "", extra_
             actualizarReloj();
             setInterval(actualizarReloj, 1000);
 
-            try {{
-                const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
-                const ws = new WebSocket(protocol + '//' + window.location.host + '/ws?token=' + encodeURIComponent(window.token || ''));
-
-                // ── Sistema de sonidos via Web Audio API ───────────────────
-                const AudioCtx = window.AudioContext || window.webkitAudioContext;
-                let _actx = null;
-                function _getCtx() {{ if (!_actx) _actx = new AudioCtx(); return _actx; }}
-
-                function _playTone(freqs, dur, waveType, vol) {{
-                    dur = dur||0.18; waveType = waveType||'sine'; vol = vol||0.35;
-                    // ── NUEVO BLOQUE DEL WEBSOCKET PROTEGIDO Y CORREGIDO ──
-            try {{
-                const tokenValido = window.token || localStorage.getItem('access_token');
-                
-                if (tokenValido && tokenValido !== 'null' && tokenValido !== 'undefined') {{
+            // ── Renovación automática de token (refresh) ──────────────────
+            async function _refreshToken() {{
+                try {{
+                    const t = window.token || localStorage.getItem('access_token');
+                    if (!t) return null;
+                    const res = await fetch('/api/auth/refresh', {{
+                        method: 'POST',
+                        headers: {{ 'Authorization': 'Bearer ' + t }}
+                    }});
+                    if (res.ok) {{
+                        const data = await res.json();
+                        window.token = data.access_token;
+                        localStorage.setItem('access_token', data.access_token);
+                        return data.access_token;
+                    }}
+                }} catch(e) {{ console.error("Error renovando token:", e); }}
+                return null;
+            }}
+            // Renovar cada 25 minutos
+            setInterval(_refreshToken, 25 * 60 * 1000);
+
+            // ── Sistema de sonidos via Web Audio API ───────────────────
+            const AudioCtx = window.AudioContext || window.webkitAudioContext;
+            let _actx = null;
+            function _getCtx() {{ if (!_actx) _actx = new AudioCtx(); return _actx; }}
+
+            function _playTone(freqs, dur, waveType, vol) {{
+                dur = dur||0.18; waveType = waveType||'sine'; vol = vol||0.35;
+                try {{
+                    const ctx = _getCtx();
+                    freqs.forEach(function(f, i) {{
+                        const osc = ctx.createOscillator();
+                        const gain = ctx.createGain();
+                        osc.connect(gain); gain.connect(ctx.destination);
+                        osc.type = waveType;
+                        osc.frequency.setValueAtTime(f, ctx.currentTime + i*dur);
+                        gain.gain.setValueAtTime(vol, ctx.currentTime + i*dur);
+                        gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + i*dur + dur);
+                        osc.start(ctx.currentTime + i*dur);
+                        osc.stop(ctx.currentTime + (i+1)*dur);
+                    }});
+                }} catch(e) {{}}
+            }}
+
+            const _SOUNDS = {{
+                solicitud_nueva:      function(){{ _playTone([660,880],0.15,'sine',0.4); }},
+                asignacion_nueva:     function(){{ _playTone([523,659,784],0.14,'triangle',0.35); }},
+                solicitud_aprobada:   function(){{ _playTone([784,988,1047],0.13,'sine',0.3); }},
+                actividad_iniciada:   function(){{ _playTone([440,554],0.16,'triangle',0.3); }},
+                actividad_completada: function(){{ _playTone([523,659,784,1047],0.12,'sine',0.4); }},
+                ticket_nuevo:         function(){{ _playTone([330,262,220],0.2,'sawtooth',0.25); }},
+            }};
+            const _LABELS = {{
+                solicitud_nueva:      'Solicitud de actividad',
+                asignacion_nueva:     'Actividad asignada',
+                solicitud_aprobada:   'Solicitud aprobada',
+                actividad_iniciada:   'Actividad iniciada',
+                actividad_completada: 'Actividad completada',
+                ticket_nuevo:         'Nuevo ticket creado',
+            }};
+            const _ICONS = {{
+                solicitud_nueva:'&#x1F4CB;', asignacion_nueva:'&#x2705;',
+                solicitud_aprobada:'&#x1F44D;', actividad_iniciada:'&#x25B6;&#xFE0F;',
+                actividad_completada:'&#x1F3C1;', ticket_nuevo:'&#x1F3AB;',
+            }};
+
+            function _showToast(evType, payload) {{
+                const label = _LABELS[evType] || evType;
+                const icon  = _ICONS[evType]  || '';
+                const t = document.createElement('div');
+                t.style.cssText = 'position:fixed;bottom:24px;right:24px;background:#1F4E78;color:#fff;'
+                    + 'padding:12px 18px;border-radius:10px;font-size:13px;font-family:Arial,sans-serif;'
+                    + 'z-index:9999;box-shadow:0 4px 16px rgba(0,0,0,.35);max-width:280px;'
+                    + 'line-height:1.4;opacity:0;transition:opacity .25s';
+                var extra = (payload && (payload.unidad || payload.unit_number || payload.tecnico))
+                    ? '<br><span style="opacity:.75;font-size:11px">'
+                        + (payload.unidad || payload.unit_number || '')
+                        + (payload.tecnico ? ' &middot; ' + payload.tecnico : '')
+                        + '</span>'
+                    : '';
+                t.innerHTML = icon + ' <strong>' + label + '</strong>' + extra;
+                document.body.appendChild(t);
+                requestAnimationFrame(function(){{ t.style.opacity = '1'; }});
+                setTimeout(function(){{ t.style.opacity = '0'; setTimeout(function(){{ t.remove(); }}, 300); }}, 4500);
+            }}
+
+            // Desbloquear AudioContext al primer click del usuario
+            document.addEventListener('click', function(){{ try{{ _getCtx().resume(); }}catch(e){{}} }}, {{once:true}});
+
+            // ── Conexión WebSocket con reconexión y token siempre actualizado ──
+            function _connectWS() {{
+                try {{
+                    const tokenValido = window.token || localStorage.getItem('access_token');
+                    if (!tokenValido || tokenValido === 'null' || tokenValido === 'undefined') {{
+                        console.warn("WebSocket pausado de forma segura: Esperando inicio de sesión.");
+                        return;
+                    }}
                     const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
                     const wsUrl = protocol + '//' + window.location.host + '/ws?token=' + encodeURIComponent(tokenValido);
-                    const ws = new WebSocket(wsUrl);
-
-                    // ── Sistema de sonidos via Web Audio API ───────────────────
-                    const AudioCtx = window.AudioContext || window.webkitAudioContext;
-                    let _actx = null;
-                    function _getCtx() {{ if (!_actx) _actx = new AudioCtx(); return _actx; }}
+                    const socket = new WebSocket(wsUrl);
 
-                    function _playTone(freqs, dur, waveType, vol) {{
-                        dur = dur||0.18; waveType = waveType||'sine'; vol = vol||0.35;
+                    socket.onmessage = function(ev) {{
                         try {{
-                            const ctx = _getCtx();
-                            freqs.forEach(function(f, i) {{
-                                const osc = ctx.createOscillator();
-                                const gain = ctx.createGain();
-                                osc.connect(gain); gain.connect(ctx.destination);
-                                osc.type = waveType;
-                                osc.frequency.setValueAtTime(f, ctx.currentTime + i*dur);
-                                gain.gain.setValueAtTime(vol, ctx.currentTime + i*dur);
-                                gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + i*dur + dur);
-                                osc.start(ctx.currentTime + i*dur);
-                                osc.stop(ctx.currentTime + (i+1)*dur);
-                            }});
+                            const d = JSON.parse(ev.data);
+                            if (d.type && d.type !== 'status' && _SOUNDS[d.type]) {{
+                                _SOUNDS[d.type]();
+                                _showToast(d.type, d.payload || {{}});
+                            }}
                         }} catch(e) {{}}
-                    }}
-
-                    const _SOUNDS = {{
-                        solicitud_nueva:      function(){{ _playTone([660,880],0.15,'sine',0.4); }},
-                        asignacion_nueva:     function(){{ _playTone([523,659,784],0.14,'triangle',0.35); }},
-                        solicitud_aprobada:   function(){{ _playTone([784,988,1047],0.13,'sine',0.3); }},
-                        actividad_iniciada:   function(){{ _playTone([440,554],0.16,'triangle',0.3); }},
-                        actividad_completada: function(){{ _playTone([523,659,784,1047],0.12,'sine',0.4); }},
-                        ticket_nuevo:         function(){{ _playTone([330,262,220],0.2,'sawtooth',0.25); }},
                     }};
-                    const _LABELS = {{
-                        solicitud_nueva:      'Solicitud de actividad',
-                        asignacion_nueva:     'Actividad asignada',
-                        solicitud_aprobada:   'Solicitud aprobada',
-                        actividad_iniciada:   'Actividad iniciada',
-                        actividad_completada: 'Actividad completada',
-                        ticket_nuevo:         'Nuevo ticket creado',
-                    }};
-                    const _ICONS = {{
-                        solicitud_nueva:'&#x1F4CB;', asignacion_nueva:'&#x2705;',
-                        solicitud_aprobada:'&#x1F44D;', actividad_iniciada:'&#x25B6;&#xFE0F;',
-                        actividad_completada:'&#x1F3C1;', ticket_nuevo:'&#x1F3AB;',
+                    socket.onerror = function(err) {{ console.error("WS Error detectado:", err); }};
+                    socket.onclose = async function(ev) {{
+                        // Si el cierre fue por token inválido/expirado, intenta renovarlo primero
+                        if (ev.code === 1008) {{
+                            await _refreshToken();
+                        }}
+                        setTimeout(_connectWS, 10000);
                     }};
-
-                    function _showToast(evType, payload) {{
-                        const label = _LABELS[evType] || evType;
-                        const icon  = _ICONS[evType]  || '';
-                        const t = document.createElement('div');
-                        t.style.cssText = 'position:fixed;bottom:24px;right:24px;background:#1F4E78;color:#fff;'
-                            + 'padding:12px 18px;border-radius:10px;font-size:13px;font-family:Arial,sans-serif;'
-                            + 'z-index:9999;box-shadow:0 4px 16px rgba(0,0,0,.35);max-width:280px;'
-                            + 'line-height:1.4;opacity:0;transition:opacity .25s';
-                        var extra = (payload && (payload.unidad || payload.unit_number || payload.tecnico))
-                            ? '<br><span style="opacity:.75;font-size:11px">'
-                                + (payload.unidad || payload.unit_number || '')
-                                + (payload.tecnico ? ' &middot; ' + payload.tecnico : '')
-                                + '</span>'
-                            : '';
-                        t.innerHTML = icon + ' <strong>' + label + '</strong>' + extra;
-                        document.body.appendChild(t);
-                        requestAnimationFrame(function(){{ t.style.opacity = '1'; }});
-                        setTimeout(function(){{ t.style.opacity = '0'; setTimeout(function(){{ t.remove(); }}, 300); }}, 4500);
-                    }}
-
-                    document.addEventListener('click', function(){{ try{{ _getCtx().resume(); }}catch(e){{}} }}, {{once:true}});
-
-                    function _attachHandlers(socket) {{
-                        socket.onmessage = function(ev) {{
-                            try {{
-                                const d = JSON.parse(ev.data);
-                                if (d.type && d.type !== 'status' && _SOUNDS[d.type]) {{
-                                    _SOUNDS[d.type]();
-                                    _showToast(d.type, d.payload || {{}});
-                                }}
-                            }} catch(e) {{}}
-                        }};
-                        socket.onerror = function(err){{ console.error("WS Error detectado:", err); }};
-                        socket.onclose = function() {{
-                            setTimeout(function() {{
-                                try {{
-                                    const t = window.token || localStorage.getItem('access_token');
-                                    if(t) {{
-                                        var ws2 = new WebSocket(protocol + '//' + window.location.host + '/ws?token=' + encodeURIComponent(t));
-                                        _attachHandlers(ws2);
-                                    }}
-                                }} catch(e) {{}}
-                            }}, 10000);
-                        }};
-                    }}
-                    _attachHandlers(ws);
-                }} else {{
-                    console.warn("WebSocket pausado de forma segura: Esperando inicio de sesión.");
-                }}
-            }} catch(e) {{ console.error("Error en inicialización del WS:", e); }}
+                }} catch(e) {{ console.error("Error en inicialización del WS:", e); }}
+            }}
+            _connectWS();
 
             // ── FUNCIÓN ADICIONAL PARA LAS IMÁGENES ROTAS (401) ──
             window.cargarImagenAutenticada = async (urlElemento, imgElementId) => {{
                 try {{
-                    const token = window.token || localStorage.getItem('access_token');
-                    const res = await fetch(urlElemento, {{
+                    let token = window.token || localStorage.getItem('access_token');
+                    let res = await fetch(urlElemento, {{
                         headers: {{ 'Authorization': 'Bearer ' + token }}
                     }});
+                    if (res.status === 401) {{
+                        token = await _refreshToken();
+                        if (token) {{
+                            res = await fetch(urlElemento, {{
+                                headers: {{ 'Authorization': 'Bearer ' + token }}
+                            }});
+                        }}
+                    }}
                     if(res.ok) {{
                         const blob = await res.blob();
                         document.getElementById(imgElementId).src = URL.createObjectURL(blob);
                     }}
                 }} catch(e) {{ console.error("Error al transferir imagen:", e); }}
             }};
-                }}
-
-                const _SOUNDS = {{
-                    solicitud_nueva:      function(){{ _playTone([660,880],0.15,'sine',0.4); }},
-                    asignacion_nueva:     function(){{ _playTone([523,659,784],0.14,'triangle',0.35); }},
-                    solicitud_aprobada:   function(){{ _playTone([784,988,1047],0.13,'sine',0.3); }},
-                    actividad_iniciada:   function(){{ _playTone([440,554],0.16,'triangle',0.3); }},
-                    actividad_completada: function(){{ _playTone([523,659,784,1047],0.12,'sine',0.4); }},
-                    ticket_nuevo:         function(){{ _playTone([330,262,220],0.2,'sawtooth',0.25); }},
-                }};
-                const _LABELS = {{
-                    solicitud_nueva:      'Solicitud de actividad',
-                    asignacion_nueva:     'Actividad asignada',
-                    solicitud_aprobada:   'Solicitud aprobada',
-                    actividad_iniciada:   'Actividad iniciada',
-                    actividad_completada: 'Actividad completada',
-                    ticket_nuevo:         'Nuevo ticket creado',
-                }};
-                const _ICONS = {{
-                    solicitud_nueva:'&#x1F4CB;', asignacion_nueva:'&#x2705;',
-                    solicitud_aprobada:'&#x1F44D;', actividad_iniciada:'&#x25B6;&#xFE0F;',
-                    actividad_completada:'&#x1F3C1;', ticket_nuevo:'&#x1F3AB;',
-                }};
-
-                function _showToast(evType, payload) {{
-                    const label = _LABELS[evType] || evType;
-                    const icon  = _ICONS[evType]  || '';
-                    const t = document.createElement('div');
-                    t.style.cssText = 'position:fixed;bottom:24px;right:24px;background:#1F4E78;color:#fff;'
-                        + 'padding:12px 18px;border-radius:10px;font-size:13px;font-family:Arial,sans-serif;'
-                        + 'z-index:9999;box-shadow:0 4px 16px rgba(0,0,0,.35);max-width:280px;'
-                        + 'line-height:1.4;opacity:0;transition:opacity .25s';
-                    var extra = (payload && (payload.unidad || payload.unit_number || payload.tecnico))
-                        ? '<br><span style="opacity:.75;font-size:11px">'
-                            + (payload.unidad || payload.unit_number || '')
-                            + (payload.tecnico ? ' &middot; ' + payload.tecnico : '')
-                            + '</span>'
-                        : '';
-                    t.innerHTML = icon + ' <strong>' + label + '</strong>' + extra;
-                    document.body.appendChild(t);
-                    requestAnimationFrame(function(){{ t.style.opacity = '1'; }});
-                    setTimeout(function(){{ t.style.opacity = '0'; setTimeout(function(){{ t.remove(); }}, 300); }}, 4500);
-                }}
 
-                // Desbloquear AudioContext al primer click del usuario
-                document.addEventListener('click', function(){{ try{{ _getCtx().resume(); }}catch(e){{}} }}, {{once:true}});
-
-                function _attachHandlers(socket) {{
-                    socket.onmessage = function(ev) {{
-                        try {{
-                            const d = JSON.parse(ev.data);
-                            if (d.type && d.type !== 'status' && _SOUNDS[d.type]) {{
-                                _SOUNDS[d.type]();
-                                _showToast(d.type, d.payload || {{}});
-                            }}
-                        }} catch(e) {{}}
-                    }};
-                    socket.onerror = function(){{}};
-                    socket.onclose = function() {{
-                        setTimeout(function() {{
-                            try {{
-                                var ws2 = new WebSocket(protocol + '//' + window.location.host + '/ws?token=' + encodeURIComponent(window.token || ''));
-                                _attachHandlers(ws2);
-                            }} catch(e) {{}}
-                        }}, 8000);
-                    }};
-                }}
-                _attachHandlers(ws);
-            }} catch(e) {{}}
 
             // ── Push Notifications (segundo plano) ────────────────────────
             function _b64ToUint8(b64) {{
@@ -1627,6 +1573,12 @@ async def admin():
             <option value="">— Selecciona unidad —</option>
           </select>
           <span id="ev-total-badge" style="font-size:13px;color:var(--color-text-secondary);"></span>
+          <button class="btn btn-ghost" onclick="evToggleSeleccion()" id="ev-btn-seleccionar" style="display:none;">
+            <i class="ti ti-checkbox"></i> Seleccionar
+          </button>
+          <button class="btn" style="background:#c0392b;color:#fff;display:none;" onclick="evEliminarSeleccionadas()" id="ev-btn-eliminar">
+            <i class="ti ti-trash"></i> Eliminar seleccionadas (<span id="ev-sel-count">0</span>)
+          </button>
           <button class="btn btn-navy" onclick="evDescargarZip()" id="ev-btn-zip" style="display:none;">
             <i class="ti ti-download"></i> Descargar ZIP
           </button>
@@ -1802,10 +1754,15 @@ async def admin():
     let evPaginaActual = 1;
     let evTotalPages   = 1;
     let evCargado      = false;
+    let evModoSeleccion = false;
+    let evSeleccionadas = new Set();
 
     async function evInicializar() {
         if (evCargado) return;
         evCargado = true;
+        if (window.role === 'admin') {
+            document.getElementById('ev-btn-seleccionar').style.display = 'inline-flex';
+        }
         const sel = document.getElementById('ev-select-unidad');
         try {
             const res = await fetchAuth('/api/evidencias/unidades-con-fotos');
@@ -1832,6 +1789,8 @@ async def admin():
         pag.innerHTML  = '';
         badge.textContent = '';
         btnZip.style.display = 'none';
+        evSeleccionadas.clear();
+        evActualizarBotonEliminar();
 
         if (!unidad) return;
 
@@ -1854,10 +1813,17 @@ async def admin():
 
             data.fotos.forEach(f => {
                 const card = document.createElement('div');
-                card.style.cssText = 'background:#f4f6fb;border-radius:10px;overflow:hidden;cursor:pointer;box-shadow:0 2px 8px rgba(0,0,0,.07);transition:transform .15s;';
+                card.style.cssText = 'position:relative;background:#f4f6fb;border-radius:10px;overflow:hidden;cursor:pointer;box-shadow:0 2px 8px rgba(0,0,0,.07);transition:transform .15s;';
                 card.onmouseenter = ()=>card.style.transform='scale(1.03)';
                 card.onmouseleave = ()=>card.style.transform='scale(1)';
-                card.onclick = ()=>evAbrirLightbox(f.id, f.nombre, f.tecnico, f.fecha);
+                card.onclick = (ev)=>{
+                    if (evModoSeleccion) {
+                        ev.stopPropagation();
+                        evToggleFoto(f.id, card);
+                    } else {
+                        evAbrirLightbox(f.id, f.nombre, f.tecnico, f.fecha);
+                    }
+                };
 
                 const img = document.createElement('img');
                 img.src   = `/api/evidencias/foto/${f.id}`;
@@ -1872,8 +1838,22 @@ async def admin():
                   👷 ${f.tecnico||'—'}<br>
                   ${f.fecha ? '🗓 '+f.fecha.slice(0,10) : ''}`;
 
+                const checkbox = document.createElement('div');
+                checkbox.className = 'ev-checkbox';
+                checkbox.dataset.id = f.id;
+                checkbox.style.cssText = 'position:absolute;top:6px;left:6px;width:22px;height:22px;'
+                    + 'border-radius:50%;border:2px solid #fff;background:rgba(0,0,0,.35);'
+                    + 'display:' + (evModoSeleccion ? 'flex' : 'none') + ';align-items:center;justify-content:center;'
+                    + 'font-size:13px;color:#fff;z-index:2;';
+                checkbox.textContent = evSeleccionadas.has(f.id) ? '✓' : '';
+                if (evSeleccionadas.has(f.id)) {
+                    checkbox.style.background = 'var(--color-navy, #1F4E78)';
+                    checkbox.style.borderColor = 'var(--color-navy, #1F4E78)';
+                }
+
                 card.appendChild(img);
                 card.appendChild(info);
+                card.appendChild(checkbox);
                 grid.appendChild(card);
             });
 
@@ -1932,6 +1912,71 @@ async def admin():
         URL.revokeObjectURL(url);
     }
 
+    function evToggleSeleccion() {
+        evModoSeleccion = !evModoSeleccion;
+        evSeleccionadas.clear();
+        evActualizarBotonEliminar();
+        const btn = document.getElementById('ev-btn-seleccionar');
+        btn.classList.toggle('btn-navy', evModoSeleccion);
+        btn.classList.toggle('btn-ghost', !evModoSeleccion);
+        btn.innerHTML = evModoSeleccion
+            ? '<i class="ti ti-x"></i> Cancelar selección'
+            : '<i class="ti ti-checkbox"></i> Seleccionar';
+        document.querySelectorAll('.ev-checkbox').forEach(cb => {
+            cb.style.display = evModoSeleccion ? 'flex' : 'none';
+            cb.textContent = '';
+            cb.style.background = 'rgba(0,0,0,.35)';
+            cb.style.borderColor = '#fff';
+        });
+    }
+
+    function evToggleFoto(id, card) {
+        const cb = card.querySelector('.ev-checkbox');
+        if (evSeleccionadas.has(id)) {
+            evSeleccionadas.delete(id);
+            cb.textContent = '';
+            cb.style.background = 'rgba(0,0,0,.35)';
+            cb.style.borderColor = '#fff';
+        } else {
+            evSeleccionadas.add(id);
+            cb.textContent = '✓';
+            cb.style.background = 'var(--color-navy, #1F4E78)';
+            cb.style.borderColor = 'var(--color-navy, #1F4E78)';
+        }
+        evActualizarBotonEliminar();
+    }
+
+    function evActualizarBotonEliminar() {
+        const btn = document.getElementById('ev-btn-eliminar');
+        const count = document.getElementById('ev-sel-count');
+        count.textContent = evSeleccionadas.size;
+        btn.style.display = evSeleccionadas.size > 0 ? 'inline-flex' : 'none';
+    }
+
+    async function evEliminarSeleccionadas() {
+        if (evSeleccionadas.size === 0) return;
+        const ids = Array.from(evSeleccionadas);
+        if (!confirm(`¿Eliminar ${ids.length} foto(s)? Esta acción no se puede deshacer.`)) return;
+
+        try {
+            const res = await fetchAuth('/api/evidencias/eliminar', {
+                method: 'POST',
+                headers: { 'Content-Type': 'application/json' },
+                body: JSON.stringify({ ids })
+            });
+            if (!res.ok) {
+                const err = await res.json().catch(()=>({}));
+                alert('Error al eliminar: ' + (err.detail || res.statusText));
+                return;
+            }
+            evToggleSeleccion(); // salir del modo selección
+            await evCargarFotos(evPaginaActual);
+        } catch(e) {
+            alert('Error de red al eliminar.');
+            console.error('evEliminarSeleccionadas', e);
+        }
+    }
+
     // -- Editar Actividades -----------------------------------
     function editarFilaAct(id) {
         editing.act=id;
diff --git a/backend/routers/ws.py b/backend/routers/ws.py
index f1e08fd..1a7de4d 100644
--- a/backend/routers/ws.py
+++ b/backend/routers/ws.py
@@ -80,6 +80,7 @@ async def notify(event: str, payload: dict = None):
 @router.websocket("/ws")
 async def websocket_endpoint(websocket: WebSocket, token: str = Query(default=None)):
     if not token:
+        await websocket.accept()
         await websocket.close(code=1008)
         return
     try:
@@ -87,6 +88,7 @@ async def websocket_endpoint(websocket: WebSocket, token: str = Query(default=No
         if not payload.get("sub"):
             raise ValueError("Token sin usuario")
     except (JWTError, ValueError):
+        await websocket.accept()
         await websocket.close(code=1008)
         return
