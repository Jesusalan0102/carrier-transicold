=================================================================
INSTRUCCIONES: Abre web_router.py y busca la función fetchAuth
dentro de pagina_con_menu(). Está aproximadamente en la línea:

    window.fetchAuth = async (url, options) => {{

Reemplaza TODO el bloque (hasta el cierre }};) por este:
=================================================================

            window.fetchAuth = async (url, options) => {{
                options = options || {{}};
                // FIX: Object.assign preserva Content-Type y otros headers del caller
                const headers = Object.assign({{}}, options.headers || {{}});
                headers['Authorization'] = 'Bearer ' + window.token;
                try {{
                    const res = await fetch(url, {{ ...options, headers }});
                    if (res.status === 401) {{
                        localStorage.clear();
                        window.location.href = '/app';
                        return null;
                    }}
                    return res;
                }} catch (networkErr) {{
                    // FIX: capturar errores de red reales y devolver objeto compatible
                    console.error('[fetchAuth] Error de red:', networkErr);
                    return {{
                        ok:     false,
                        status: 503,
                        json:   async () => ({{ detail: 'Sin conexión al servidor. Intenta de nuevo.' }}),
                    }};
                }}
            }};

=================================================================
