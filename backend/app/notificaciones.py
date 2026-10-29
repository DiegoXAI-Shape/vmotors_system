"""Contenido de cada correo que manda el taller y el PDF del comprobante.

Se separa de los routers para poder reutilizarlo: el comprobante se envia
tanto desde el boton "Enviar al cliente" como automaticamente cuando una
orden se marca como Entregada, y el portal del cliente descarga el mismo PDF.
"""

from __future__ import annotations

import os
from datetime import date, datetime, timedelta

from fastapi import HTTPException

from . import correo
from .correo import Adjunto, esc, plantilla
from .database import query_all, query_one
from reportlab.platypus import Paragraph, Spacer

from .pdf import DIM, NORMAL, encabezado, fila_kpis, generar_pdf, seccion, tabla

MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
         "agosto", "septiembre", "octubre", "noviembre", "diciembre"]

# Ciclo de mantenimiento preventivo (mismo criterio que el motor de alertas)
MESES_CICLO = 6
DIAS_ENTRE_RECORDATORIOS = 30


def notificaciones_automaticas() -> bool:
    return os.getenv("NOTIFICACIONES_AUTOMATICAS", "1").strip().lower() not in ("0", "no", "false")


def _money(v) -> str:
    return f"${(v or 0):,.2f}"


def _fecha_larga(iso: str | date | None) -> str:
    if not iso:
        return "—"
    if isinstance(iso, str):
        iso = date.fromisoformat(iso[:10])
    return f"{iso.day} de {MESES[iso.month - 1]} de {iso.year}"


# ---------------------------------------------------------------------------
# Datos de una orden
# ---------------------------------------------------------------------------

def datos_orden(id_orden: int) -> dict:
    o = query_one(
        """SELECT o.*, c.motivo_ingreso, c.fecha AS fecha_cita, c.id_vehiculo,
                  v.placas, v.marca, v.modelo, v.anio, v.color, v.transmision,
                  cl.id_cliente, cl.nombre, cl.apellido, cl.correo, cl.telefono,
                  cl.razon_social, cl.rfc, cl.acepta_promociones
             FROM ordenes_servicio o
             JOIN citas c      ON c.id_cita = o.id_cita
             JOIN vehiculos v  ON v.id_vehiculo = c.id_vehiculo
             JOIN clientes cl  ON cl.id_cliente = v.id_cliente
            WHERE o.id_orden = ?""",
        (id_orden,),
    )
    if not o:
        raise HTTPException(404, "La orden indicada no existe.")
    o["detalle"] = query_all(
        """SELECT r.clave, r.descripcion, d.cantidad, d.precio_unitario, d.importe
             FROM orden_refacciones d JOIN refacciones r ON r.id_refaccion = d.id_refaccion
            WHERE d.id_orden = ? ORDER BY d.id_detalle""",
        (id_orden,),
    )
    return o


def pdf_comprobante(o: dict) -> bytes:
    def construir(el):
        encabezado(el, f"Comprobante de servicio · {o['folio']}",
                   f"{o['marca']} {o['modelo']} {o['anio']} · Placas {o['placas']} · "
                   f"Cliente: {o['nombre']} {o['apellido']}")
        fila_kpis(el, [
            ("Ingreso", _fecha_larga(o["fecha_ingreso"])),
            ("Entrega", _fecha_larga(o["fecha_entrega"]) if o["fecha_entrega"] else "Pendiente"),
            ("Estatus", o["estatus"]),
            ("Total", _money(o["costo_total"])),
        ])
        seccion(el, "Motivo de ingreso")
        el.append(Paragraph(esc(o["motivo_ingreso"]), NORMAL))
        seccion(el, "Diagnóstico y reparaciones realizadas")
        el.append(Paragraph(esc(o["diagnostico"] or "Pendiente de captura."), NORMAL))
        seccion(el, "Refacciones instaladas")
        tabla(el, ["Clave", "Descripción", "Cant.", "P. unitario", "Importe"], [
            [d["clave"], d["descripcion"], str(d["cantidad"]), _money(d["precio_unitario"]),
             _money(d["importe"])] for d in o["detalle"]
        ])
        seccion(el, "Totales")
        tabla(el, ["Concepto", "Importe"], [
            ["Refacciones", _money(o["costo_refacciones"])],
            ["Mano de obra", _money(o["costo_mano_obra"])],
            ["<b>Total</b>", f"<b>{_money(o['costo_total'])}</b>"],
        ])
        el.append(Spacer(1, 8))
        el.append(Paragraph(
            "Garantía de 30 días naturales o 3,000 km, lo que ocurra primero, sobre el servicio descrito. "
            "No cubre daños por uso indebido ni piezas suministradas por el cliente.", DIM))

    return generar_pdf(construir)


