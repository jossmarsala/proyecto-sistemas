"""
seed_demo_data.py — Popula la BD con datos históricos realistas para demo.
Crea ~90 días de ventas sintéticas con tendencia creciente + ruido.

Uso: python3 seed_demo_data.py
"""

import sqlite3
import random
import math
from datetime import datetime, timedelta, date
from pathlib import Path

# ── Locate DB ─────────────────────────────────────────────────────────────────

BASE = Path(__file__).resolve().parent
DB   = BASE / "database" / "ventas.db"

if not DB.exists():
    print("❌ Base de datos no encontrada. Arrancá el servidor primero con uvicorn.")
    raise SystemExit(1)

conn = sqlite3.connect(str(DB))
conn.row_factory = sqlite3.Row
conn.execute("PRAGMA foreign_keys = ON")

# ── Products ──────────────────────────────────────────────────────────────────

PRODUCTOS = [
    ("FER-001", "Tornillo autorroscante 5mm",  None,  12.0,  22.0, 500, 50),
    ("FER-002", "Tornillo hexagonal M8",        None,  18.0,  35.0, 300, 40),
    ("FER-003", "Tuerca mariposa 10mm",         None,  8.0,   15.0, 400, 60),
    ("PIN-001", "Pintura látex interior 4L",    "Pinturas",    650.0,1100.0,  80, 10),
    ("PIN-002", "Esmalte sintético blanco 1L",  "Pinturas",    320.0, 550.0,  60,  8),
    ("HER-001", "Taladro percutor 750W",        "Herramientas",4200.0,7500.0, 20,  3),
    ("HER-002", "Amoladora angular 115mm",      "Herramientas",2800.0,5000.0, 15,  3),
    ("ELE-001", "Cable eléctrico 2.5mm x 10m",  "Eléctrica",  480.0, 850.0,  40,  8),
    ("ELE-002", "Disyuntor 16A bipolar",        "Eléctrica",  380.0, 680.0,  30,  5),
    ("PLO-001", "Caño PVC 110mm x 3m",         "Plomería",    220.0, 390.0,  50,  8),
    ("PLO-002", "Llave de paso 3/4\"",          "Plomería",    290.0, 520.0,  35,  6),
    ("ABR-001", "Adhesivo epoxi bicomponente",  "Adhesivos",   95.0,  170.0, 120, 20),
    ("ABR-002", "Silicona transparente 280ml",  "Adhesivos",   65.0,  115.0, 150, 25),
    ("SEG-001", "Guantes de trabajo talle L",   "Seguridad",   85.0,  150.0, 100, 15),
    ("SEG-002", "Casco de seguridad blanco",    "Seguridad",  180.0, 320.0,  40,  8),
]

CLIENTES = [
    ("Construcciones", "García", "García S.A.", "30712345678", "1134567890", 500000),
    ("Mario",  "Rodríguez", None, None, "1123456789", 50000),
    ("Laura",  "Fernández", None, None, "1198765432", 30000),
    ("Obras",  "Del Norte",  "Del Norte S.R.L.", "30765432100", "1156789012", 200000),
    ("Pablo",  "Torres",    None, None, "1167890123", 20000),
]

# ── Wipe and recreate test data ────────────────────────────────────────────────

print("🌱 Eliminando datos de demo anteriores…")
conn.execute("DELETE FROM alertas")
conn.execute("DELETE FROM cuenta_corriente")
conn.execute("DELETE FROM detalle_venta")
conn.execute("DELETE FROM ventas")
conn.execute("DELETE FROM stock_sucursal")
conn.execute("DELETE FROM productos")
conn.execute("DELETE FROM clientes")
conn.commit()

# ── Insert products ────────────────────────────────────────────────────────────

print("📦 Insertando productos…")
prod_ids = {}
for sku, nombre, cat, costo, venta, stock, minimo in PRODUCTOS:
    cur = conn.execute(
        "INSERT INTO productos (sku, nombre, categoria, precio_costo, precio_venta) VALUES (?,?,?,?,?)",
        (sku, nombre, cat, costo, venta)
    )
    pid = cur.lastrowid
    prod_ids[sku] = {"id": pid, "nombre": nombre, "precio": venta, "costo": costo, "stock": stock}
    conn.execute(
        "INSERT INTO stock_sucursal (id_producto, id_sucursal, cantidad_actual, stock_minimo_seguridad) VALUES (?,1,?,?)",
        (pid, stock, minimo)
    )
conn.commit()

# ── Insert clients ─────────────────────────────────────────────────────────────

print("👤 Insertando clientes…")
cli_ids = []
for nombre, apellido, rs, cuit, tel, limite in CLIENTES:
    cur = conn.execute(
        "INSERT INTO clientes (nombre, apellido, razon_social, cuit_dni, telefono, limite_credito) VALUES (?,?,?,?,?,?)",
        (nombre, apellido, rs, cuit, tel, limite)
    )
    cli_ids.append(cur.lastrowid)
