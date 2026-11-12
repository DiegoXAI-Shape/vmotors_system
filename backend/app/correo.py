"""Envio de correos del taller: comprobantes, recordatorios de mantenimiento,
avisos de seguimiento y el resumen mensual para el dueno.

Funciona en dos modos, segun la configuracion de `backend/.env`:

* **SMTP real**: si `SMTP_HOST` esta definido, el correo sale de verdad por
  ese servidor (por ejemplo Gmail con una contrasena de aplicacion).
* **Simulado**: si no hay SMTP configurado, el correo NO sale a internet,
  pero se guarda completo en la bandeja de salida (tabla `correos_enviados`)
  y puede revisarse desde la pantalla "Bandeja de correos". Asi el sistema
  se puede demostrar sin credenciales y sin mandar correos a los clientes
  ficticios de la base de datos.

En ambos casos cada envio queda registrado en `correos_enviados`, lo que
ademas sirve para no repetir un recordatorio al mismo cliente cada vez que
se presiona el boton.
"""

from __future__ import annotations

import html
import logging
import os
import smtplib
import ssl
from dataclasses import dataclass, field
from datetime import datetime
from email.message import EmailMessage

from .database import get_connection

log = logging.getLogger("vmotors.correo")

DDL_CORREOS = """
CREATE TABLE IF NOT EXISTS correos_enviados (
    id_correo     INTEGER  PRIMARY KEY AUTOINCREMENT,
    fecha         TEXT     NOT NULL DEFAULT (datetime('now', 'localtime')),
    tipo          TEXT     NOT NULL,
    referencia    TEXT,
    destinatario  TEXT     NOT NULL,
    asunto        TEXT     NOT NULL,
    cuerpo_html   TEXT     NOT NULL,
    adjunto       TEXT,
    modo          TEXT     NOT NULL,
    estado        TEXT     NOT NULL,
    error         TEXT,

    CHECK (tipo IN ('comprobante', 'recordatorio', 'seguimiento', 'reporte_mensual', 'prueba')),
    CHECK (modo IN ('smtp', 'simulado')),
    CHECK (estado IN ('enviado', 'fallido'))
);
CREATE INDEX IF NOT EXISTS ix_correos_tipo_ref ON correos_enviados (tipo, referencia, fecha);
"""


def asegurar_tabla() -> None:
    con = get_connection()
    try:
        con.executescript(DDL_CORREOS)
        con.commit()
    finally:
        con.close()


@dataclass
class Adjunto:
    nombre: str
    contenido: bytes
    tipo_mime: str = "application/pdf"


@dataclass
class ResultadoEnvio:
    ok: bool
    modo: str
    destinatario: str
    id_correo: int | None = None
    error: str | None = None
    extra: dict = field(default_factory=dict)

    def como_dict(self) -> dict:
        return {"ok": self.ok, "modo": self.modo, "destinatario": self.destinatario,
                "id_correo": self.id_correo, "error": self.error}


def smtp_configurado() -> bool:
    return bool(os.getenv("SMTP_HOST", "").strip())


def correo_dueno() -> str | None:
    return (os.getenv("CORREO_DUENO") or "").strip() or None


def _remitente() -> str:
    return os.getenv("SMTP_FROM") or os.getenv("SMTP_USER") or "VMotors <no-responder@vmotors.mx>"


def _enviar_smtp(destinatario: str, asunto: str, cuerpo_html: str, texto: str,
                 adjuntos: list[Adjunto]) -> None:
    msg = EmailMessage()
    msg["From"] = _remitente()
    msg["To"] = destinatario
    msg["Subject"] = asunto
    msg.set_content(texto)
    msg.add_alternative(cuerpo_html, subtype="html")
    for a in adjuntos:
        principal, secundario = a.tipo_mime.split("/", 1)
        msg.add_attachment(a.contenido, maintype=principal, subtype=secundario, filename=a.nombre)

    host = os.getenv("SMTP_HOST")
    puerto = int(os.getenv("SMTP_PORT", "587"))
    usuario = os.getenv("SMTP_USER")
    contrasena = os.getenv("SMTP_PASSWORD")
    contexto = ssl.create_default_context()
    if puerto == 465:
        with smtplib.SMTP_SSL(host, puerto, context=contexto, timeout=20) as s:
            if usuario:
                s.login(usuario, contrasena or "")
            s.send_message(msg)
    else:
        with smtplib.SMTP(host, puerto, timeout=20) as s:
            s.starttls(context=contexto)
            if usuario:
                s.login(usuario, contrasena or "")
            s.send_message(msg)


