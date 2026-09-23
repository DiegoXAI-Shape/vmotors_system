"""Reportes descargables en PDF: diario, historial por placa y resumen
mensual. Son la version imprimible/archivable de lo que `reportes.html` ya
muestra en pantalla con datos en vivo."""

from __future__ import annotations

from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response

from ..auth import require_auth
from ..database import query_all, query_one
from ..pdf import encabezado, fila_kpis, generar_pdf, seccion, tabla

router = APIRouter(prefix="/api/reportes", tags=["reportes"], dependencies=[Depends(require_auth)])

MESES_LARGO = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
               "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
MESES_CORTO = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]
BLOQUES_HORARIOS = ["08:00", "09:00", "10:00", "11:00", "12:00", "13:00", "14:00", "15:00", "16:00", "17:00"]


def _money(v) -> str:
    v = v or 0
    return f"${v:,.2f}"


def _fecha(iso: str | None) -> str:
    if not iso:
        return "—"
    y, m, d = iso[:10].split("-")
    return f"{int(d)} {MESES_CORTO[int(m) - 1]} {y}"


def _pdf_response(contenido: bytes, nombre_archivo: str) -> Response:
    return Response(
        content=contenido,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{nombre_archivo}"'},
    )


@router.get("/diario.pdf")
def reporte_diario_pdf():
    hoy = date.today().isoformat()
    citas_hoy = query_all(
        """SELECT c.hora_inicio, c.hora_fin, c.motivo_ingreso, c.estatus_cita, c.id_cita,
                  v.placas, v.marca, v.modelo,
                  cl.nombre, cl.apellido, cl.telefono,
                  o.estatus AS estatus_orden
             FROM citas c
             JOIN vehiculos v ON v.id_vehiculo = c.id_vehiculo
             JOIN clientes  cl ON cl.id_cliente = v.id_cliente
             LEFT JOIN ordenes_servicio o ON o.id_cita = c.id_cita
            WHERE c.fecha = ? AND c.estatus_cita <> 'Cancelada'
            ORDER BY c.hora_inicio""",
        (hoy,),
    )

    ocupadas = {c["hora_inicio"][:5] for c in citas_hoy}
    horas = sum(int(c["hora_fin"][:2]) - int(c["hora_inicio"][:2]) for c in citas_hoy)
    libres = [h for h in BLOQUES_HORARIOS if h not in ocupadas]

    def construir(el):
        d = date.today()
        encabezado(el, "Reporte diario de citas y bahías",
                   f"{d.day} de {MESES_LARGO[d.month - 1]} de {d.year}")
        fila_kpis(el, [
            ("Citas confirmadas", str(len(citas_hoy))),
            ("Bloques libres", str(len(libres))),
            ("Horas comprometidas", f"{horas}h"),
            ("Ocupación", f"{round(len(ocupadas) / len(BLOQUES_HORARIOS) * 100)}%"),
        ])
        seccion(el, "Agenda cronológica del día")
        tabla(el, ["Bloque", "Unidad", "Cliente", "Motivo", "Estatus"], [
            [f"{c['hora_inicio'][:5]}–{c['hora_fin'][:5]}",
             f"{c['marca']} {c['modelo']} ({c['placas']})",
             f"{c['nombre']} {c['apellido']}",
             c["motivo_ingreso"],
             c["estatus_orden"] or c["estatus_cita"]]
            for c in citas_hoy
        ], anchos=None)
        seccion(el, "Bloques disponibles para atención inmediata")
        tabla(el, ["Horario libre"], [[h] for h in libres] or [["Sin bloques libres"]])

    pdf = generar_pdf(construir)
    return _pdf_response(pdf, f"vmotors-reporte-diario-{hoy}.pdf")


