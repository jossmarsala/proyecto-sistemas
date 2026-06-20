"""
simulacion_service.py
What-If DSS engine (CU08) — runs entirely in-memory, never mutates the DB.
"""
from __future__ import annotations
from typing import Optional
from db.connection import get_connection


def simular_escenario(
    inflacion_pct: float,
    variacion_demanda_pct: float,
    costos_fijos_adicionales: float = 0.0,
    id_sucursal: Optional[int] = None,
    ventana_dias: int = 30,
) -> dict:
    """
    Clones current revenue/cost data IN MEMORY and applies the What-If formulas.

    Formulas:
        precio_venta_sim  = precio_venta  * (1 + inflacion/100)
        precio_costo_sim  = precio_costo  * (1 + inflacion/100)
        demanda_sim       = promedio_diario * (1 + variacion_demanda/100)
        ingreso_sim       = precio_venta_sim  * demanda_sim * ventana_dias
        costo_sim         = precio_costo_sim  * demanda_sim * ventana_dias
        rentabilidad_sim  = ingreso_sim - costo_sim - costos_fijos_adicionales

    Returns both ACTUAL and SIMULATED numbers for the frontend to render diffs.
    """
    conn = get_connection()
    try:
        sc_filter = "AND v.id_sucursal = ?" if id_sucursal else ""
        sc_params = [id_sucursal] if id_sucursal else []

        rows = conn.execute(
            f"""SELECT
                    p.id_producto,
                    p.nombre,
                    p.precio_costo,
                    p.precio_venta,
                    COALESCE(SUM(dv.cantidad), 0) AS total_vendido
                FROM productos p
                LEFT JOIN detalle_venta dv ON p.id_producto = dv.id_producto
                LEFT JOIN ventas v ON dv.id_venta = v.id_venta
                    AND v.estado != 'Cancelado'
                    AND v.fecha_hora >= datetime('now', ?)
                    {sc_filter}
                WHERE p.activo = 1
                GROUP BY p.id_producto""",
            [f"-{ventana_dias} days"] + sc_params
        ).fetchall()

        # ── Actual totals ─────────────────────────────────────────────────────
        actual_ingreso = 0.0
        actual_costo   = 0.0

        # ── Simulated totals ──────────────────────────────────────────────────
        sim_ingreso = 0.0
        sim_costo   = 0.0

        productos_detalle = []

        for r in rows:
            prom_diario = r["total_vendido"] / ventana_dias if ventana_dias > 0 else 0

            # Actual
            ing_act = r["precio_venta"] * prom_diario * ventana_dias
            cos_act = r["precio_costo"] * prom_diario * ventana_dias
            actual_ingreso += ing_act
            actual_costo   += cos_act

            # Simulated
            pv_sim  = r["precio_venta"] * (1 + inflacion_pct / 100)
            pc_sim  = r["precio_costo"] * (1 + inflacion_pct / 100)
            dem_sim = prom_diario * (1 + variacion_demanda_pct / 100)
            ing_sim = pv_sim * dem_sim * ventana_dias
            cos_sim = pc_sim * dem_sim * ventana_dias
            sim_ingreso += ing_sim
            sim_costo   += cos_sim

            productos_detalle.append({
                "id_producto":      r["id_producto"],
                "nombre":           r["nombre"],
                "ingreso_actual":   round(ing_act, 2),
                "ingreso_simulado": round(ing_sim, 2),
                "delta_ingreso":    round(ing_sim - ing_act, 2),
            })

        actual_rent  = round(actual_ingreso - actual_costo, 2)
        sim_rent     = round(sim_ingreso - sim_costo - costos_fijos_adicionales, 2)
        delta_rent   = round(sim_rent - actual_rent, 2)
        delta_pct    = round((delta_rent / actual_rent * 100) if actual_rent else 0, 1)

        return {
            "parametros": {
                "inflacion_pct":              inflacion_pct,
                "variacion_demanda_pct":      variacion_demanda_pct,
                "costos_fijos_adicionales":   costos_fijos_adicionales,
                "ventana_dias":               ventana_dias,
            },
            "actual": {
                "ingreso_total":     round(actual_ingreso, 2),
                "costo_total":       round(actual_costo, 2),
                "rentabilidad":      actual_rent,
            },
            "simulado": {
                "ingreso_total":     round(sim_ingreso, 2),
                "costo_total":       round(sim_costo, 2),
                "rentabilidad":      sim_rent,
            },
            "delta": {
                "rentabilidad":      delta_rent,
                "porcentaje":        delta_pct,
                "alerta":            delta_rent < 0,
            },
            "productos": productos_detalle,
        }
    finally:
        conn.close()
