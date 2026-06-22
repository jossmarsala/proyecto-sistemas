"""
venta_service.py
Business logic for creating, listing, and querying sales.

Handles:
- Stock validation before committing a sale
- Atomic write: ventas + detalle_venta + stock_sucursal update
- Cuenta Corriente ledger entry when tipo_pago == 'Cuenta Corriente'
- Alerta generation when stock falls below stock_minimo_seguridad after a sale
"""

from __future__ import annotations

import sqlite3
from typing import List, Optional
from datetime import datetime

from db.connection import get_connection
from models.venta import VentaCreate, VentaResponse, VentaDetalleCompleto, DetalleVentaResponse



def _row_to_venta(row: sqlite3.Row) -> VentaResponse:
    return VentaResponse(
        id_venta=row["id_venta"],
        id_cliente=row["id_cliente"],
        id_usuario=row["id_usuario"],
        id_sucursal=row["id_sucursal"],
        fecha_hora=row["fecha_hora"],
        tipo_pago=row["tipo_pago"],
        tipo_venta=row["tipo_venta"],
        estado=row["estado"],
        referencia=row["referencia"],
        total=row["total"],
    )


def _row_to_detalle(row: sqlite3.Row) -> DetalleVentaResponse:
    return DetalleVentaResponse(
        id_detalle=row["id_detalle"],
        id_venta=row["id_venta"],
        id_producto=row["id_producto"],
        nombre_producto=row["nombre_producto"],
        cantidad=row["cantidad"],
        precio_unitario_historico=row["precio_unitario_historico"],
        subtotal=row["subtotal"],
    )


