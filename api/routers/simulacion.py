from fastapi import APIRouter, Query
from typing import Optional
from services.simulacion_service import simular_escenario

router = APIRouter(prefix="/simulacion", tags=["Proyecciones"])


@router.get("")
def simular(
    inflacion_pct: float = Query(0.0, description="% de inflación estimada"),
    variacion_demanda_pct: float = Query(0.0, ge=-100, description="% de variación de demanda (-50 a +50)"),
    costos_fijos_adicionales: float = Query(0.0, ge=0),
    id_sucursal: Optional[int] = Query(None),
    ventana_dias: int = Query(30, ge=7, le=90),
):
    """
    **CU08 – Simulador de Escenarios (What-If)**

    Clona los datos de precios/demanda EN MEMORIA y aplica:
    - Ajuste de precios por inflación
    - Variación de demanda
    - Costos fijos adicionales

    Retorna rentabilidad actual vs simulada sin mutar la BD de producción.
    """
    return simular_escenario(
        inflacion_pct=inflacion_pct,
        variacion_demanda_pct=variacion_demanda_pct,
        costos_fijos_adicionales=costos_fijos_adicionales,
        id_sucursal=id_sucursal,
        ventana_dias=ventana_dias,
    )
