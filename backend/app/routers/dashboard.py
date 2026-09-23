"""Series agregadas para las graficas del tablero (`index.html`) y de
reportes: facturacion mensual, servicios por semana y mezcla de servicios
por categoria de refaccion."""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends

from ..auth import require_auth
from ..database import query_all

router = APIRouter(prefix="/api", tags=["dashboard"], dependencies=[Depends(require_auth)])

MESES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]


def _ultimos_meses(n: int) -> list[tuple[int, int]]:
    hoy = date.today()
    anio, mes = hoy.year, hoy.month
    meses = []
    for _ in range(n):
        meses.append((anio, mes))
        mes -= 1
        if mes == 0:
            mes = 12
            anio -= 1
    return list(reversed(meses))


@router.get("/dashboard")
def dashboard():
    # ---- Facturacion mensual (ultimos 7 meses, incluido el actual) ----
    filas = {
        (int(r["anio"]), int(r["mes"])): r["total"]
        for r in query_all(
            """SELECT CAST(strftime('%Y', fecha_entrega) AS INTEGER) AS anio,
                      CAST(strftime('%m', fecha_entrega) AS INTEGER) AS mes,
                      SUM(costo_total) AS total
                 FROM ordenes_servicio
                WHERE estatus = 'Entregado'
                  AND fecha_entrega >= date('now', '-7 months', 'start of month')
                GROUP BY anio, mes"""
        )
    }
    ingresos_mensuales = [
        {"mes": MESES[mes - 1], "valor": round(filas.get((anio, mes), 0) or 0, 2)}
        for anio, mes in _ultimos_meses(7)
    ]

    # ---- Servicios por semana (ultimas 7 semanas) ----
    semanas_raw = query_all(
        """SELECT strftime('%Y-%W', fecha_ingreso) AS semana,
                  CAST(strftime('%W', fecha_ingreso) AS INTEGER) AS num,
                  COUNT(*) AS total
             FROM ordenes_servicio
            WHERE fecha_ingreso >= date('now', '-49 days')
            GROUP BY semana
            ORDER BY semana"""
    )
    servicios_por_semana = [
        {"sem": f"S{f['num']}", "valor": f["total"]} for f in semanas_raw[-7:]
    ]

    # ---- Mezcla de servicios por categoria de refaccion (ultimos 6 meses) ----
    tipos_servicio = query_all(
        """SELECT r.categoria AS nombre, COUNT(DISTINCT orf.id_orden) AS valor
             FROM orden_refacciones orf
             JOIN refacciones r        ON r.id_refaccion = orf.id_refaccion
             JOIN ordenes_servicio o   ON o.id_orden = orf.id_orden
            WHERE o.fecha_ingreso >= date('now', '-180 days')
            GROUP BY r.categoria
            ORDER BY valor DESC
            LIMIT 8"""
    )

    # ---- Indicadores del mismo periodo de 7 meses que ingresos_mensuales ----
    resumen = query_all(
        """SELECT COUNT(*) AS ordenes,
                  COALESCE(SUM(costo_total), 0) AS facturacion,
                  AVG(julianday(fecha_entrega) - julianday(fecha_ingreso)) AS dias_promedio
             FROM ordenes_servicio
            WHERE estatus = 'Entregado'
              AND fecha_entrega >= date('now', '-7 months', 'start of month')"""
    )[0]
    ordenes_cerradas = resumen["ordenes"] or 0
    facturacion_periodo = round(resumen["facturacion"] or 0, 2)
    resumen_periodo = {
        "facturacion": facturacion_periodo,
        "ordenesCerradas": ordenes_cerradas,
        "ticketPromedio": round(facturacion_periodo / ordenes_cerradas, 2) if ordenes_cerradas else 0,
        "diasPromedioTaller": round(resumen["dias_promedio"], 1) if resumen["dias_promedio"] is not None else 0,
    }

    return {
        "ingresosMensuales": ingresos_mensuales,
        "serviciosPorSemana": servicios_por_semana,
        "tiposServicio": tipos_servicio,
        "resumenPeriodo": resumen_periodo,
    }
