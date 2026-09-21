from __future__ import annotations

from fastapi import APIRouter, Request
from pydantic import BaseModel

from ..auth import (
    limpiar_intentos,
    registrar_intento_fallido,
    validar_credenciales,
    verificar_limite_intentos,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])


class Credenciales(BaseModel):
    usuario: str
    contrasena: str


@router.post("/login")
def login(datos: Credenciales, request: Request):
    verificar_limite_intentos(request)
    if not validar_credenciales(datos.usuario, datos.contrasena):
        registrar_intento_fallido(request)
        return {"ok": False, "error": "Usuario o contraseña incorrectos."}
    limpiar_intentos(request)
    request.session["auth"] = True
    request.session["usuario"] = datos.usuario
    return {"ok": True}


@router.post("/logout")
def logout(request: Request):
    request.session.clear()
    return {"ok": True}


@router.get("/me")
def me(request: Request):
    return {
        "autenticado": bool(request.session.get("auth")),
        "usuario": request.session.get("usuario"),
    }
