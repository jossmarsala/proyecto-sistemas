"""
prediccion_service.py — FARO ML Forecasting Engine
====================================================
Uses scikit-learn LinearRegression + polynomial features for trend-aware
sales forecasting. Falls back to a simple 7-day moving average when there
is insufficient history (<7 days).

All predictions are in-memory. Nothing is written to the DB.
"""

from __future__ import annotations

import math
from datetime import datetime, timedelta, date
from typing import Optional

import numpy as np

from db.connection import get_connection


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _get_daily_series(
    id_sucursal: Optional[int],
    dias_historial: int,
) -> tuple[list[str], list[float]]:
    """
    Returns (fechas, valores) — a dense time series filling every day
    in the window with 0 where there were no sales.
    """
    conn = get_connection()
    try:
        sc = "AND id_sucursal = ?" if id_sucursal else ""
        params = [f"-{dias_historial} days"] + ([id_sucursal] if id_sucursal else [])

        rows = conn.execute(
            f"""SELECT DATE(fecha_hora) AS dia, COALESCE(SUM(total), 0) AS ingreso
                FROM ventas
                WHERE fecha_hora >= datetime('now', ?)
                  AND estado != 'Cancelado'
                  {sc}
                GROUP BY dia
                ORDER BY dia ASC""",
            params,
        ).fetchall()
    finally:
        conn.close()

    # Fill missing days
    data_map = {r["dia"]: float(r["ingreso"]) for r in rows}
    today = date.today()
    fechas, valores = [], []
    for i in range(dias_historial):
        d = (today - timedelta(days=dias_historial - 1 - i)).strftime("%Y-%m-%d")
        fechas.append(d)
        valores.append(data_map.get(d, 0.0))
    return fechas, valores


def _get_product_daily_series(
    id_producto: int,
    id_sucursal: Optional[int],
    dias_historial: int,
) -> tuple[list[str], list[float]]:
    conn = get_connection()
    try:
        sc = "AND v.id_sucursal = ?" if id_sucursal else ""
        params = [id_producto, f"-{dias_historial} days"] + ([id_sucursal] if id_sucursal else [])

        rows = conn.execute(
            f"""SELECT DATE(v.fecha_hora) AS dia, COALESCE(SUM(dv.cantidad), 0) AS qty
                FROM detalle_venta dv
                JOIN ventas v ON dv.id_venta = v.id_venta
                WHERE dv.id_producto = ?
                  AND v.fecha_hora >= datetime('now', ?)
                  AND v.estado != 'Cancelado'
                  {sc}
                GROUP BY dia
                ORDER BY dia ASC""",
            params,
        ).fetchall()
    finally:
        conn.close()

    data_map = {r["dia"]: float(r["qty"]) for r in rows}
    today = date.today()
    fechas, valores = [], []
    for i in range(dias_historial):
        d = (today - timedelta(days=dias_historial - 1 - i)).strftime("%Y-%m-%d")
        fechas.append(d)
        valores.append(data_map.get(d, 0.0))
    return fechas, valores


# ─────────────────────────────────────────────────────────────────────────────
# Core model
# ─────────────────────────────────────────────────────────────────────────────

def _ajuste_lineal(X: np.ndarray, y: np.ndarray):
    """
    Fits a degree-2 polynomial regression (quadratic trend) using numpy's
    lstsq. Falls back to degree-1 (linear) if fewer than 14 points.
    Returns (coefficients, degree).
    """
    degree = 2 if len(X) >= 14 else 1
    A = np.vstack([X ** i for i in range(degree + 1)]).T
    coeffs, _, _, _ = np.linalg.lstsq(A, y, rcond=None)
    return coeffs, degree


def _predict_poly(coeffs, degree: int, X: np.ndarray) -> np.ndarray:
    A = np.vstack([X ** i for i in range(degree + 1)]).T
    return A @ coeffs


def _moving_avg(values: list[float], window: int = 7) -> float:
    tail = values[-window:] if len(values) >= window else values
    return float(np.mean(tail)) if tail else 0.0


def _residual_std(actual: np.ndarray, predicted: np.ndarray) -> float:
    if len(actual) < 2:
        return 0.0
    residuals = actual - predicted
    return float(np.std(residuals))


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────