def enviar(*, tipo: str, destinatario: str, asunto: str, cuerpo_html: str,
           referencia: str | None = None, adjuntos: list[Adjunto] | None = None) -> ResultadoEnvio:
    """Envia (o simula) un correo y lo registra en la bandeja de salida."""
    adjuntos = adjuntos or []
    asegurar_tabla()
    modo = "smtp" if smtp_configurado() else "simulado"
    error = None
    if modo == "smtp":
        try:
            _enviar_smtp(destinatario, asunto, cuerpo_html, _a_texto(cuerpo_html), adjuntos)
        except Exception as exc:  # noqa: BLE001 - se reporta al usuario tal cual
            log.warning("No se pudo enviar el correo a %s: %s", destinatario, exc)
            error = f"{type(exc).__name__}: {exc}"

    con = get_connection()
    try:
        cur = con.execute(
            """INSERT INTO correos_enviados
                   (tipo, referencia, destinatario, asunto, cuerpo_html, adjunto, modo, estado, error)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (tipo, referencia, destinatario, asunto, cuerpo_html,
             ", ".join(a.nombre for a in adjuntos) or None, modo,
             "fallido" if error else "enviado", error),
        )
        con.commit()
        id_correo = cur.lastrowid
    finally:
        con.close()
    return ResultadoEnvio(ok=error is None, modo=modo, destinatario=destinatario,
                          id_correo=id_correo, error=error)


def enviado_recientemente(tipo: str, referencia: str, dias: int) -> bool:
    asegurar_tabla()
    con = get_connection()
    try:
        fila = con.execute(
            """SELECT 1 FROM correos_enviados
                WHERE tipo = ? AND referencia = ? AND estado = 'enviado'
                  AND fecha >= datetime('now', 'localtime', ?)
                LIMIT 1""",
            (tipo, referencia, f"-{int(dias)} days"),
        ).fetchone()
        return fila is not None
    finally:
        con.close()


# ---------------------------------------------------------------------------
# Plantilla HTML comun
# ---------------------------------------------------------------------------

def _a_texto(cuerpo_html: str) -> str:
    """Version en texto plano (para clientes de correo sin HTML)."""
    import re
    texto = re.sub(r"<br\s*/?>|</p>|</div>|</tr>|</h\d>", "\n", cuerpo_html)
    texto = re.sub(r"<[^>]+>", "", texto)
    texto = html.unescape(texto)
    return re.sub(r"\n\s*\n+", "\n\n", texto).strip()


def esc(valor) -> str:
    return html.escape(str(valor if valor is not None else ""))


def plantilla(titulo: str, saludo: str, parrafos: list[str], tabla: list[tuple[str, str]] | None = None,
              nota: str | None = None) -> str:
    """Correo con la identidad visual del sistema. `parrafos` y `nota` ya
    deben venir escapados (pueden traer <strong>)."""
    filas = ""
    if tabla:
        filas = "".join(
            f'<tr><td style="padding:7px 0;color:#667085;font-size:13px;width:42%">{esc(k)}</td>'
            f'<td style="padding:7px 0;color:#101828;font-size:13px;font-weight:600">{esc(v)}</td></tr>'
            for k, v in tabla
        )
        filas = (f'<table role="presentation" style="width:100%;border-collapse:collapse;'
                 f'border-top:1px solid #E4E7EC;border-bottom:1px solid #E4E7EC;margin:18px 0">{filas}</table>')
    cuerpo = "".join(f'<p style="margin:0 0 12px;font-size:14px;line-height:1.6;color:#344054">{p}</p>'
                     for p in parrafos)
    pie_nota = (f'<p style="margin:16px 0 0;font-size:12px;line-height:1.6;color:#667085">{nota}</p>'
                if nota else "")
    return f"""<!DOCTYPE html>
<html lang="es"><body style="margin:0;background:#F2F4F7;font-family:Segoe UI,Helvetica,Arial,sans-serif">
<table role="presentation" style="width:100%;border-collapse:collapse"><tr><td style="padding:28px 12px">
<table role="presentation" style="max-width:560px;margin:0 auto;background:#ffffff;border-radius:12px;
       border:1px solid #E4E7EC;border-collapse:separate;overflow:hidden">
  <tr><td style="background:#101828;padding:18px 26px">
    <span style="display:inline-block;background:#D9531E;color:#fff;font-weight:700;font-size:13px;
                 border-radius:7px;padding:6px 8px;letter-spacing:.5px">VM</span>
    <span style="color:#fff;font-weight:700;letter-spacing:1.4px;font-size:15px;margin-left:10px">VMOTORS</span>
  </td></tr>
  <tr><td style="padding:26px">
    <h1 style="margin:0 0 14px;font-size:19px;color:#101828">{esc(titulo)}</h1>
    <p style="margin:0 0 12px;font-size:14px;color:#344054">{esc(saludo)}</p>
    {cuerpo}{filas}{pie_nota}
  </td></tr>
  <tr><td style="padding:16px 26px;background:#FAFBFC;border-top:1px solid #E4E7EC;font-size:11.5px;
                 color:#8A91A0;line-height:1.6">
    VMotors · Taller automotriz · Av. Miguel Alemán 1450, San Nicolás de los Garza, N. L.<br>
    Tel. (81) 8345 6600 · contacto@vmotors.mx · Correo enviado el {datetime.now():%d/%m/%Y %H:%M}
  </td></tr>
</table></td></tr></table></body></html>"""
