"""
predicciones.py — ML Forecasting Endpoints
"""

from fastapi import APIRouter, Query, HTTPException
from typing import Optional

from services.prediccion_service import (
    predecir_ventas_globales,
    predecir_producto,
    analytics_avanzado,
)

router = APIRouter(prefix="/predicciones", tags=["Predicciones ML"])


@router.get("/ventas")
def forecast_ventas(
    dias_historial: int = Query(60, ge=7, le=365),
    dias_futuro:    int = Query(30, ge=7, le=90),
    id_sucursal:    Optional[int] = Query(None),
):
    """
    **Pronóstico de Ventas (Linear / Polynomial Regression)**

    Ajusta una regresión polinómica de grado 1–2 a los últimos
    `dias_historial` días de ventas y proyecta `dias_futuro` días hacia el futuro.

    Devuelve historial real, predicción con intervalo de confianza 95%,
    tendencia estimada, R² del modelo y proyección del próximo mes.
    """
    return predecir_ventas_globales(
        dias_historial=dias_historial,
        dias_futuro=dias_futuro,
        id_sucursal=id_sucursal,
    )


@router.get("/productos/{id_producto}")
def forecast_producto(
    id_producto:    int,
    dias_historial: int = Query(60, ge=7, le=365),
    dias_futuro:    int = Query(30, ge=7, le=90),
    id_sucursal:    Optional[int] = Query(None),
):
    """
    **Pronóstico por Producto**

    Proyecta demanda diaria y stock proyectado para un producto específico.
    Calcula `dias_hasta_quiebre` basado en la tendencia de demanda.
    """
    try:
        return predecir_producto(
            id_producto=id_producto,
            dias_historial=dias_historial,
            dias_futuro=dias_futuro,
            id_sucursal=id_sucursal,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/analytics")
def analytics(
    id_sucursal: Optional[int] = Query(None),
    dias:        int = Query(90, ge=7, le=365),
):
    """
    **Analytics Avanzado** — Payload completo para Chart.js:
    - Ventas por día de la semana y por hora
    - Top 10 productos por revenue y por cantidad
    - Margen diario (ingreso vs costo)
    - Ticket promedio
    """
    return analytics_avanzado(id_sucursal=id_sucursal, dias=dias)
