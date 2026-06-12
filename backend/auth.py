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
 
diff --git a/backend/routers/web_router.py b/backend/routers/web_router.py
index 59fed6e..56fe511 100644
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
-
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
