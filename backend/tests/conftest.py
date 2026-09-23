"""Fixtures compartidos: cada prueba corre contra su propia base de datos
SQLite temporal (nunca contra database/vmotors.db), con el mismo esquema y
catalogo de refacciones que usa el sistema real.
"""

from __future__ import annotations

import os
import sqlite3

import pytest
from fastapi.testclient import TestClient

from generador import REFACCIONES
from seed_sqlite import construir_ddl


@pytest.fixture()
def db_path(tmp_path, monkeypatch):
    path = tmp_path / "test_vmotors.db"
    monkeypatch.setenv("VMOTORS_DB_PATH", str(path))

    con = sqlite3.connect(path)
    con.executescript(construir_ddl())
    con.executemany(
        "INSERT INTO refacciones (id_refaccion, clave, descripcion, categoria, precio_unitario) "
        "VALUES (?, ?, ?, ?, ?)",
        [(i, *r) for i, r in enumerate(REFACCIONES, start=1)],
    )
    con.commit()
    con.close()
    return path


@pytest.fixture(autouse=True)
def _limpiar_limite_intentos():
    """El limitador de intentos de login vive en un diccionario a nivel de
    modulo (ver app/auth.py); si no se limpia entre pruebas, una prueba que
    provoca varios intentos fallidos deja bloqueadas a las siguientes."""
    from app.auth import _intentos_fallidos
    _intentos_fallidos.clear()
    yield
    _intentos_fallidos.clear()


@pytest.fixture()
def client(db_path):
    from app.main import app
    return TestClient(app)


@pytest.fixture()
def auth(client):
    """Cliente ya autenticado como el administrador (credenciales por
    omision definidas en app/auth.py)."""
    r = client.post("/api/auth/login", json={"usuario": "administrador", "contrasena": "vmotors2026"})
    assert r.status_code == 200 and r.json()["ok"] is True
    return client


@pytest.fixture()
def cliente_id(auth):
    r = auth.post("/api/clientes", json={
        "nombre": "Ana", "apellido": "Pérez", "telefono": "8112223344", "acepta_promociones": True,
    })
    assert r.status_code == 201
    return r.json()["id_cliente"]


@pytest.fixture()
def vehiculo_id(auth, cliente_id):
    r = auth.post(f"/api/vehiculos?id_cliente={cliente_id}", json={
        "placas": "ABC-123-D", "marca": "Nissan", "modelo": "Versa", "anio": 2022, "transmision": "Manual",
    })
    assert r.status_code == 201
    return r.json()["id_vehiculo"]