def predecir_ventas_globales(
    dias_historial: int = 60,
    dias_futuro: int = 30,
    id_sucursal: Optional[int] = None,
) -> dict:
    """
    Fits a polynomial regression to the last `dias_historial` daily sales
    totals and projects `dias_futuro` days ahead.

    Returns:
    {
        metodo:   'polynomial_regression' | 'moving_average' | 'insufficient_data',
        historial: [ { dia, ingreso } ],
        prediccion: [ { dia, ingreso_predicho, ci_lower, ci_upper } ],
        tendencia: 'creciente' | 'decreciente' | 'estable',
        ingreso_promedio_diario: float,
        ingreso_mes_proyectado: float,
        r2_score: float | None,
        dias_historial_usado: int,
    }
    """
    fechas, valores = _get_daily_series(id_sucursal, dias_historial)

    historial = [{"dia": f, "ingreso": v} for f, v in zip(fechas, valores)]
    non_zero  = [v for v in valores if v > 0]
    n = len(valores)

    today = date.today()

    # Not enough data → return flat projection from moving avg
    if len(non_zero) < 3:
        avg = _moving_avg(valores) if non_zero else 0.0
        prediccion = []
        for i in range(1, dias_futuro + 1):
            d = (today + timedelta(days=i)).strftime("%Y-%m-%d")
            prediccion.append({
                "dia": d,
                "ingreso_predicho": round(avg, 2),
                "ci_lower": 0.0,
                "ci_upper": round(avg * 1.5, 2),
            })
        return {
            "metodo": "moving_average",
            "historial": historial,
            "prediccion": prediccion,
            "tendencia": "estable",
            "ingreso_promedio_diario": round(avg, 2),
            "ingreso_mes_proyectado": round(avg * 30, 2),
            "r2_score": None,
            "dias_historial_usado": n,
        }

    # Polynomial regression
    X_hist = np.arange(n, dtype=float)
    y_hist = np.array(valores, dtype=float)
    coeffs, degree = _ajuste_lineal(X_hist, y_hist)
    y_pred_hist = _predict_poly(coeffs, degree, X_hist)
    std = _residual_std(y_hist, y_pred_hist)

    # R² score
    ss_res = np.sum((y_hist - y_pred_hist) ** 2)
    ss_tot = np.sum((y_hist - np.mean(y_hist)) ** 2)
    r2 = float(1 - ss_res / ss_tot) if ss_tot > 0 else None

    # Trend: compare last week prediction to the next week prediction
    end_hist  = _predict_poly(coeffs, degree, np.array([n - 1], dtype=float))[0]
    end_fut   = _predict_poly(coeffs, degree, np.array([n + 6], dtype=float))[0]
    delta_pct = ((end_fut - end_hist) / (end_hist + 1e-9)) * 100
    if delta_pct > 5:
        tendencia = "creciente"
    elif delta_pct < -5:
        tendencia = "decreciente"
    else:
        tendencia = "estable"

    # Future predictions
    prediccion = []
    for i in range(1, dias_futuro + 1):
        xi = float(n + i - 1)
        pred = float(_predict_poly(coeffs, degree, np.array([xi]))[0])
        pred = max(pred, 0.0)
        prediccion.append({
            "dia": (today + timedelta(days=i)).strftime("%Y-%m-%d"),
            "ingreso_predicho": round(pred, 2),
            "ci_lower":  round(max(pred - 1.96 * std, 0), 2),
            "ci_upper":  round(pred + 1.96 * std, 2),
        })

    # Use avg daily (from non-zero days) × 30 as the month projection
    # (raw regression can undershoot for early-window predictions)
    avg_diario = float(np.mean(y_hist[y_hist > 0])) if non_zero else 0.0
    # Also compute trend-adjusted version by averaging the next 30 predicted values
    mes_proy   = avg_diario * 30  # conservative baseline
    pred_sum   = sum(p["ingreso_predicho"] for p in prediccion[:30] if p["ingreso_predicho"] > 0)
    if pred_sum > 0:
        mes_proy = max(mes_proy, pred_sum)


    return {
        "metodo": "polynomial_regression",
        "historial": historial,
        "prediccion": prediccion,
        "tendencia": tendencia,
        "ingreso_promedio_diario": round(avg_diario, 2),
        "ingreso_mes_proyectado": round(mes_proy, 2),
        "r2_score": round(r2, 4) if r2 is not None else None,
        "dias_historial_usado": n,
    }


