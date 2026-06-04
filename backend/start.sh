#!/bin/bash

# Asegurar que el script se detenga si ocurre un error intermedio
set -e

echo "🚀 Iniciando entorno de producción (Junio 2026) — build $(date +%s)..."

# Moverse al directorio del backend donde se encuentran main.py y las rutas
cd "$(dirname "$0")"

# ── Pasos Previos (Opcional) ──────────────────────────────────────────────────
# Aquí puedes agregar comandos iniciales si los necesitas, por ejemplo:
# python -m migrations_or_setup
# ──────────────────────────────────────────────────────────────────────────────

echo "🔥 Delegando control de ejecución a Uvicorn ASGI..."

# CRÍTICO: Usar 'exec' para que Uvicorn tome el PID 1 del contenedor.
# Esto previene que Clever Cloud detecte el proceso como colgado o inactivo.
exec uvicorn main:app --host 0.0.0.0 --port 9000 --workers 1 --log-level info
