from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional

from models import VentaCreate, VentaResponse, VentaDetalleCompleto
from services.venta_service import crear_venta, listar_ventas, get_detalles_venta, resumen_stats

router = APIRouter(prefix="/ventas", tags=["Ventas"])


@router.post("", response_model=VentaDetalleCompleto, status_code=201)
def crear(data: VentaCreate):
    """
    **CU01 – Registrar Venta**

    Crea una venta completa de forma atómica:
    - Valida stock disponible por item
    - Registra precio histórico en el momento de la venta
    - Descuenta stock de `stock_sucursal`
    - Si `tipo_pago == 'Cuenta Corriente'`, actualiza el saldo del cliente
    - Genera alertas automáticas si el stock cae por debajo del mínimo
    """
    try:
        return crear_venta(data)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.get("", response_model=List[VentaResponse])
def listar(
    fecha_desde: Optional[str] = Query(None, description="ISO date, ej: 2026-01-01"),
    fecha_hasta: Optional[str] = Query(None, description="ISO date, ej: 2026-12-31"),
    id_sucursal: Optional[int] = Query(None),
    id_usuario: Optional[int] = Query(None),
    id_cliente: Optional[int] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=500),
):
    """
    Lista ventas con filtros opcionales por fecha, sucursal, usuario y cliente.
    """
    return listar_ventas(
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
        id_sucursal=id_sucursal,
        id_usuario=id_usuario,
        id_cliente=id_cliente,
        page=page,
        limit=limit,
    )


@router.get("/stats/resumen")
def stats(id_sucursal: Optional[int] = Query(None)):
    """
    **Analytics seed** — returns aggregate totals:
    total_ventas, ingresos_totales, ingresos_hoy, ingresos_mes, top_5_productos.
    """
    return resumen_stats(id_sucursal=id_sucursal)


@router.get("/{id_venta}", response_model=VentaDetalleCompleto)
def detalle(id_venta: int):
    """Retorna una venta con el desglose completo de items."""
    try:
        return get_detalles_venta(id_venta)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{id_venta}/detalles", response_model=VentaDetalleCompleto)
def detalles_alias(id_venta: int):
    """Alias explícito para GET /ventas/{id}/detalles."""
    return detalle(id_venta)