# ---------------------------------------------------------------------------
# Comprobante
# ---------------------------------------------------------------------------

def _destino(destinatario: str | None, correo_cliente: str | None) -> str:
    d = (destinatario or correo_cliente or "").strip()
    if not d:
        raise HTTPException(
            409, "El cliente no tiene correo registrado. Capture uno en su expediente o escriba el destinatario.")
    return d


def enviar_comprobante(id_orden: int, destinatario: str | None = None) -> correo.ResultadoEnvio:
    o = datos_orden(id_orden)
    para = _destino(destinatario, o["correo"])
    cuerpo = plantilla(
        f"Comprobante de servicio {o['folio']}",
        f"Hola, {o['nombre']}:",
        [
            f"Te compartimos el comprobante del servicio de tu <strong>{esc(o['marca'])} {esc(o['modelo'])}</strong> "
            f"(placas {esc(o['placas'])}). Lo encontrarás adjunto en PDF.",
            "Gracias por confiar en VMotors.",
        ],
        tabla=[
            ("Folio", o["folio"]),
            ("Estatus", o["estatus"]),
            ("Fecha de entrega", _fecha_larga(o["fecha_entrega"]) if o["fecha_entrega"] else "Pendiente"),
            ("Total", _money(o["costo_total"])),
        ],
        nota="Puedes consultar el avance y el historial de tu vehículo en el portal de clientes, "
             "entrando con tus placas y tu número de teléfono.",
    )
    return correo.enviar(
        tipo="comprobante", referencia=str(id_orden), destinatario=para,
        asunto=f"Tu comprobante de servicio VMotors · {o['folio']}", cuerpo_html=cuerpo,
        adjuntos=[Adjunto(f"comprobante-{o['folio']}.pdf", pdf_comprobante(o))],
    )


# ---------------------------------------------------------------------------
# Seguimiento automatico al cambiar de estatus
# ---------------------------------------------------------------------------

def avisar_cambio_estatus(id_orden: int, estatus: str) -> correo.ResultadoEnvio | None:
    """Correo de seguimiento cuando la unidad esta lista o ya se entrego.
    Nunca rompe la operacion del taller: si falla, solo queda registrado."""
    if not notificaciones_automaticas() or estatus not in ("Terminado", "Entregado"):
        return None
    try:
        o = datos_orden(id_orden)
        if not o["correo"]:
            return None
        if estatus == "Entregado":
            # Al entregar, el seguimiento es el propio comprobante + la fecha
            # sugerida del siguiente mantenimiento.
            return enviar_comprobante(id_orden)
        cuerpo = plantilla(
            "Tu vehículo está listo",
            f"Hola, {o['nombre']}:",
            [
                f"Terminamos el servicio de tu <strong>{esc(o['marca'])} {esc(o['modelo'])}</strong> "
                f"(placas {esc(o['placas'])}). Ya puedes pasar a recogerlo.",
                "Nuestro horario es de lunes a sábado de 8:00 a 18:00 h.",
            ],
            tabla=[("Folio", o["folio"]), ("Total a pagar", _money(o["costo_total"]))],
        )
        return correo.enviar(
            tipo="seguimiento", referencia=str(id_orden), destinatario=o["correo"],
            asunto=f"Tu {o['marca']} {o['modelo']} está listo · VMotors", cuerpo_html=cuerpo,
        )
    except Exception:  # noqa: BLE001
        correo.log.exception("No se pudo generar el aviso de seguimiento de la orden %s", id_orden)
        return None


