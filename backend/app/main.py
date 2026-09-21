"""VMotors · backend

Une la API (SQLite) con el prototipo estatico de `frontend/`: un solo
proceso, un solo puerto. Esto simplifica exponer el sistema completo a
traves de un tunel (cloudflared) para que el equipo lo revise sin que cada
quien tenga que levantar su propio backend.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

from .routers import alertas, auth, catalogos, dashboard, ordenes, recepcion  # noqa: E402

FRONTEND_DIR = Path(__file__).resolve().parent.parent.parent / "frontend"

DEFAULT_SECRET = "cambia-esta-clave-antes-de-compartir-el-tunel"
SECRET_KEY = os.getenv("SECRET_KEY", DEFAULT_SECRET)
if SECRET_KEY == DEFAULT_SECRET:
    logging.warning(
        "SECRET_KEY sigue en su valor por omisión. Antes de compartir el túnel de "
        "cloudflared, defina una clave propia en backend/.env (ver .env.example)."
    )

app = FastAPI(title="VMotors API")

# same_site="lax" es la defensa principal contra CSRF aqui: un sitio externo
# no puede lograr que el navegador reenvie esta cookie en un POST/PATCH/DELETE
# de otro origen. No hay CORS habilitado, asi que tampoco un fetch cruzado
# desde otro dominio puede leer la sesion.
app.add_middleware(
    SessionMiddleware,
    secret_key=SECRET_KEY,
    session_cookie="vmotors_session",
    same_site="lax",
    max_age=60 * 60 * 12,  # 12 horas
)

app.include_router(auth.router)
app.include_router(catalogos.router)
app.include_router(ordenes.router)
app.include_router(recepcion.router)
app.include_router(alertas.router)
app.include_router(dashboard.router)

# El prototipo estatico se sirve desde el mismo proceso: las rutas /api/*
# de arriba se resuelven primero, y cualquier otra ruta cae en los archivos
# de frontend/ (html, css, js).
if FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")