def crear_venta(data: VentaCreate) -> VentaDetalleCompleto:
    conn = get_connection()
    try:
        conn.execute("BEGIN")

        total = 0.0
        item_rows = []

        for item in data.items:
            prod = conn.execute(
                "SELECT id_producto, nombre, precio_venta FROM productos WHERE id_producto = ? AND activo = 1",
                (item.id_producto,)
            ).fetchone()
            if not prod:
                raise ValueError(f"Producto id={item.id_producto} no encontrado o inactivo.")

            stock_row = conn.execute(
                """SELECT cantidad_actual, stock_minimo_seguridad
                   FROM stock_sucursal
                   WHERE id_producto = ? AND id_sucursal = ?""",
                (item.id_producto, data.id_sucursal)
            ).fetchone()

            if not stock_row or stock_row["cantidad_actual"] < item.cantidad:
                disponible = stock_row["cantidad_actual"] if stock_row else 0
                raise ValueError(
                    f"Stock insuficiente para '{prod['nombre']}'. "
                    f"Disponible: {disponible}, solicitado: {item.cantidad}."
                )

            precio_historico = prod["precio_venta"]
            subtotal = round(precio_historico * item.cantidad, 2)
            total += subtotal
            item_rows.append({
                "id_producto": item.id_producto,
                "nombre_producto": prod["nombre"],
                "cantidad": item.cantidad,
                "precio_unitario_historico": precio_historico,
                "subtotal": subtotal,
                "stock_minimo": stock_row["stock_minimo_seguridad"],
                "nueva_cantidad": stock_row["cantidad_actual"] - item.cantidad,
            })

        total = round(total, 2)

        
        cur = conn.execute(
            """INSERT INTO ventas (id_cliente, id_usuario, id_sucursal, tipo_pago, tipo_venta, referencia, total)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (data.id_cliente, data.id_usuario, data.id_sucursal,
             data.tipo_pago, data.tipo_venta, data.referencia, total)
        )
        id_venta = cur.lastrowid

        detalle_responses: List[DetalleVentaResponse] = []

        for ir in item_rows:
            
            det_cur = conn.execute(
                """INSERT INTO detalle_venta (id_venta, id_producto, cantidad, precio_unitario_historico, subtotal)
                   VALUES (?, ?, ?, ?, ?)""",
                (id_venta, ir["id_producto"], ir["cantidad"],
                 ir["precio_unitario_historico"], ir["subtotal"])
            )
            detalle_responses.append(DetalleVentaResponse(
                id_detalle=det_cur.lastrowid,
                id_venta=id_venta,
                id_producto=ir["id_producto"],
                nombre_producto=ir["nombre_producto"],
                cantidad=ir["cantidad"],
                precio_unitario_historico=ir["precio_unitario_historico"],
                subtotal=ir["subtotal"],
            ))

            
            conn.execute(
                """UPDATE stock_sucursal
                   SET cantidad_actual = ?
                   WHERE id_producto = ? AND id_sucursal = ?""",
                (ir["nueva_cantidad"], ir["id_producto"], data.id_sucursal)
            )

            
            if ir["nueva_cantidad"] < ir["stock_minimo"]:
                conn.execute(
                    """INSERT OR IGNORE INTO alertas (tipo, id_referencia, id_sucursal, mensaje)
                       VALUES ('stock_minimo', ?, ?, ?)""",
                    (
                        ir["id_producto"],
                        data.id_sucursal,
                        f"⚠️ Stock mínimo perforado: '{ir['nombre_producto']}' "
                        f"— quedan {ir['nueva_cantidad']} unidades."
                    )
                )

        
        if data.tipo_pago == "Cuenta Corriente" and data.id_cliente:
            cliente = conn.execute(
                "SELECT saldo_cuenta_corriente, limite_credito FROM clientes WHERE id_cliente = ?",
                (data.id_cliente,)
            ).fetchone()
            if not cliente:
                raise ValueError(f"Cliente id={data.id_cliente} no encontrado.")

            nuevo_saldo = round(cliente["saldo_cuenta_corriente"] + total, 2)
            if nuevo_saldo > cliente["limite_credito"] > 0:
                raise ValueError(
                    f"Límite de crédito excedido. Saldo actual: {cliente['saldo_cuenta_corriente']}, "
                    f"Límite: {cliente['limite_credito']}."
                )

            conn.execute(
                """INSERT INTO cuenta_corriente (id_cliente, id_venta, tipo, monto, saldo_resultante)
                   VALUES (?, ?, 'cargo', ?, ?)""",
                (data.id_cliente, id_venta, total, nuevo_saldo)
            )
            conn.execute(
                "UPDATE clientes SET saldo_cuenta_corriente = ? WHERE id_cliente = ?",
                (nuevo_saldo, data.id_cliente)
            )

            
            if cliente["limite_credito"] > 0 and nuevo_saldo >= cliente["limite_credito"] * 0.9:
                conn.execute(
                    """INSERT OR IGNORE INTO alertas (tipo, id_referencia, mensaje)
                       VALUES ('limite_credito', ?, ?)""",
                    (
                        data.id_cliente,
                        f"⚠️ Cliente id={data.id_cliente} alcanzó el 90% de su límite de crédito "
                        f"(${nuevo_saldo} / ${cliente['limite_credito']})."
                    )
                )

        conn.commit()

        
        venta_row = conn.execute(
            "SELECT * FROM ventas WHERE id_venta = ?", (id_venta,)
        ).fetchone()

        return VentaDetalleCompleto(
            **_row_to_venta(venta_row).model_dump(),
            items=detalle_responses,
        )

    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def listar_ventas(
    fecha_desde: Optional[str] = None,
    fecha_hasta: Optional[str] = None,
    id_sucursal: Optional[int] = None,
    id_usuario: Optional[int] = None,
    id_cliente: Optional[int] = None,
    page: int = 1,
    limit: int = 50,
) -> List[VentaResponse]:
    """Returns a paginated list of ventas with optional filters."""
    conn = get_connection()
    try:
        where_clauses = []
        params: list = []

        if fecha_desde:
            where_clauses.append("v.fecha_hora >= ?")
            params.append(fecha_desde)
        if fecha_hasta:
            where_clauses.append("v.fecha_hora <= ?")
            params.append(fecha_hasta)
        if id_sucursal:
            where_clauses.append("v.id_sucursal = ?")
            params.append(id_sucursal)
        if id_usuario:
            where_clauses.append("v.id_usuario = ?")
            params.append(id_usuario)
        if id_cliente:
            where_clauses.append("v.id_cliente = ?")
            params.append(id_cliente)

        where_sql = ("WHERE " + " AND ".join(where_clauses)) if where_clauses else ""
        offset = (page - 1) * limit
        params += [limit, offset]

        rows = conn.execute(
            f"SELECT * FROM ventas v {where_sql} ORDER BY v.fecha_hora DESC LIMIT ? OFFSET ?",
            params
        ).fetchall()

        return [_row_to_venta(r) for r in rows]
    finally:
        conn.close()


def get_detalles_venta(id_venta: int) -> VentaDetalleCompleto:
    """Returns a venta with its full line-item breakdown."""
    conn = get_connection()
    try:
        venta_row = conn.execute(
            "SELECT * FROM ventas WHERE id_venta = ?", (id_venta,)
        ).fetchone()
        if not venta_row:
            raise ValueError(f"Venta id={id_venta} no encontrada.")

        detalle_rows = conn.execute(
            """SELECT dv.*, p.nombre AS nombre_producto
               FROM detalle_venta dv
               JOIN productos p ON dv.id_producto = p.id_producto
               WHERE dv.id_venta = ?
               ORDER BY dv.id_detalle""",
            (id_venta,)
        ).fetchall()

        return VentaDetalleCompleto(
            **_row_to_venta(venta_row).model_dump(),
            items=[_row_to_detalle(r) for r in detalle_rows],
        )
    finally:
        conn.close()


def resumen_stats(id_sucursal: Optional[int] = None) -> dict:
    """
    Returns a quick analytics summary:
    - total_ventas (count)
    - ingresos_totales (sum)
    - ingresos_hoy
    - ingresos_mes
    - top_5_productos (by qty sold)
    """
    conn = get_connection()
    try:
        sc = "AND v.id_sucursal = ?" if id_sucursal else ""
        p = [id_sucursal] if id_sucursal else []

        total_row = conn.execute(
            f"SELECT COUNT(*) as cnt, COALESCE(SUM(total),0) as suma FROM ventas v WHERE v.estado != 'Cancelado' {sc}",
            p
        ).fetchone()

        hoy = datetime.now().strftime("%Y-%m-%d")
        hoy_row = conn.execute(
            f"SELECT COALESCE(SUM(total),0) as suma FROM ventas v WHERE DATE(v.fecha_hora)=? AND v.estado!='Cancelado' {sc}",
            [hoy] + p
        ).fetchone()

        mes = datetime.now().strftime("%Y-%m")
        mes_row = conn.execute(
            f"SELECT COALESCE(SUM(total),0) as suma FROM ventas v WHERE strftime('%Y-%m',v.fecha_hora)=? AND v.estado!='Cancelado' {sc}",
            [mes] + p
        ).fetchone()

        top_rows = conn.execute(
            f"""SELECT p.nombre, SUM(dv.cantidad) as total_vendido
                FROM detalle_venta dv
                JOIN ventas v ON dv.id_venta = v.id_venta
                JOIN productos p ON dv.id_producto = p.id_producto
                WHERE v.estado != 'Cancelado' {sc}
                GROUP BY dv.id_producto
                ORDER BY total_vendido DESC
                LIMIT 5""",
            p
        ).fetchall()

        return {
            "total_ventas": total_row["cnt"],
            "ingresos_totales": total_row["suma"],
            "ingresos_hoy": hoy_row["suma"],
            "ingresos_mes": mes_row["suma"],
            "top_5_productos": [{"nombre": r["nombre"], "total_vendido": r["total_vendido"]} for r in top_rows],
        }
    finally:
        conn.close()