# ---------------------------------------------------------------------------
# Recordatorios de mantenimiento preventivo
# ---------------------------------------------------------------------------

def enviar_recordatorio(id_vehiculo: int, destinatario: str | None = None,
                        forzar: bool = False) -> dict:
    v = query_one(
        """SELECT v.id_vehiculo, v.placas, v.marca, v.modelo, v.anio,
                  cl.nombre, cl.apellido, cl.correo, cl.acepta_promociones,
                  (SELECT MAX(o.fecha_entrega) FROM ordenes_servicio o
                     JOIN citas c ON c.id_cita = o.id_cita
                    WHERE c.id_vehiculo = v.id_vehiculo) AS ultima_visita,
                  (SELECT o.kilometraje FROM ordenes_servicio o
                     JOIN citas c ON c.id_cita = o.id_cita
                    WHERE c.id_vehiculo = v.id_vehiculo AND o.kilometraje IS NOT NULL
                    ORDER BY o.fecha_ingreso DESC LIMIT 1) AS ultimo_km
             FROM vehiculos v JOIN clientes cl ON cl.id_cliente = v.id_cliente
            WHERE v.id_vehiculo = ?""",
        (id_vehiculo,),
    )
    if not v:
        return {"id_vehiculo": id_vehiculo, "ok": False, "motivo": "El vehículo no existe."}
    if not destinatario:
        if not v["correo"]:
            return {"id_vehiculo": id_vehiculo, "placas": v["placas"], "ok": False,
                    "motivo": "Sin correo registrado."}
        if not v["acepta_promociones"]:
            return {"id_vehiculo": id_vehiculo, "placas": v["placas"], "ok": False,
                    "motivo": "No autorizó recibir correos."}
    if not forzar and correo.enviado_recientemente("recordatorio", str(id_vehiculo), DIAS_ENTRE_RECORDATORIOS):
        return {"id_vehiculo": id_vehiculo, "placas": v["placas"], "ok": False,
                "motivo": f"Ya se le envió un recordatorio en los últimos {DIAS_ENTRE_RECORDATORIOS} días."}

    meses = None
    if v["ultima_visita"]:
        dias = (datetime.now() - datetime.fromisoformat(v["ultima_visita"][:19])).days
        meses = round(dias / 30.44, 1)
    cuerpo = plantilla(
        "Es momento de dar mantenimiento a tu vehículo",
        f"Hola, {v['nombre']}:",
        [
            f"Han pasado <strong>{meses if meses is not None else 'varios'} meses</strong> desde el último servicio "
            f"de tu <strong>{esc(v['marca'])} {esc(v['modelo'])} {esc(v['anio'])}</strong> "
            f"(placas {esc(v['placas'])}).",
            f"Recomendamos un servicio de mantenimiento preventivo cada {MESES_CICLO} meses para revisar "
            "afinación, frenos, niveles y suspensión, y así evitar reparaciones mayores.",
            "Responde a este correo o llámanos al <strong>(81) 8345 6600</strong> para agendar tu cita.",
        ],
        tabla=[
            ("Última visita", _fecha_larga(v["ultima_visita"])),
            ("Último kilometraje registrado", f"{v['ultimo_km']:,} km" if v["ultimo_km"] else "—"),
            ("Servicio sugerido", "Mantenimiento preventivo"),
        ],
        nota="Recibes este correo porque autorizaste recibir avisos de VMotors.",
    )
    r = correo.enviar(
        tipo="recordatorio", referencia=str(id_vehiculo), destinatario=_destino(destinatario, v["correo"]),
        asunto=f"Recordatorio de mantenimiento · {v['marca']} {v['modelo']} ({v['placas']})",
        cuerpo_html=cuerpo,
    )
    return {"id_vehiculo": id_vehiculo, "placas": v["placas"], **r.como_dict(),
            "motivo": r.error}


def proximo_mantenimiento(ultima_entrega: str | None) -> str | None:
    if not ultima_entrega:
        return None
    d = date.fromisoformat(ultima_entrega[:10]) + timedelta(days=round(MESES_CICLO * 30.44))
    return d.isoformat()
