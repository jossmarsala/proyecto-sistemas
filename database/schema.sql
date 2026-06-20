-- ============================================================
-- FARO – Sistema de Control de Inventario y Proyección
-- Full DDL Schema Reference  (SQLite-flavoured)
-- ============================================================

-- ------------------------------------------------------------
-- SUCURSALES
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS sucursales (
    id_sucursal     INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre          TEXT    NOT NULL,
    direccion       TEXT,
    activa          INTEGER NOT NULL DEFAULT 1       -- 0 = inactiva
);

-- Seed: pilot branch
INSERT OR IGNORE INTO sucursales (id_sucursal, nombre, direccion)
VALUES (1, 'Sucursal Principal', 'Dirección pendiente');

-- ------------------------------------------------------------
-- USUARIOS
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS usuarios (
    id_usuario      INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre          TEXT    NOT NULL,
    apellido        TEXT,
    rol             TEXT    NOT NULL CHECK(rol IN ('Vendedor','Supervisor','Gerente')),
    id_sucursal     INTEGER NOT NULL REFERENCES sucursales(id_sucursal),
    password_hash   TEXT,                           -- phase 2: JWT auth
    activo          INTEGER NOT NULL DEFAULT 1
);

-- Seed: default admin user (no password in phase 1)
INSERT OR IGNORE INTO usuarios (id_usuario, nombre, rol, id_sucursal)
VALUES (1, 'Admin', 'Gerente', 1);

-- ------------------------------------------------------------
-- PROVEEDORES
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS proveedores (
    id_proveedor            INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre                  TEXT    NOT NULL,
    contacto                TEXT,
    tiempo_reposicion_dias  INTEGER NOT NULL DEFAULT 7
);

-- ------------------------------------------------------------
-- PRODUCTOS
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS productos (
    id_producto     INTEGER PRIMARY KEY AUTOINCREMENT,
    sku             TEXT    UNIQUE,
    nombre          TEXT    NOT NULL,
    categoria       TEXT,
    precio_costo    REAL    NOT NULL DEFAULT 0.0,
    precio_venta    REAL    NOT NULL DEFAULT 0.0,
    id_proveedor    INTEGER REFERENCES proveedores(id_proveedor),
    activo          INTEGER NOT NULL DEFAULT 1,
    creado_en       TEXT    NOT NULL DEFAULT (datetime('now','localtime')),
    actualizado_en  TEXT    NOT NULL DEFAULT (datetime('now','localtime'))
);

-- ------------------------------------------------------------
-- STOCK POR SUCURSAL
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS stock_sucursal (
    id_producto             INTEGER NOT NULL REFERENCES productos(id_producto),
    id_sucursal             INTEGER NOT NULL REFERENCES sucursales(id_sucursal),
    cantidad_actual         REAL    NOT NULL DEFAULT 0.0,
    stock_minimo_seguridad  REAL    NOT NULL DEFAULT 0.0,
    PRIMARY KEY (id_producto, id_sucursal)
);

-- ------------------------------------------------------------
-- CLIENTES
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS clientes (
    id_cliente              INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre                  TEXT    NOT NULL,
    apellido                TEXT,
    cuit_dni                TEXT,
    razon_social            TEXT,
    telefono                TEXT,
    notas                   TEXT,
    saldo_cuenta_corriente  REAL    NOT NULL DEFAULT 0.0,
    limite_credito          REAL    NOT NULL DEFAULT 0.0,
    creado_en               TEXT    NOT NULL DEFAULT (datetime('now','localtime'))
);

-- ------------------------------------------------------------
-- VENTAS
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS ventas (
    id_venta        INTEGER PRIMARY KEY AUTOINCREMENT,
    id_cliente      INTEGER REFERENCES clientes(id_cliente),
    id_usuario      INTEGER NOT NULL REFERENCES usuarios(id_usuario),
    id_sucursal     INTEGER NOT NULL REFERENCES sucursales(id_sucursal),
    fecha_hora      TEXT    NOT NULL DEFAULT (datetime('now','localtime')),
    tipo_pago       TEXT    NOT NULL DEFAULT 'Efectivo'
                            CHECK(tipo_pago IN ('Efectivo','Tarjeta','Cuenta Corriente')),
    tipo_venta      TEXT    NOT NULL DEFAULT 'local'
                            CHECK(tipo_venta IN ('local','pedido')),
    estado          TEXT    NOT NULL DEFAULT 'Pagado'
                            CHECK(estado IN ('Pagado','A cobrar / parcial','Cancelado')),
    referencia      TEXT,
    total           REAL    NOT NULL DEFAULT 0.0
);

-- ------------------------------------------------------------
-- DETALLE VENTA
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS detalle_venta (
    id_detalle                  INTEGER PRIMARY KEY AUTOINCREMENT,
    id_venta                    INTEGER NOT NULL REFERENCES ventas(id_venta) ON DELETE CASCADE,
    id_producto                 INTEGER NOT NULL REFERENCES productos(id_producto),
    cantidad                    REAL    NOT NULL,
    precio_unitario_historico   REAL    NOT NULL,   -- snapshot at time of sale
    subtotal                    REAL    NOT NULL
);

-- ------------------------------------------------------------
-- CUENTA CORRIENTE  (append-only ledger)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS cuenta_corriente (
    id_movimiento       INTEGER PRIMARY KEY AUTOINCREMENT,
    id_cliente          INTEGER NOT NULL REFERENCES clientes(id_cliente),
    id_venta            INTEGER REFERENCES ventas(id_venta),
    tipo                TEXT    NOT NULL CHECK(tipo IN ('cargo','pago')),
    monto               REAL    NOT NULL,
    saldo_resultante    REAL    NOT NULL,
    notas               TEXT,
    fecha_hora          TEXT    NOT NULL DEFAULT (datetime('now','localtime'))
);

-- ------------------------------------------------------------
-- ALERTAS
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS alertas (
    id_alerta       INTEGER PRIMARY KEY AUTOINCREMENT,
    tipo            TEXT    NOT NULL CHECK(tipo IN ('stock_minimo','limite_credito')),
    id_referencia   INTEGER NOT NULL,   -- id_producto or id_cliente depending on type
    id_sucursal     INTEGER REFERENCES sucursales(id_sucursal),
    mensaje         TEXT    NOT NULL,
    activa          INTEGER NOT NULL DEFAULT 1,
    fecha_hora      TEXT    NOT NULL DEFAULT (datetime('now','localtime'))
);
