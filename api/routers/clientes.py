from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional

from models import ClienteCreate, ClienteResponse, MovimientoCCResponse
from services.cliente_service import (
    crear_cliente, listar_clientes, get_cliente,
    get_cuenta_corriente, registrar_pago_cc
)

router = APIRouter(prefix="/clientes", tags=["Clientes"])


class PagoCC(BaseModel):
    monto: float
    notas: Optional[str] = None


@router.post("", response_model=ClienteResponse, status_code=201)
def crear(data: ClienteCreate):
    """Registra un nuevo cliente."""
    try:
        return crear_cliente(data)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.get("", response_model=List[ClienteResponse])
def listar(
    nombre: Optional[str] = Query(None, description="Filtro por nombre/apellido/razón social"),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
):
    """Lista clientes con búsqueda opcional por nombre."""
    return listar_clientes(nombre=nombre, page=page, limit=limit)


@router.get("/{id_cliente}", response_model=ClienteResponse)
def get_one(id_cliente: int):
    try:
        return get_cliente(id_cliente)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{id_cliente}/cuenta-corriente", response_model=List[MovimientoCCResponse])
def cuenta_corriente(
    id_cliente: int,
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
):
    """**CU04** – Consulta el libro mayor de cuenta corriente del cliente."""
    try:
        return get_cuenta_corriente(id_cliente, page=page, limit=limit)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{id_cliente}/cuenta-corriente/pago", response_model=ClienteResponse)
def pago_cc(id_cliente: int, data: PagoCC):
    """**CU04** – Registra un pago sobre la cuenta corriente del cliente."""
    try:
        return registrar_pago_cc(id_cliente, data.monto, data.notas)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
