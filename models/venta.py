from __future__ import annotations
from pydantic import BaseModel, Field
from typing import List, Optional


# ── Item inside a new sale ────────────────────────────────────────────────────

class ItemVenta(BaseModel):
    id_producto: int = Field(..., ge=1)
    cantidad: float = Field(..., gt=0)


# ── Request ───────────────────────────────────────────────────────────────────

class VentaCreate(BaseModel):
    id_cliente: Optional[int] = None       # optional: walk-in customer
    id_usuario: int = Field(1, ge=1)       # defaults to admin until auth is added
    id_sucursal: int = Field(1, ge=1)
    tipo_pago: str = Field("Efectivo")
    tipo_venta: str = Field("local")
    referencia: Optional[str] = None
    items: List[ItemVenta] = Field(..., min_length=1)


# ── Response ──────────────────────────────────────────────────────────────────

class DetalleVentaResponse(BaseModel):
    id_detalle: int
    id_venta: int
    id_producto: int
    nombre_producto: str
    cantidad: float
    precio_unitario_historico: float
    subtotal: float

    model_config = {"from_attributes": True}


class VentaResponse(BaseModel):
    id_venta: int
    id_cliente: Optional[int]
    id_usuario: int
    id_sucursal: int
    fecha_hora: str
    tipo_pago: str
    tipo_venta: str
    estado: str
    referencia: Optional[str]
    total: float

    model_config = {"from_attributes": True}


class VentaDetalleCompleto(VentaResponse):
    """Full sale response including line items."""
    items: List[DetalleVentaResponse] = []
