#!/usr/bin/env python3
"""
cargar_alarmas.py
Carga (o actualiza) las 226 alarmas del JSON en la tabla alarmas_reefer.
Ejecutar UNA VEZ en el servidor tras hacer deploy:
    python cargar_alarmas.py
"""
import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

import pymysql

JSON_PATH = Path(__file__).parent / "alarmas.json"


def main():
    if not JSON_PATH.exists():
        print(f"❌ No se encontró {JSON_PATH}")
        sys.exit(1)

    alarmas = json.loads(JSON_PATH.read_text(encoding="utf-8"))
    print(f"📦 {len(alarmas)} alarmas leídas del JSON")

    conn = pymysql.connect(
        host=os.getenv("DB_HOST"),
        port=int(os.getenv("DB_PORT", 3306)),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME"),
        charset="utf8mb4",
    )

    insertadas = 0
    actualizadas = 0

    try:
        with conn.cursor() as cur:
            for a in alarmas:
                cur.execute(
                    """
                    INSERT INTO alarmas_reefer
                        (codigo, titulo, activacion, control_unidad,
                         condicion_reset, notas, acciones_correctivas,
                         referencia_alarma, alarmas_relacionadas, figuras)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                    ON DUPLICATE KEY UPDATE
                        titulo              = VALUES(titulo),
                        activacion          = VALUES(activacion),
                        control_unidad      = VALUES(control_unidad),
                        condicion_reset     = VALUES(condicion_reset),
                        notas               = VALUES(notas),
                        acciones_correctivas= VALUES(acciones_correctivas),
                        referencia_alarma   = VALUES(referencia_alarma),
                        alarmas_relacionadas= VALUES(alarmas_relacionadas),
                        figuras             = VALUES(figuras)
                    """,
                    (
                        a["codigo"],
                        a["titulo"],
                        a.get("activacion"),
                        a.get("control_unidad"),
                        a.get("condicion_reset"),
                        a.get("notas"),
                        json.dumps(a.get("acciones_correctivas") or [], ensure_ascii=False),
                        json.dumps(a.get("referencia_alarma"), ensure_ascii=False),
                        json.dumps(a.get("alarmas_relacionadas") or [], ensure_ascii=False),
                        json.dumps(a.get("figuras") or [], ensure_ascii=False),
                    ),
                )
                if cur.rowcount == 1:
                    insertadas += 1
                else:
                    actualizadas += 1
        conn.commit()
        print(f"✅ Listo: {insertadas} insertadas, {actualizadas} actualizadas")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