@router.get("/placa/{id_vehiculo}.pdf")
def reporte_placa_pdf(id_vehiculo: int):
    vehiculo = query_one(
        """SELECT v.*, cl.nombre, cl.apellido, cl.telefono, cl.correo
             FROM vehiculos v JOIN clientes cl ON cl.id_cliente = v.id_cliente
            WHERE v.id_vehiculo = ?""",
        (id_vehiculo,),
    )
    if not vehiculo:
        raise HTTPException(404, "El vehículo indicado no existe.")

    visitas = query_all(
        """SELECT c.fecha, c.motivo_ingreso, o.folio, o.diagnostico, o.kilometraje,
                  o.costo_total, o.estatus
             FROM citas c
             LEFT JOIN ordenes_servicio o ON o.id_cita = c.id_cita
            WHERE c.id_vehiculo = ? AND c.estatus_cita <> 'Cancelada'
            ORDER BY c.fecha DESC""",
        (id_vehiculo,),
    )
    total_pagado = sum(v["costo_total"] or 0 for v in visitas)

    def construir(el):
        encabezado(el, f"{vehiculo['marca']} {vehiculo['modelo']} {vehiculo['anio']}",
                   f"Placas {vehiculo['placas']} · Propietario: {vehiculo['nombre']} {vehiculo['apellido']}")
        fila_kpis(el, [
            ("Visitas registradas", str(len(visitas))),
            ("Transmisión", vehiculo["transmision"]),
            ("Teléfono", vehiculo["telefono"]),
            ("Acumulado pagado", _money(total_pagado)),
        ])
        seccion(el, "Bitácora acumulativa de servicios")
        tabla(el, ["Fecha", "Folio", "Trabajo realizado", "Km", "Importe"], [
            [_fecha(v["fecha"]), v["folio"] or "—",
             (v["diagnostico"] or v["motivo_ingreso"] or "—")[:70],
             f"{v['kilometraje']:,}" if v["kilometraje"] else "—",
             _money(v["costo_total"]) if v["costo_total"] else "—"]
            for v in visitas
        ])

    pdf = generar_pdf(construir)
    return _pdf_response(pdf, f"vmotors-historial-{vehiculo['placas']}.pdf")


@router.get("/mensual.pdf")
def reporte_mensual_pdf(meses: int = Query(default=7, ge=2, le=24)):
    filas = {
        (int(r["anio"]), int(r["mes"])): r["total"]
        for r in query_all(
            f"""SELECT CAST(strftime('%Y', fecha_entrega) AS INTEGER) AS anio,
                      CAST(strftime('%m', fecha_entrega) AS INTEGER) AS mes,
                      SUM(costo_total) AS total
                 FROM ordenes_servicio
                WHERE estatus = 'Entregado'
                  AND fecha_entrega >= date('now', '-{meses} months', 'start of month')
                GROUP BY anio, mes"""
        )
    }
    hoy = date.today()
    anio, mes = hoy.year, hoy.month
    secuencia = []
    for _ in range(meses):
        secuencia.append((anio, mes))
        mes -= 1
        if mes == 0:
            mes, anio = 12, anio - 1
    secuencia.reverse()
    ingresos = [(f"{MESES_CORTO[m - 1]} {a}", filas.get((a, m), 0) or 0) for a, m in secuencia]

    resumen = query_all(
        f"""SELECT COUNT(*) AS ordenes, COALESCE(SUM(costo_total), 0) AS facturacion,
                  AVG(julianday(fecha_entrega) - julianday(fecha_ingreso)) AS dias_promedio
             FROM ordenes_servicio
            WHERE estatus = 'Entregado'
              AND fecha_entrega >= date('now', '-{meses} months', 'start of month')"""
    )[0]
    n_ordenes = resumen["ordenes"] or 0
    facturacion = resumen["facturacion"] or 0

    tipos = query_all(
        f"""SELECT r.categoria AS nombre, COUNT(DISTINCT orf.id_orden) AS valor
             FROM orden_refacciones orf
             JOIN refacciones r      ON r.id_refaccion = orf.id_refaccion
             JOIN ordenes_servicio o ON o.id_orden = orf.id_orden
            WHERE o.fecha_ingreso >= date('now', '-{meses} months')
            GROUP BY r.categoria
            ORDER BY valor DESC"""
    )

    def construir(el):
        encabezado(el, "Resumen mensual",
                   f"Últimos {meses} meses · generado el {_fecha(datetime.now().isoformat())}")
        fila_kpis(el, [
            ("Facturación acumulada", _money(facturacion)),
            ("Órdenes cerradas", str(n_ordenes)),
            ("Ticket promedio", _money(facturacion / n_ordenes if n_ordenes else 0)),
            ("Días promedio en taller", f"{resumen['dias_promedio']:.1f}" if resumen["dias_promedio"] else "0"),
        ])
        seccion(el, "Facturación por mes")
        tabla(el, ["Mes", "Facturación"], [[m, _money(v)] for m, v in ingresos])
        seccion(el, "Servicios por categoría de refacción")
        tabla(el, ["Categoría", "Órdenes"], [[t["nombre"], str(t["valor"])] for t in tipos])

    pdf = generar_pdf(construir)
    return _pdf_response(pdf, f"vmotors-resumen-mensual-{date.today().isoformat()}.pdf")
