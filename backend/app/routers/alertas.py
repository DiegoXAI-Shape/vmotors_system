"""Motor de alertas de mantenimiento preventivo: unidades con seis meses o
mas desde su ultima orden entregada (equivalente a la vista
`v_alertas_mantenimiento` del script de PostgreSQL, adaptada a SQLite)."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from ..auth import require_auth
from ..database import query_all

router = APIRouter(prefix="/api", tags=["alertas"], dependencies=[Depends(require_auth)])


@router.get("/alertas")
def listar_alertas():
    filas = query_all(
        """SELECT v.id_vehiculo,
                  MAX(o.fecha_entrega)                                             AS ultima_visita,
                  ROUND((julianday('now') - julianday(MAX(o.fecha_entrega))) / 30.44, 1) AS meses
             FROM vehiculos v
             JOIN citas c            ON c.id_vehiculo = v.id_vehiculo
             JOIN ordenes_servicio o ON o.id_cita     = c.id_cita
            WHERE o.fecha_entrega IS NOT NULL
            GROUP BY v.id_vehiculo
           HAVING julianday('now') - julianday(MAX(o.fecha_entrega)) >= 182.5
            ORDER BY meses DESC"""
    )
    for f in filas:
        meses = f["meses"] or 0
        f["prioridad"] = "alta" if meses >= 7 else ("media" if meses >= 6 else "baja")
        f["servicio_sugerido"] = "Servicio de mantenimiento preventivo"
    return filas
