"""Envios por correo desde el panel del administrador y bandeja de salida."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel, EmailStr, Field

from .. import correo
from ..auth import require_auth
from ..database import query_all, query_one
from ..notificaciones import datos_orden, enviar_comprobante, enviar_recordatorio, pdf_comprobante
from ..reporte_mensual import enviar_reporte_mensual

router = APIRouter(prefix="/api", tags=["correos"], dependencies=[Depends(require_auth)])


class EnvioIn(BaseModel):
    destinatario: EmailStr | None = None


class RecordatoriosIn(BaseModel):
    # Si no se indica, se envia a todas las unidades del motor de alertas.
    ids_vehiculo: list[int] | None = Field(default=None, max_length=500)
    destinatario: EmailStr | None = None   # util para probar: manda todo a un correo propio
    forzar: bool = False                   # ignora el limite de un recordatorio cada 30 dias


@router.get("/correos/estado")
def estado_correo():
    return {
        "modo": "smtp" if correo.smtp_configurado() else "simulado",
        "correo_dueno": correo.correo_dueno(),
    }


@router.get("/correos")
def bandeja_de_salida(limite: int = 200):
    correo.asegurar_tabla()
    return query_all(
        """SELECT id_correo, fecha, tipo, referencia, destinatario, asunto, adjunto, modo, estado, error
             FROM correos_enviados ORDER BY id_correo DESC LIMIT ?""",
        (max(1, min(limite, 1000)),),
    )


@router.get("/correos/{id_correo}")
def ver_correo(id_correo: int):
    correo.asegurar_tabla()
    c = query_one("SELECT * FROM correos_enviados WHERE id_correo = ?", (id_correo,))
    if not c:
        raise HTTPException(404, "El correo indicado no existe.")
    return c


@router.get("/ordenes/{id_orden}/comprobante.pdf")
def descargar_comprobante(id_orden: int):
    o = datos_orden(id_orden)
    return Response(
        content=pdf_comprobante(o), media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="comprobante-{o["folio"]}.pdf"'},
    )


@router.post("/ordenes/{id_orden}/comprobante/enviar")
def enviar_comprobante_orden(id_orden: int, datos: EnvioIn):
    return enviar_comprobante(id_orden, datos.destinatario).como_dict()


@router.post("/alertas/recordatorios")
def enviar_recordatorios(datos: RecordatoriosIn):
    from .alertas import listar_alertas

    ids = datos.ids_vehiculo if datos.ids_vehiculo is not None else [a["id_vehiculo"] for a in listar_alertas()]
    resultados = [enviar_recordatorio(i, datos.destinatario, datos.forzar) for i in ids]
    return {
        "enviados": sum(1 for r in resultados if r["ok"]),
        "omitidos": sum(1 for r in resultados if not r["ok"]),
        "modo": "smtp" if correo.smtp_configurado() else "simulado",
        "resultados": resultados,
    }


@router.post("/reportes/mensual/enviar")
def enviar_reporte_al_dueno(datos: EnvioIn):
    return enviar_reporte_mensual(datos.destinatario).como_dict()