conn.commit()

# ── Generate 90 days of sales ─────────────────────────────────────────────────

print("🧾 Generando 90 días de historial de ventas…")

random.seed(42)
today   = date.today()
prods   = list(prod_ids.values())
stock_track = {p["id"]: p["stock"] for p in prods}  # track deductions

PAGOS = ["Efectivo", "Tarjeta", "Cuenta Corriente"]
PAY_WEIGHTS = [0.55, 0.30, 0.15]

ventas_count = 0
for days_ago in range(89, -1, -1):   # oldest first
    target_date = today - timedelta(days=days_ago)

    # Skip Sundays (lower traffic)
    is_domingo = target_date.weekday() == 6
    if is_domingo and random.random() < 0.6:
        continue

    # Growing trend: more sales as time progresses
    trend_factor = 1.0 + (89 - days_ago) / 89 * 0.8   # 1.0 → 1.8

    # Day-of-week multiplier
    dow_mult = [0.9, 1.1, 1.2, 1.0, 1.3, 1.4, 0.5][target_date.weekday()]

    num_ventas = max(1, int(random.gauss(3, 1.2) * trend_factor * dow_mult))

    for _ in range(num_ventas):
        # Random hour (8am–7pm, peak at 10–12 and 15–17)
        if random.random() < 0.4:
            hora = random.randint(10, 12)
        elif random.random() < 0.5:
            hora = random.randint(15, 17)
        else:
            hora = random.randint(8, 19)
        minuto = random.randint(0, 59)
        fecha_hora = datetime.combine(target_date, datetime.min.time()).replace(
            hour=hora, minute=minuto, second=random.randint(0, 59)
        )

        tipo_pago = random.choices(PAGOS, weights=PAY_WEIGHTS)[0]
        cliente_id = random.choice(cli_ids) if tipo_pago != "Efectivo" or random.random() < 0.3 else None

        # Select 1–4 random products
        items = random.sample(prods, k=random.randint(1, min(4, len(prods))))
        total = 0.0
        detalles = []
        skip = False

        for prod in items:
            max_qty = min(stock_track.get(prod["id"], 0), random.randint(1, 8))
            if max_qty <= 0:
                continue
            qty = random.randint(1, max_qty)
            sub = round(prod["precio"] * qty, 2)
            total += sub
            stock_track[prod["id"]] -= qty
            detalles.append((prod["id"], qty, prod["precio"], sub))

        if not detalles:
            continue

        total = round(total, 2)
        cur = conn.execute(
            """INSERT INTO ventas (id_cliente, id_usuario, id_sucursal, fecha_hora, tipo_pago, tipo_venta, estado, total)
               VALUES (?,1,1,?,?,'local','Pagado',?)""",
            (cliente_id, fecha_hora.strftime("%Y-%m-%d %H:%M:%S"), tipo_pago, total)
        )
        venta_id = cur.lastrowid

        for id_prod, qty, precio, sub in detalles:
            conn.execute(
                "INSERT INTO detalle_venta (id_venta, id_producto, cantidad, precio_unitario_historico, subtotal) VALUES (?,?,?,?,?)",
                (venta_id, id_prod, qty, precio, sub)
            )

        ventas_count += 1

conn.commit()

# ── Update stock_sucursal to reflect deductions ───────────────────────────────

print("📉 Actualizando stock en base a ventas…")
for prod_id, remaining in stock_track.items():
    conn.execute(
        "UPDATE stock_sucursal SET cantidad_actual = ? WHERE id_producto = ? AND id_sucursal = 1",
        (max(remaining, 0), prod_id)
    )

# ── Create some stock alerts for low-stock items ──────────────────────────────

low_stock = conn.execute(
    """SELECT p.id_producto, p.nombre, ss.cantidad_actual, ss.stock_minimo_seguridad
       FROM productos p JOIN stock_sucursal ss ON p.id_producto = ss.id_producto
       WHERE ss.cantidad_actual <= ss.stock_minimo_seguridad AND ss.id_sucursal = 1"""
).fetchall()

for r in low_stock:
    conn.execute(
        "INSERT OR IGNORE INTO alertas (tipo, id_referencia, id_sucursal, mensaje) VALUES ('stock_minimo',?,1,?)",
        (r["id_producto"], f"⚠️ Stock mínimo perforado: '{r['nombre']}' — quedan {r['cantidad_actual']} unidades.")
    )

conn.commit()
conn.close()

print(f"\n✅ Seed completo:")
print(f"   Productos: {len(PRODUCTOS)}")
print(f"   Clientes:  {len(CLIENTES)}")
print(f"   Ventas:    {ventas_count}")
print(f"   Alertas:   {len(low_stock)} (stock bajo)")
print(f"\n🚀 Abrí http://localhost:8000 para ver el dashboard con datos reales.")
