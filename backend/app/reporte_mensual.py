"""Resumen mensual para el dueno del taller: se envia por correo a
`CORREO_DUENO` con el PDF de reportes adjunto.

Ademas del boton "Enviar al dueño" en Reportes, el backend revisa cada hora
(mientras esta encendido) si ya se mando el resumen del mes anterior; si no,
lo envia solo. Asi, aunque la laptop del taller este apagada el dia 1, el
reporte sale en cuanto se vuelve a encender el sistema.
"""

from __future__ import annotations

import asyncio
import logging
import os
from datetime import date

from fastapi import HTTPException

from . import correo
from .correo import Adjunto, esc, plantilla
from .database import query_one

log = logging.getLogger("vmotors.reporte_mensual")

MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
         "agosto", "septiembre", "octubre", "noviembre", "diciembre"]


def _mes_anterior(hoy: date | None = None) -> tuple[int, int]:
    hoy = hoy or date.today()
    return (hoy.year, hoy.month - 1) if hoy.month > 1 else (hoy.year - 1, 12)


def _resumen_de_mes(anio: int, mes: int) -> dict:
    inicio = f"{anio:04d}-{mes:02d}-01"
    fin = f"{anio + (mes == 12):04d}-{(mes % 12) + 1:02d}-01"
    r = query_one(
        """SELECT COUNT(*) AS ordenes, COALESCE(SUM(costo_total), 0) AS facturacion,
                  AVG(julianday(fecha_entrega) - julianday(fecha_ingreso)) AS dias
             FROM ordenes_servicio
            WHERE estatus = 'Entregado' AND fecha_entrega >= ? AND fecha_entrega < ?""",
        (inicio, fin),
    )
    abiertas = query_one("SELECT COUNT(*) AS n FROM ordenes_servicio WHERE estatus <> 'Entregado'")["n"]
    return {**r, "abiertas": abiertas}


def enviar_reporte_mensual(destinatario: str | None = None, referencia: str = "manual") -> correo.ResultadoEnvio:
    from .routers.reportes import construir_pdf_mensual  # import tardio: evita ciclo

    para = (destinatario or correo.correo_dueno() or "").strip()
    if not para:
        raise HTTPException(
            409, "No hay correo del dueño configurado. Defina CORREO_DUENO en backend/.env "
                 "o escriba el destinatario.")
    anio, mes = _mes_anterior()
    r = _resumen_de_mes(anio, mes)
    n = r["ordenes"] or 0
    ticket = (r["facturacion"] / n) if n else 0
    nombre_mes = f"{MESES[mes - 1]} {anio}"
    cuerpo = plantilla(
        f"Resumen mensual · {nombre_mes}",
        "Hola:",
        [f"Este es el resumen de operación de VMotors correspondiente a <strong>{esc(nombre_mes)}</strong>. "
         "Adjuntamos el PDF con la facturación de los últimos meses y los servicios por categoría."],
        tabla=[
            ("Facturación del mes", f"${r['facturacion']:,.2f}"),
            ("Órdenes entregadas", str(n)),
            ("Ticket promedio", f"${ticket:,.2f}"),
            ("Días promedio en taller", f"{r['dias']:.1f}" if r["dias"] else "—"),
            ("Órdenes abiertas hoy", str(r["abiertas"])),
        ],
        nota="Reporte generado automáticamente por el sistema VMotors.",
    )
    return correo.enviar(
        tipo="reporte_mensual", referencia=referencia, destinatario=para,
        asunto=f"VMotors · Resumen mensual de {nombre_mes}", cuerpo_html=cuerpo,
        adjuntos=[Adjunto(f"vmotors-resumen-{anio}-{mes:02d}.pdf", construir_pdf_mensual(7))],
    )


def revisar_envio_programado() -> correo.ResultadoEnvio | None:
    """Envia el resumen del mes anterior si todavia no se ha enviado."""
    if not correo.correo_dueno():
        return None
    anio, mes = _mes_anterior()
    periodo = f"{anio:04d}-{mes:02d}"
    correo.asegurar_tabla()
    ya = query_one(
        "SELECT 1 AS x FROM correos_enviados WHERE tipo = 'reporte_mensual' AND referencia = ? "
        "AND estado = 'enviado'", (periodo,))
    if ya:
        return None
    log.info("Enviando resumen mensual de %s a %s", periodo, correo.correo_dueno())
    return enviar_reporte_mensual(referencia=periodo)


async def tarea_programada() -> None:
    if os.getenv("REPORTE_MENSUAL_AUTOMATICO", "1").strip().lower() in ("0", "no", "false"):
        return
    while True:
        try:
            await asyncio.to_thread(revisar_envio_programado)
        except Exception:  # noqa: BLE001
            log.exception("Fallo la revisión del envío mensual programado")
        await asyncio.sleep(60 * 60)
