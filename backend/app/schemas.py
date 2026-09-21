"""Modelos de entrada con las mismas reglas de negocio que ya vivian como
CHECK constraints en el esquema de PostgreSQL (ver database/seed_database.py):
telefono de 10 a 15 digitos, RFC con el patron oficial, CP de 5 digitos,
placas en mayusculas, anio dentro de rango, etc. SQLite no aplica estas
reglas con regex, asi que quedan aqui, en la capa que recibe la escritura.
"""

from __future__ import annotations

import re
from datetime import date, datetime

from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator

TELEFONO_RE = re.compile(r"^[0-9]{10,15}$")
RFC_RE = re.compile(r"^[A-ZÑ&]{3,4}[0-9]{6}[A-Z0-9]{3}$")
CP_RE = re.compile(r"^[0-9]{5}$")
PLACAS_RE = re.compile(r"^[A-Z0-9-]{5,10}$")
HORA_RE = re.compile(r"^([01][0-9]|2[0-3]):[0-5][0-9]$")

TRANSMISIONES = {"Manual", "Automático"}
FORMAS_PAGO = {"Efectivo", "Tarjeta", "Transferencia", "Cheque"}
ETAPAS = ["Pendiente", "Recibido", "En diagnóstico", "En reparación", "Terminado", "Entregado"]


class ClienteIn(BaseModel):
    nombre: str = Field(min_length=2, max_length=60)
    apellido: str = Field(min_length=2, max_length=60)
    razon_social: str | None = Field(default=None, max_length=120)
    rfc: str | None = None
    telefono: str
    telefono_oficina: str | None = None
    correo: EmailStr | None = None
    acepta_promociones: bool = False
    calle: str | None = Field(default=None, max_length=120)
    numero: str | None = Field(default=None, max_length=10)
    colonia: str | None = Field(default=None, max_length=100)
    municipio: str | None = Field(default=None, max_length=100)
    estado: str | None = Field(default=None, max_length=60)
    codigo_postal: str | None = None

    @field_validator("nombre", "apellido")
    @classmethod
    def _sin_espacios_vacios(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 2:
            raise ValueError("Debe tener al menos 2 caracteres.")
        return v

    @field_validator("telefono", "telefono_oficina")
    @classmethod
    def _telefono_valido(cls, v: str | None) -> str | None:
        if v is None or v == "":
            return None
        if not TELEFONO_RE.match(v):
            raise ValueError("El teléfono debe tener entre 10 y 15 dígitos numéricos.")
        return v

    @field_validator("rfc")
    @classmethod
    def _rfc_valido(cls, v: str | None) -> str | None:
        if v is None or v == "":
            return None
        v = v.strip().upper()
        if not RFC_RE.match(v):
            raise ValueError("El RFC no tiene un formato válido (ej. CARF900101AB1).")
        return v

    @field_validator("codigo_postal")
    @classmethod
    def _cp_valido(cls, v: str | None) -> str | None:
        if v is None or v == "":
            return None
        if not CP_RE.match(v):
            raise ValueError("El código postal debe tener 5 dígitos.")
        return v


class VehiculoIn(BaseModel):
    placas: str
    marca: str = Field(min_length=1, max_length=50)
    modelo: str = Field(min_length=1, max_length=50)
    anio: int
    color: str | None = Field(default=None, max_length=30)
    transmision: str = "Manual"
    motor: str | None = Field(default=None, max_length=40)

    @field_validator("placas")
    @classmethod
    def _placas_validas(cls, v: str) -> str:
        v = v.strip().upper()
        if not PLACAS_RE.match(v):
            raise ValueError("La placa debe tener de 5 a 10 caracteres (letras, números y guiones).")
        return v

    @field_validator("anio")
    @classmethod
    def _anio_valido(cls, v: int) -> int:
        limite = date.today().year + 1
        if not (1980 <= v <= limite):
            raise ValueError(f"El año debe estar entre 1980 y {limite}.")
        return v

    @field_validator("transmision")
    @classmethod
    def _transmision_valida(cls, v: str) -> str:
        if v not in TRANSMISIONES:
            raise ValueError(f"La transmisión debe ser una de: {', '.join(TRANSMISIONES)}.")
        return v


class VisitaIn(BaseModel):
    fecha: date
    hora_inicio: str
    hora_fin: str
    hora_entrada: str
    hora_prometida: str
    kilometraje: int = Field(ge=0)
    nivel_combustible: int | None = Field(default=None, ge=0, le=8)
    motivo_ingreso: str = Field(min_length=1)
    forma_pago: str | None = None

    @field_validator("hora_inicio", "hora_fin", "hora_entrada", "hora_prometida")
    @classmethod
    def _hora_valida(cls, v: str) -> str:
        if not HORA_RE.match(v):
            raise ValueError("La hora debe tener formato HH:MM (08:00 a 23:59).")
        return v

    @field_validator("motivo_ingreso")
    @classmethod
    def _motivo_no_vacio(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("El motivo de ingreso no puede quedar vacío.")
        return v

    @field_validator("forma_pago")
    @classmethod
    def _forma_pago_valida(cls, v: str | None) -> str | None:
        if v is None or v == "":
            return None
        if v not in FORMAS_PAGO:
            raise ValueError(f"La forma de pago debe ser una de: {', '.join(FORMAS_PAGO)}.")
        return v

    @model_validator(mode="after")
    def _horario_coherente(self):
        if self.hora_fin <= self.hora_inicio:
            raise ValueError("La hora de fin del bloque debe ser posterior a la hora de inicio.")
        if not ("08:00" <= self.hora_inicio and self.hora_fin <= "19:00"):
            raise ValueError("El bloque debe caer dentro del horario del taller (08:00 a 19:00).")
        return self


class RecepcionIn(BaseModel):
    cliente: ClienteIn
    vehiculo: VehiculoIn
    visita: VisitaIn


class CitaIn(BaseModel):
    id_vehiculo: int
    fecha: date
    hora_inicio: str
    motivo_ingreso: str = Field(min_length=1)

    @field_validator("hora_inicio")
    @classmethod
    def _hora_valida(cls, v: str) -> str:
        if not HORA_RE.match(v):
            raise ValueError("La hora debe tener formato HH:MM.")
        if not ("08:00" <= v <= "17:00"):
            raise ValueError("El bloque debe caer entre las 08:00 y las 17:00.")
        return v

    @field_validator("motivo_ingreso")
    @classmethod
    def _motivo_no_vacio(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("El motivo de ingreso no puede quedar vacío.")
        return v

    @field_validator("fecha")
    @classmethod
    def _fecha_no_pasada(cls, v: date) -> date:
        if v < date.today():
            raise ValueError("No se admiten fechas anteriores al día de hoy.")
        return v


class OrdenPatchIn(BaseModel):
    diagnostico: str | None = None
    costo_mano_obra: float | None = Field(default=None, ge=0)
    estatus: str | None = None

    @field_validator("estatus")
    @classmethod
    def _estatus_valido(cls, v: str | None) -> str | None:
        if v is None:
            return None
        if v not in ETAPAS:
            raise ValueError(f"Estatus inválido: {v}.")
        return v


class RefaccionOrdenIn(BaseModel):
    id_refaccion: int
    cantidad: int = Field(gt=0, le=999)
