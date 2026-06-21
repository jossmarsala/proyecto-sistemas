from __future__ import annotations
from pydantic import BaseModel, Field
from typing import Optional


# ── Request ───────────────────────────────────────────────────────────────────

class ProductoCreate(BaseModel):
    sku: Optional[str] = None
    nombre: str = Field(..., min_length=1, max_length=100)
    categoria: Optional[str] = None
    precio_costo: float = Field(0.0, ge=0)
    precio_venta: float = Field(0.0, ge=0)
    id_proveedor: Optional[int] = None
    # initial stock for the default sucursal
    stock_inicial: float = Field(0.0, ge=0)
    stock_minimo_seguridad: float = Field(0.0, ge=0)
    id_sucursal: int = Field(1, ge=1)


class PrecioUpdate(BaseModel):
    precio_costo: Optional[float] = Field(None, ge=0)
    precio_venta: Optional[float] = Field(None, ge=0)


class ProductoUpdate(BaseModel):
    precio_costo: Optional[float] = Field(None, ge=0)
    precio_venta: Optional[float] = Field(None, ge=0)
    cantidad_actual: Optional[float] = Field(None, ge=0)
    id_sucursal: Optional[int] = Field(1, ge=1)


# ── Response ──────────────────────────────────────────────────────────────────

class ProductoResponse(BaseModel):
    id_producto: int
    sku: Optional[str]
    nombre: str
    categoria: Optional[str]
    precio_costo: float
    precio_venta: float
    id_proveedor: Optional[int]
    activo: int
    creado_en: str
    actualizado_en: str

    model_config = {"from_attributes": True}


class ProductoConStock(ProductoResponse):
    """Extended response that includes live stock for a given sucursal."""
    cantidad_actual: float
    stock_minimo_seguridad: float
    id_sucursal: int