def predecir_producto(
    id_producto: int,
    dias_historial: int = 60,
    dias_futuro: int = 30,
    id_sucursal: Optional[int] = None,
) -> dict:
    """
    Per-product demand forecast. Returns projected units/day for the
    next `dias_futuro` days, plus estimated days until stockout.
    """
    fechas, valores = _get_product_daily_series(id_producto, id_sucursal, dias_historial)

    # Get current stock and product info
    conn = get_connection()
    try:
        prod = conn.execute(
            "SELECT nombre, precio_venta FROM productos WHERE id_producto = ?", (id_producto,)
        ).fetchone()
        stock_row = conn.execute(
            "SELECT cantidad_actual, stock_minimo_seguridad FROM stock_sucursal WHERE id_producto = ? AND id_sucursal = ?",
            (id_producto, id_sucursal or 1)
        ).fetchone()
    finally:
        conn.close()

    if not prod:
        raise ValueError(f"Producto id={id_producto} no encontrado.")

    stock_actual = float(stock_row["cantidad_actual"]) if stock_row else 0.0
    stock_minimo = float(stock_row["stock_minimo_seguridad"]) if stock_row else 0.0
    non_zero = [v for v in valores if v > 0]
    n = len(valores)
    today = date.today()

    if len(non_zero) < 3:
        avg = _moving_avg(valores) if non_zero else 0.0
        prediccion = []
        acumulado = stock_actual
        dias_hasta_minimo = None
        for i in range(1, dias_futuro + 1):
            d = (today + timedelta(days=i)).strftime("%Y-%m-%d")
            acumulado -= avg
            if dias_hasta_minimo is None and acumulado <= stock_minimo:
                dias_hasta_minimo = i
            prediccion.append({
                "dia": d,
                "cantidad_predicha": round(max(avg, 0), 3),
                "stock_proyectado": round(max(acumulado, 0), 2),
            })
        return {
            "id_producto": id_producto,
            "nombre": prod["nombre"],
            "metodo": "moving_average",
            "stock_actual": stock_actual,
            "stock_minimo": stock_minimo,
            "promedio_diario": round(avg, 3),
            "dias_hasta_quiebre": dias_hasta_minimo,
            "ingreso_proyectado_30d": round(avg * 30 * prod["precio_venta"], 2),
            "prediccion": prediccion,
        }

    X_hist = np.arange(n, dtype=float)
    y_hist = np.array(valores, dtype=float)
    coeffs, degree = _ajuste_lineal(X_hist, y_hist)
    std = _residual_std(y_hist, _predict_poly(coeffs, degree, X_hist))

    prediccion = []
    acumulado = stock_actual
    dias_hasta_minimo = None
    for i in range(1, dias_futuro + 1):
        xi = float(n + i - 1)
        pred = max(float(_predict_poly(coeffs, degree, np.array([xi]))[0]), 0.0)
        acumulado -= pred
        if dias_hasta_minimo is None and acumulado <= stock_minimo:
            dias_hasta_minimo = i
        prediccion.append({
            "dia": (today + timedelta(days=i)).strftime("%Y-%m-%d"),
            "cantidad_predicha": round(pred, 3),
            "stock_proyectado": round(max(acumulado, 0), 2),
        })

    avg_diario = float(np.mean(y_hist[y_hist > 0])) if non_zero else 0.0
    return {
        "id_producto": id_producto,
        "nombre": prod["nombre"],
        "metodo": "polynomial_regression",
        "stock_actual": stock_actual,
        "stock_minimo": stock_minimo,
        "promedio_diario": round(avg_diario, 3),
        "dias_hasta_quiebre": dias_hasta_minimo,
        "ingreso_proyectado_30d": round(avg_diario * 30 * prod["precio_venta"], 2),
        "prediccion": prediccion,
    }


