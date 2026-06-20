from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional

from models import ProductoCreate, ProductoResponse, ProductoConStock, PrecioUpdate
from services.producto_service import (
    crear_producto, listar_productos, get_producto,
    actualizar_precio, prediccion_quiebre
)

router = APIRouter(prefix="/productos", tags=["Productos"])


@router.post("", response_model=ProductoResponse, status_code=201)
def crear(data: ProductoCreate):
    """**CU03** – Crea un producto y su registro inicial de stock."""
    try:
        return crear_producto(data)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.get("", response_model=List[ProductoConStock])
def listar(
    id_sucursal: int = Query(1, ge=1),
    categoria: Optional[str] = Query(None),
    solo_activos: bool = Query(True),
    page: int = Query(1, ge=1),
    limit: int = Query(100, ge=1, le=500),
):
    """Lista productos con su stock actual por sucursal."""
    return listar_productos(
        id_sucursal=id_sucursal,
        categoria=categoria,
        solo_activos=solo_activos,
        page=page,
        limit=limit,
    )


@router.get("/prediccion-quiebre")
def quiebre(
    id_sucursal: int = Query(1, ge=1),
    ventana_dias: int = Query(30, ge=7, le=90),
):
    """
    **CU07 – Proyectar Quiebre de Stock**

    Aplica la fórmula: `Dias_Restantes = Stock_Actual / Promedio_Ventas_Diarias`
    usando los últimos `ventana_dias` días para la tendencia.
    Devuelve flag `alerta_quiebre` si los días restantes < tiempo de reposición del proveedor.
    """
    return prediccion_quiebre(id_sucursal=id_sucursal, ventana_dias=ventana_dias)


@router.get("/{id_producto}", response_model=ProductoResponse)
def get_one(id_producto: int):
    try:
        return get_producto(id_producto)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.put("/{id_producto}/precio", response_model=ProductoResponse)
def precio(id_producto: int, data: PrecioUpdate):
    """
    **CU05 – Actualizar Precios** (Supervisor).
    Actualiza precio_costo y/o precio_venta, y registra la fecha de modificación.
    """
    try:
        return actualizar_precio(id_producto, data)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
