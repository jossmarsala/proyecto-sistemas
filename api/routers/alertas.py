from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional

from models import AlertaResponse
from services.alerta_service import listar_alertas, resolver_alerta

router = APIRouter(prefix="/alertas", tags=["Alertas"])


@router.get("", response_model=List[AlertaResponse])
def listar(
    tipo: Optional[str] = Query(None, description="'stock_minimo' o 'limite_credito'"),
    id_sucursal: Optional[int] = Query(None),
    solo_activas: bool = Query(True),
):
    """
    **CU06 – Consultar Alertas**

    Devuelve alertas activas de stock mínimo y límite de crédito.
    """
    return listar_alertas(tipo=tipo, id_sucursal=id_sucursal, solo_activas=solo_activas)


@router.patch("/{id_alerta}/resolver")
def resolver(id_alerta: int):
    """Marca una alerta como resuelta (activa = 0)."""
    try:
        return resolver_alerta(id_alerta)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
