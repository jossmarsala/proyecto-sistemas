from __future__ import annotations
from pydantic import BaseModel, Field
from typing import Optional

class ClienteCreate(BaseModel):
    nombre: str = Field(..., max_length=50)
    apellido: Optional[str] = Field(None, max_length=50)
    cuit_dni: Optional[str] = None
    razon_social: Optional[str] = Field(None, max_length=50)
    telefono: Optional[str] = Field(None, min_length=8, max_length=13)
    notas: Optional[str] = None
    limite_credito: float = Field(0.0, ge=0)


class ClienteResponse(BaseModel):
    id_cliente: int
    nombre: str
    apellido: Optional[str]
    cuit_dni: Optional[str]
    razon_social: Optional[str]
    telefono: Optional[str]
    notas: Optional[str]
    saldo_cuenta_corriente: float
    limite_credito: float
    creado_en: str

    model_config = {"from_attributes": True}


class MovimientoCCResponse(BaseModel):
    id_movimiento: int
    id_cliente: int
    id_venta: Optional[int]
    tipo: str        # 'cargo' | 'pago'
    monto: float
    saldo_resultante: float
    notas: Optional[str]
    fecha_hora: str

    model_config = {"from_attributes": True}

class PagoCC(BaseModel):
    monto: float
    notas: Optional[str] = None
