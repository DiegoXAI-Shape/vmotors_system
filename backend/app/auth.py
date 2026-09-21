"""Autenticacion minima: un solo usuario administrador, sesion por cookie firmada.

No hay tabla de usuarios ni roles: el taller opera con un unico nivel de
acceso (ver README). Las credenciales viven en variables de entorno para no
quedar escritas en el codigo.
"""

from __future__ import annotations

import os
import time

from fastapi import HTTPException, Request, status

ADMIN_USER = os.getenv("ADMIN_USER", "administrador")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "vmotors2026")

MAX_INTENTOS = 5
VENTANA_SEGUNDOS = 15 * 60

# Limitador en memoria: alcanza para un solo proceso / un solo administrador.
# Si el backend llegara a correr con varios workers habria que moverlo a la
# base de datos o a un cache compartido.
_intentos_fallidos: dict[str, list[float]] = {}


def _ip_cliente(request: Request) -> str:
    return request.client.host if request.client else "desconocido"


def verificar_limite_intentos(request: Request) -> None:
    ip = _ip_cliente(request)
    ahora = time.time()
    intentos = [t for t in _intentos_fallidos.get(ip, []) if ahora - t < VENTANA_SEGUNDOS]
    _intentos_fallidos[ip] = intentos
    if len(intentos) >= MAX_INTENTOS:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Demasiados intentos fallidos. Intente de nuevo en unos minutos.",
        )


def registrar_intento_fallido(request: Request) -> None:
    ip = _ip_cliente(request)
    _intentos_fallidos.setdefault(ip, []).append(time.time())


def limpiar_intentos(request: Request) -> None:
    _intentos_fallidos.pop(_ip_cliente(request), None)


def validar_credenciales(usuario: str, contrasena: str) -> bool:
    return usuario == ADMIN_USER and contrasena == ADMIN_PASSWORD


def require_auth(request: Request) -> None:
    if not request.session.get("auth"):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Sesión no iniciada.")
