"""
seed_demo_data.py — Popula la BD con datos históricos realistas para demo.
Crea ~180 días de ventas sintéticas con tendencias, variabilidad, picos estacionales, 
clientes B2B/B2C, diferentes métodos de pago y estados de venta para visualizar en charts.

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
# Variado: Distintos márgenes, precios (High ticket vs Low ticket), stock y categorías.

PRODUCTOS = [
    # Ferretería (Alto volumen, bajo ticket)
    ("FER-001", "Tornillo autorroscante 5mm (x100)", "Ferretería", 150.0, 350.0, 800, 100),
    ("FER-002", "Tornillo hexagonal M8 (x50)", "Ferretería", 300.0, 600.0, 500, 80),
    ("FER-003", "Tuerca mariposa 10mm (x50)", "Ferretería", 200.0, 450.0, 600, 100),
    ("FER-004", "Clavos punta parís 2.5 pulg (1kg)", "Ferretería", 800.0, 1500.0, 300, 50),
    ("FER-005", "Tarugo Nylon N8 (x100)", "Ferretería", 400.0, 950.0, 500, 80),
    ("FER-006", "Bisagra libro zincada 2 pulg", "Ferretería", 250.0, 550.0, 200, 30),
    # Pinturas (Ticket medio, margen medio-alto)
    ("PIN-001", "Pintura látex interior 20L", "Pinturas", 15000.0, 25000.0, 60, 15),
    ("PIN-002", "Pintura látex exterior 20L", "Pinturas", 18000.0, 32000.0, 50, 10),
    ("PIN-003", "Esmalte sintético brillante 4L", "Pinturas", 8500.0, 14500.0, 80, 20),
    ("PIN-004", "Enduido plástico 10L", "Pinturas", 6000.0, 11000.0, 90, 25),
    ("PIN-005", "Rodillo antigota 22cm", "Pinturas", 1200.0, 2500.0, 120, 25),
    ("PIN-006", "Pincel cerda blanca N20", "Pinturas", 800.0, 1800.0, 150, 30),
    # Herramientas (Ticket alto, margen medio)
    ("HER-001", "Taladro percutor 750W", "Herramientas", 45000.0, 78000.0, 30, 8),
    ("HER-002", "Amoladora angular 115mm", "Herramientas", 38000.0, 65000.0, 25, 6),
    ("HER-003", "Sierra circular 1400W", "Herramientas", 65000.0, 110000.0, 15, 3),
    ("HER-004", "Set de llaves combinadas (12 pzs)", "Herramientas", 12000.0, 22000.0, 40, 10),
    ("HER-005", "Cinta métrica 5m", "Herramientas", 1800.0, 3500.0, 100, 20),
    ("HER-006", "Martillo galponero", "Herramientas", 4500.0, 8500.0, 60, 15),
    # Eléctrica
    ("ELE-001", "Rollo cable 2.5mm Normalizado 100m", "Eléctrica", 22000.0, 38000.0, 50, 10),
    ("ELE-002", "Interruptor termomagnético 2x16A", "Eléctrica", 4500.0, 8500.0, 80, 20),
    ("ELE-003", "Disyuntor diferencial 2x25A", "Eléctrica", 18000.0, 32000.0, 40, 10),
    ("ELE-004", "Caja rectangular 5x10 chapa", "Eléctrica", 250.0, 550.0, 300, 60),
    ("ELE-005", "Módulo toma doble 10A", "Eléctrica", 1500.0, 3200.0, 200, 40),
    # Plomería
    ("PLO-001", "Caño termofusión 20mm x 4m", "Plomería", 2500.0, 4800.0, 150, 30),
    ("PLO-002", "Llave de paso termofusión 20mm", "Plomería", 3800.0, 7500.0, 80, 15),
    ("PLO-003", "Codo 90 termofusión 20mm", "Plomería", 350.0, 800.0, 300, 60),
    ("PLO-004", "Caño PVC cloacal 110mm x 4m", "Plomería", 5500.0, 10500.0, 60, 15),
    ("PLO-005", "Sifón pileta cocina", "Plomería", 2200.0, 4500.0, 90, 20),
    # Construcción (Materiales pesados, ticket medio-alto)
    ("CON-001", "Cemento Portland 50kg", "Construcción", 6500.0, 9500.0, 400, 100),
    ("CON-002", "Cal hidratada 25kg", "Construcción", 3200.0, 5000.0, 300, 80),
    ("CON-003", "Pegamento impermeable 30kg", "Construcción", 4800.0, 7500.0, 150, 40),
    ("CON-004", "Hierro aletado 8mm x 12m", "Construcción", 5800.0, 9200.0, 500, 100),
    ("CON-005", "Ladrillo hueco 12x18x33 (palet x 144)", "Construcción", 28000.0, 45000.0, 30, 8),
    # Seguridad (Adicionales)
    ("SEG-001", "Guantes de trabajo Moteados", "Seguridad", 600.0, 1200.0, 250, 50),
    ("SEG-002", "Casco de seguridad amarillo", "Seguridad", 3500.0, 6500.0, 80, 20),
]

# ── Clients ───────────────────────────────────────────────────────────────────

CLIENTES = [
    # B2B - Grandes Constructoras (Mucho límite de crédito, cuentas corrientes altas)
    ("Constructora", "Nacional", "Construcciones Nacionales S.A.", "30712345678", "1134567890", 2500000, "B2B"),
    ("Desarrollos", "Urbanos", "Desarrollos Urbanos SRL", "30765432100", "1156789012", 1500000, "B2B"),
    ("Edificios", "Premium", "Edificios Premium S.A.", "30987654321", "1145678901", 3000000, "B2B"),
    # B2B - Contratistas y Profesionales
    ("Carlos", "Gómez", "Gómez Instalaciones", "20123456789", "1123456789", 500000, "B2B"),
    ("Roberto", "Silva", "Silva Plomería y Gas", "20987654321", "1187654321", 300000, "B2B"),
    ("Mariano", "Herrera", "Herrera Electricidad", "20345678901", "1176543210", 400000, "B2B"),
    # B2C - Consumidores Finales (Sin límite o muy bajo, sin Razón Social)
    ("Laura", "Fernández", None, "27456789012", "1198765432", 0, "B2C"),
    ("Pablo", "Torres", None, "20567890123", "1167890123", 0, "B2C"),
    ("Ana", "Martínez", None, "27678901234", "1134567812", 0, "B2C"),
    ("Diego", "López", None, "20789012345", "1155667788", 0, "B2C"),
    ("Sofía", "Romero", None, "27890123456", "1122334455", 0, "B2C"),
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
    prod_ids[pid] = {"id": pid, "nombre": nombre, "precio": venta, "costo": costo, "stock": stock, "cat": cat}
    conn.execute(
        "INSERT INTO stock_sucursal (id_producto, id_sucursal, cantidad_actual, stock_minimo_seguridad) VALUES (?,1,?,?)",
        (pid, stock, minimo)
    )
conn.commit()

# ── Insert clients ─────────────────────────────────────────────────────────────

print("👤 Insertando clientes…")
cli_b2b = []
cli_b2c = []
for nombre, apellido, rs, cuit, tel, limite, tipo in CLIENTES:
    cur = conn.execute(
        "INSERT INTO clientes (nombre, apellido, razon_social, cuit_dni, telefono, limite_credito) VALUES (?,?,?,?,?,?)",
        (nombre, apellido, rs, cuit, tel, limite)
    )
    cid = cur.lastrowid
    if tipo == "B2B":
        cli_b2b.append(cid)
    else:
        cli_b2c.append(cid)
conn.commit()

# ── Generate 180 days of sales ─────────────────────────────────────────────────
# Ampliamos a ~180 días (6 meses) para dar más riqueza a los gráficos anuales/mensuales.

DAYS = 180
print(f"🧾 Generando {DAYS} días de historial de ventas realista…")

random.seed(101) # Fija para resultados reproducibles pero variados
today = date.today()
prods = list(prod_ids.values())
stock_track = {p["id"]: p["stock"] for p in prods}

PAGOS = ["Efectivo", "Tarjeta", "Cuenta Corriente"]
ESTADOS = ["Pagado", "A cobrar / parcial", "Cancelado"]

ventas_count = 0
recaudacion_total = 0.0

for days_ago in range(DAYS-1, -1, -1):
    target_date = today - timedelta(days=days_ago)
    
    is_domingo = target_date.weekday() == 6
    is_sabado = target_date.weekday() == 5
    
    # Domingos cerramos, o abrimos mediodía con poquísimas ventas (10% de un día normal)
    if is_domingo and random.random() < 0.8:
        continue

    # Tendencia base: Crecimiento ligero mensual (para simular negocio en expansión)
    # Factor de tendencia base (de 1.0 hace 180 días a ~1.4 hoy)
    base_trend = 1.0 + ((DAYS - days_ago) / DAYS) * 0.4 
    
    # Efecto estacional: principio de mes (cobro de sueldos) hay más ventas
    day_of_month = target_date.day
    if 1 <= day_of_month <= 10:
        seasonality = 1.3
    elif 11 <= day_of_month <= 20:
        seasonality = 1.0
    else:
        seasonality = 0.85
        
    # Picos especiales (ej. Hot Sale o Promociones al azar)
    is_promo_day = random.random() < 0.03 # 3% de los días son promos
    promo_multiplier = 2.5 if is_promo_day else 1.0
    
    # Multiplicador día de la semana
    dow_mult = [1.1, 1.1, 1.0, 1.2, 1.3, 1.5, 0.3][target_date.weekday()] # Sábados fuertes, domingos flojos

    # Calcular cantidad de ventas para el día
    if is_domingo:
        num_ventas = random.randint(1, 3)
    else:
        mean_ventas = 8 * base_trend * seasonality * dow_mult * promo_multiplier
        num_ventas = max(1, int(random.gauss(mean_ventas, mean_ventas * 0.3)))

    for _ in range(num_ventas):
        # Distribución horaria
        if is_sabado:
            hora = random.randint(8, 14) # Sábados abren hasta el mediodía
        elif random.random() < 0.4:
            hora = random.randint(9, 12) # Mañana fuerte
        elif random.random() < 0.4:
            hora = random.randint(15, 18) # Tarde fuerte
        else:
            hora = random.randint(8, 19)
            
        minuto = random.randint(0, 59)
        fecha_hora = datetime.combine(target_date, datetime.min.time()).replace(
            hour=hora, minute=minuto, second=random.randint(0, 59)
        )

        # B2B vs B2C sale
        is_b2b = random.random() < 0.25 # 25% de las ventas son B2B
        
        if is_b2b:
            cliente_id = random.choice(cli_b2b)
            # B2B pagan con CC, Tarjeta, o a veces efectivo
            tipo_pago = random.choices(["Cuenta Corriente", "Tarjeta", "Efectivo"], weights=[0.6, 0.3, 0.1])[0]
            # B2B compran más items y mayor cantidad (ticket promedio alto)
            max_items = random.randint(3, 10)
            qty_multiplier = random.randint(2, 8)
        else:
            # B2C pueden ser anonimos (None) o tener id
            cliente_id = random.choice(cli_b2c) if random.random() < 0.4 else None
            # B2C pagan con Tarjeta o Efectivo
            tipo_pago = random.choices(["Tarjeta", "Efectivo"], weights=[0.6, 0.4])[0]
            max_items = random.randint(1, 4)
            qty_multiplier = 1

        # Estados realistas: 
        # CC suele quedar "A cobrar / parcial" o "Pagado"
        # 3% de cancelaciones generales
        if random.random() < 0.03:
            estado = "Cancelado"
        elif tipo_pago == "Cuenta Corriente" and random.random() < 0.7:
            estado = "A cobrar / parcial"
        else:
            estado = "Pagado"

        # Elegimos productos (evitando los que no hay stock para no romper tracking, aunque podemos ignorarlo en historial)
        items = random.sample(prods, k=random.randint(1, min(max_items, len(prods))))
        total = 0.0
        detalles = []

        for prod in items:
            # Seleccionamos categoría preferentemente si es B2B Constructor (compran construcción)
            # Simplificado: Compran aleatorio, pero cantidades variadas
            base_qty = random.randint(1, 5)
            qty = base_qty * qty_multiplier
            
            # Limitar a stock disponible en tracking
            max_qty = min(stock_track.get(prod["id"], 0), qty)
            if max_qty <= 0:
                continue
            
            qty = random.randint(1, max_qty) if max_qty > 1 else 1
            sub = round(prod["precio"] * qty, 2)
            total += sub
            stock_track[prod["id"]] -= qty
            detalles.append((prod["id"], qty, prod["precio"], sub))

        if not detalles:
            continue

        total = round(total, 2)
        
        # Descuentos B2B
        if is_b2b and total > 50000:
            descuento = round(total * 0.10, 2) # 10% off
            total = total - descuento

        cur = conn.execute(
            """INSERT INTO ventas (id_cliente, id_usuario, id_sucursal, fecha_hora, tipo_pago, tipo_venta, estado, total)
               VALUES (?,1,1,?,?,'local',?,?)""",
            (cliente_id, fecha_hora.strftime("%Y-%m-%d %H:%M:%S"), tipo_pago, estado, total)
        )
        venta_id = cur.lastrowid
        
        if estado == "Pagado":
            recaudacion_total += total

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
    # Simulamos que repusieron stock si bajó de cero o muy poco, para que siempre haya algo en DB.
    # Así la demo no queda en 0 total.
    if remaining < 10:
        remaining = remaining + random.randint(50, 150)
        
    conn.execute(
        "UPDATE stock_sucursal SET cantidad_actual = ? WHERE id_producto = ? AND id_sucursal = 1",
        (remaining, prod_id)
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

print(f"\n✅ Seed completo (Datos Enriquecidos):")
print(f"   Productos creados: {len(PRODUCTOS)}")
print(f"   Clientes creados:  {len(CLIENTES)}")
print(f"   Ventas simuladas:  {ventas_count} (últimos {DAYS} días)")
print(f"   Recaudación est.:  ${recaudacion_total:,.2f}")
print(f"   Alertas generadas: {len(low_stock)} (stock bajo)")
print(f"\n🚀 Listo! Corré 'python3 seed_demo_data.py' si necesitas regenerar.")
print(f"   Abrí http://localhost:8000 para ver el dashboard y los nuevos charts.")

