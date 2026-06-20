"""
producto_service.py
Business logic for product catalog and stock management.
"""

from __future__ import annotations

import sqlite3
from datetime import datetime
from typing import List, Optional

from db.connection import get_connection
from models.producto import ProductoCreate, ProductoResponse, ProductoConStock, PrecioUpdate


def _row_to_producto(row: sqlite3.Row) -> ProductoResponse:
    return ProductoResponse(
        id_producto=row["id_producto"],
        sku=row["sku"],
        nombre=row["nombre"],
        categoria=row["categoria"],
        precio_costo=row["precio_costo"],
        precio_venta=row["precio_venta"],
        id_proveedor=row["id_proveedor"],
        activo=row["activo"],
        creado_en=row["creado_en"],
        actualizado_en=row["actualizado_en"],
    )


def crear_producto(data: ProductoCreate) -> ProductoResponse:
    """
    Creates a product and seeds its initial stock record for the given sucursal.
    """
    conn = get_connection()
    try:
        conn.execute("BEGIN")

        # Check for duplicate SKU
        if data.sku:
            existing = conn.execute(
                "SELECT id_producto FROM productos WHERE sku = ?", (data.sku,)
            ).fetchone()
            if existing:
                raise ValueError(f"Ya existe un producto con SKU '{data.sku}'.")

        cur = conn.execute(
            """INSERT INTO productos (sku, nombre, categoria, precio_costo, precio_venta, id_proveedor)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (data.sku, data.nombre, data.categoria, data.precio_costo,
             data.precio_venta, data.id_proveedor)
        )
        id_producto = cur.lastrowid

        # Seed stock_sucursal
        conn.execute(
            """INSERT OR IGNORE INTO stock_sucursal (id_producto, id_sucursal, cantidad_actual, stock_minimo_seguridad)
               VALUES (?, ?, ?, ?)""",
            (id_producto, data.id_sucursal, data.stock_inicial, data.stock_minimo_seguridad)
        )

        conn.commit()
        row = conn.execute("SELECT * FROM productos WHERE id_producto = ?", (id_producto,)).fetchone()
        return _row_to_producto(row)
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def listar_productos(
    id_sucursal: int = 1,
    categoria: Optional[str] = None,
    solo_activos: bool = True,
    page: int = 1,
    limit: int = 100,
) -> List[ProductoConStock]:
    """
    Returns products joined with their current stock for a given sucursal.
    Supports filtering by category and active status.
    """
    conn = get_connection()
    try:
        where = []
        params: list = [id_sucursal]

        if solo_activos:
            where.append("p.activo = 1")
        if categoria:
            where.append("p.categoria = ?")
            params.append(categoria)

        where_sql = ("AND " + " AND ".join(where)) if where else ""
        offset = (page - 1) * limit
        params += [limit, offset]

        rows = conn.execute(
            f"""SELECT p.*, 
                       COALESCE(ss.cantidad_actual, 0) as cantidad_actual,
                       COALESCE(ss.stock_minimo_seguridad, 0) as stock_minimo_seguridad,
                       ? as id_sucursal
                FROM productos p
                LEFT JOIN stock_sucursal ss ON p.id_producto = ss.id_producto AND ss.id_sucursal = ?
                WHERE 1=1 {where_sql}
                ORDER BY p.nombre
                LIMIT ? OFFSET ?""",
            [id_sucursal] + params
        ).fetchall()

        return [
            ProductoConStock(
                id_producto=r["id_producto"],
                sku=r["sku"],
                nombre=r["nombre"],
                categoria=r["categoria"],
                precio_costo=r["precio_costo"],
                precio_venta=r["precio_venta"],
                id_proveedor=r["id_proveedor"],
                activo=r["activo"],
                creado_en=r["creado_en"],
                actualizado_en=r["actualizado_en"],
                cantidad_actual=r["cantidad_actual"],
                stock_minimo_seguridad=r["stock_minimo_seguridad"],
                id_sucursal=id_sucursal,
            )
            for r in rows
        ]
    finally:
        conn.close()


def get_producto(id_producto: int) -> ProductoResponse:
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT * FROM productos WHERE id_producto = ?", (id_producto,)
        ).fetchone()
        if not row:
            raise ValueError(f"Producto id={id_producto} no encontrado.")
        return _row_to_producto(row)
    finally:
        conn.close()


def actualizar_precio(id_producto: int, data: PrecioUpdate) -> ProductoResponse:
    """
    Updates precio_costo and/or precio_venta and stamps actualizado_en.
    Used by the Supervisor role for global price adjustments.
    """
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT * FROM productos WHERE id_producto = ?", (id_producto,)
        ).fetchone()
        if not row:
            raise ValueError(f"Producto id={id_producto} no encontrado.")

        nuevo_costo = data.precio_costo if data.precio_costo is not None else row["precio_costo"]
        nuevo_venta = data.precio_venta if data.precio_venta is not None else row["precio_venta"]
        ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        conn.execute(
            """UPDATE productos
               SET precio_costo = ?, precio_venta = ?, actualizado_en = ?
               WHERE id_producto = ?""",
            (nuevo_costo, nuevo_venta, ahora, id_producto)
        )
        conn.commit()

        row = conn.execute("SELECT * FROM productos WHERE id_producto = ?", (id_producto,)).fetchone()
        return _row_to_producto(row)
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def prediccion_quiebre(id_sucursal: int = 1, ventana_dias: int = 30) -> list[dict]:
    """
    Implements the stock-break prediction formula from requirements.md §6.1:
        Dias_Restantes = Stock_Actual / Promedio_Ventas_Diarias

    Uses sales from the last `ventana_dias` days to compute average daily demand.
    Returns a list of products with their estimated days remaining and an alert
    flag if days_remaining < proveedor.tiempo_reposicion_dias.
    """
    conn = get_connection()
    try:
        rows = conn.execute(
            f"""SELECT
                    p.id_producto,
                    p.nombre,
                    p.id_proveedor,
                    COALESCE(pr.tiempo_reposicion_dias, 7) as tiempo_reposicion,
                    COALESCE(ss.cantidad_actual, 0) as stock_actual,
                    COALESCE(ss.stock_minimo_seguridad, 0) as stock_minimo,
                    COALESCE(SUM(dv.cantidad), 0) as total_vendido_periodo
                FROM productos p
                LEFT JOIN stock_sucursal ss ON p.id_producto = ss.id_producto AND ss.id_sucursal = ?
                LEFT JOIN proveedores pr ON p.id_proveedor = pr.id_proveedor
                LEFT JOIN detalle_venta dv ON p.id_producto = dv.id_producto
                LEFT JOIN ventas v ON dv.id_venta = v.id_venta
                    AND v.id_sucursal = ?
                    AND v.estado != 'Cancelado'
                    AND v.fecha_hora >= datetime('now', ?)
                WHERE p.activo = 1
                GROUP BY p.id_producto
                ORDER BY stock_actual ASC""",
            (id_sucursal, id_sucursal, f"-{ventana_dias} days")
        ).fetchall()

        result = []
        for r in rows:
            promedio_diario = r["total_vendido_periodo"] / ventana_dias if ventana_dias > 0 else 0
            if promedio_diario > 0:
                dias_restantes = round(r["stock_actual"] / promedio_diario, 1)
            else:
                dias_restantes = None  # No sales history → can't predict

            alerta_quiebre = (
                dias_restantes is not None and dias_restantes < r["tiempo_reposicion"]
            )

            result.append({
                "id_producto": r["id_producto"],
                "nombre": r["nombre"],
                "stock_actual": r["stock_actual"],
                "stock_minimo": r["stock_minimo"],
                "promedio_diario": round(promedio_diario, 3),
                "dias_restantes": dias_restantes,
                "tiempo_reposicion_dias": r["tiempo_reposicion"],
                "alerta_quiebre": alerta_quiebre,
            })

        return result
    finally:
        conn.close()
