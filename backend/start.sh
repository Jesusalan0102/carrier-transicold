#!/bin/bash
cd /home/bas/app_83fd3b1b-5d1d-43fd-be37-63f56db0efe8/backend
exec /home/bas/venv/bin/uvicorn main:app --host 0.0.0.0 --port $PORT
