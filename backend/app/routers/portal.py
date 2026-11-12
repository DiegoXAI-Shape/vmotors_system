"""Portal del cliente: segundo rol del sistema.

El cliente entra con las placas de cualquiera de sus vehiculos y el telefono
que dejo registrado en recepcion (no necesita crear cuenta ni recordar una
contrasena). Su sesion es de solo lectura y queda limitada a SUS propios
vehiculos: no puede llamar a ningun endpoint del administrador, porque esos
exigen `session["auth"]`, que este login nunca establece.
"""

from __future__ import annotations

import re

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import Response
from pydantic import BaseModel, Field

from ..auth import limpiar_intentos, registrar_intento_fallido, verificar_limite_intentos
from ..database import query_all, query_one
from ..notificaciones import datos_orden, pdf_comprobante, proximo_mantenimiento
from ..schemas import ETAPAS

router = APIRouter(prefix="/api/portal", tags=["portal del cliente"])


class AccesoCliente(BaseModel):
    placas: str = Field(min_length=3, max_length=15)
    telefono: str = Field(min_length=7, max_length=20)


def _solo_digitos(t: str) -> str:
    return re.sub(r"\D", "", t or "")


def _placas_normalizadas(p: str) -> str:
    return re.sub(r"[^A-Z0-9]", "", (p or "").upper())


def require_cliente(request: Request) -> int:
    id_cliente = request.session.get("id_cliente")
    if request.session.get("rol") != "cliente" or not id_cliente:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Sesión de cliente no iniciada.")
    return int(id_cliente)


@router.post("/login")
def login_cliente(datos: AccesoCliente, request: Request):
    verificar_limite_intentos(request)
    fila = query_one(
        """SELECT cl.id_cliente, cl.nombre, cl.telefono, cl.telefono_oficina
             FROM vehiculos v JOIN clientes cl ON cl.id_cliente = v.id_cliente
            WHERE REPLACE(REPLACE(UPPER(v.placas), '-', ''), ' ', '') = ?""",
        (_placas_normalizadas(datos.placas),),
    )
    tel = _solo_digitos(datos.telefono)[-10:]
    telefonos = {_solo_digitos(fila[k])[-10:] for k in ("telefono", "telefono_oficina") if fila and fila[k]} if fila else set()
    if not fila or len(tel) < 7 or tel not in telefonos:
        registrar_intento_fallido(request)
        return {"ok": False, "error": "No encontramos un vehículo con esas placas y ese teléfono."}
    limpiar_intentos(request)
    request.session.clear()  # nunca mezclar una sesion de cliente con la del administrador
    request.session["rol"] = "cliente"
    request.session["id_cliente"] = fila["id_cliente"]
    return {"ok": True, "nombre": fila["nombre"]}


@router.post("/logout")
def logout_cliente(request: Request):
    request.session.clear()
    return {"ok": True}


@router.get("/mis-vehiculos")
def mis_vehiculos(id_cliente: int = Depends(require_cliente)):
    cliente = query_one(
        "SELECT id_cliente, nombre, apellido, correo, telefono FROM clientes WHERE id_cliente = ?",
        (id_cliente,),
    )
    if not cliente:
        raise HTTPException(401, "Sesión de cliente no válida.")

    vehiculos = query_all(
        """SELECT id_vehiculo, placas, marca, modelo, anio, color, transmision
             FROM vehiculos WHERE id_cliente = ? ORDER BY id_vehiculo""",
        (id_cliente,),
    )
    for v in vehiculos:
        ordenes = query_all(
            """SELECT o.id_orden, o.folio, o.fecha_ingreso, o.hora_prometida, o.fecha_entrega,
                      o.kilometraje, o.diagnostico, o.estatus, o.costo_total, c.motivo_ingreso
                 FROM ordenes_servicio o JOIN citas c ON c.id_cita = o.id_cita
                WHERE c.id_vehiculo = ?
                ORDER BY o.fecha_ingreso DESC""",
            (v["id_vehiculo"],),
        )
        activa = next((o for o in ordenes if o["estatus"] != "Entregado"), None)
        if activa:
            activa["etapa"] = ETAPAS.index(activa["estatus"])
            activa["historial"] = query_all(
                """SELECT estatus_nuevo AS estatus, fecha_cambio AS fecha
                     FROM historial_estatus WHERE id_orden = ? ORDER BY fecha_cambio, id_historial""",
                (activa["id_orden"],),
            )
        entregadas = [o for o in ordenes if o["estatus"] == "Entregado"]
        ultima = max((o["fecha_entrega"] for o in entregadas if o["fecha_entrega"]), default=None)
        v["orden_activa"] = activa
        v["historial"] = entregadas[:10]
        v["total_visitas"] = len(entregadas)
        v["ultima_visita"] = ultima
        v["proximo_mantenimiento"] = proximo_mantenimiento(ultima)
        v["proximas_citas"] = query_all(
            """SELECT fecha, hora_inicio, motivo_ingreso FROM citas
                WHERE id_vehiculo = ? AND estatus_cita = 'Agendada' AND fecha >= date('now', 'localtime')
                ORDER BY fecha, hora_inicio""",
            (v["id_vehiculo"],),
        )
    return {"cliente": cliente, "etapas": ETAPAS, "vehiculos": vehiculos}


@router.get("/ordenes/{id_orden}/comprobante.pdf")
def comprobante_cliente(id_orden: int, id_cliente: int = Depends(require_cliente)):
    o = datos_orden(id_orden)
    if o["id_cliente"] != id_cliente:
        # 404 y no 403: no confirmar que existe una orden ajena con ese id
        raise HTTPException(404, "La orden indicada no existe.")
    return Response(
        content=pdf_comprobante(o), media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="comprobante-{o["folio"]}.pdf"'},
    )