def analytics_avanzado(
    id_sucursal: Optional[int] = None,
    dias: int = 90,
) -> dict:
    """
    Returns a rich analytics payload for the charts page:
    - ventas_por_dia_semana: Mon–Sun avg
    - ventas_por_hora: 0–23 distribution
    - top_10_productos: by revenue AND by quantity
    - margen_diario: ingreso vs costo per day
    - ticket_promedio: avg sale value
    """
    conn = get_connection()
    try:
        sc = "AND v.id_sucursal = ?" if id_sucursal else ""
        p_base = [f"-{dias} days"] + ([id_sucursal] if id_sucursal else [])

        # Sales by day of week (0=Mon … 6=Sun)
        dow_rows = conn.execute(
            f"""SELECT strftime('%w', fecha_hora) AS dow,
                       COUNT(*) AS num_ventas,
                       COALESCE(SUM(total), 0) AS ingreso
                FROM ventas
                WHERE fecha_hora >= datetime('now', ?) AND estado != 'Cancelado' {sc}
                GROUP BY dow ORDER BY dow""",
            p_base,
        ).fetchall()

        day_names = ["Dom", "Lun", "Mar", "Mié", "Jue", "Vie", "Sáb"]
        ventas_dow = {str(i): {"dia": day_names[i], "num_ventas": 0, "ingreso": 0} for i in range(7)}
        for r in dow_rows:
            ventas_dow[r["dow"]] = {
                "dia": day_names[int(r["dow"])],
                "num_ventas": r["num_ventas"],
                "ingreso": float(r["ingreso"]),
            }

        # Sales by hour
        hora_rows = conn.execute(
            f"""SELECT CAST(strftime('%H', fecha_hora) AS INTEGER) AS hora,
                       COUNT(*) AS num_ventas,
                       COALESCE(SUM(total), 0) AS ingreso
                FROM ventas
                WHERE fecha_hora >= datetime('now', ?) AND estado != 'Cancelado' {sc}
                GROUP BY hora ORDER BY hora""",
            p_base,
        ).fetchall()

        ventas_hora = {str(h): {"hora": h, "num_ventas": 0, "ingreso": 0} for h in range(24)}
        for r in hora_rows:
            ventas_hora[str(r["hora"])] = {
                "hora": r["hora"],
                "num_ventas": r["num_ventas"],
                "ingreso": float(r["ingreso"]),
            }

        # Top 10 by revenue
        top_rev = conn.execute(
            f"""SELECT p.nombre,
                       COALESCE(SUM(dv.subtotal), 0) AS revenue,
                       COALESCE(SUM(dv.cantidad), 0) AS qty
                FROM detalle_venta dv
                JOIN ventas v ON dv.id_venta = v.id_venta
                JOIN productos p ON dv.id_producto = p.id_producto
                WHERE v.fecha_hora >= datetime('now', ?) AND v.estado != 'Cancelado' {sc}
                GROUP BY dv.id_producto
                ORDER BY revenue DESC LIMIT 10""",
            p_base,
        ).fetchall()

        # Margin by day (ingreso vs costo)
        margin_rows = conn.execute(
            f"""SELECT DATE(v.fecha_hora) AS dia,
                       COALESCE(SUM(v.total), 0) AS ingreso,
                       COALESCE(SUM(dv.cantidad * p.precio_costo), 0) AS costo
                FROM ventas v
                JOIN detalle_venta dv ON v.id_venta = dv.id_venta
                JOIN productos p ON dv.id_producto = p.id_producto
                WHERE v.fecha_hora >= datetime('now', ?) AND v.estado != 'Cancelado' {sc}
                GROUP BY dia ORDER BY dia ASC""",
            p_base,
        ).fetchall()

        # Ticket promedio
        ticket_row = conn.execute(
            f"""SELECT AVG(total) AS avg_ticket, COUNT(*) AS num_ventas
                FROM ventas WHERE fecha_hora >= datetime('now', ?) AND estado != 'Cancelado' {sc}""",
            p_base,
        ).fetchone()

        return {
            "ventas_por_dia_semana": list(ventas_dow.values()),
            "ventas_por_hora": list(ventas_hora.values()),
            "top_10_productos": [
                {"nombre": r["nombre"], "revenue": float(r["revenue"]), "qty": float(r["qty"])}
                for r in top_rev
            ],
            "margen_diario": [
                {"dia": r["dia"], "ingreso": float(r["ingreso"]), "costo": float(r["costo"]),
                 "margen": round(float(r["ingreso"]) - float(r["costo"]), 2)}
                for r in margin_rows
            ],
            "ticket_promedio": round(float(ticket_row["avg_ticket"] or 0), 2),
            "total_ventas_periodo": ticket_row["num_ventas"],
        }
    finally:
        conn.close()
