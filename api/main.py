"""
FARO – FastAPI Application
===========================
Sistema de Control de Inventario y Proyección de Negocio

Run with:
    uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

Docs:  http://localhost:8000/docs
App:   http://localhost:8000
"""

from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from db.connection import run_migration, get_connection
from api.routers import ventas, productos, clientes, usuarios, sucursales, alertas
from api.routers.predicciones import router as predicciones_router
from api.routers.simulacion import router as simulacion_router

# ── Paths ─────────────────────────────────────────────────────────────────────

BASE_DIR    = Path(__file__).resolve().parent.parent
SCHEMA_PATH = BASE_DIR / "database" / "schema.sql"
FRONTEND    = BASE_DIR / "frontend"

# ── Schema migration ──────────────────────────────────────────────────────────

def _apply_schema() -> None:
    if not SCHEMA_PATH.exists():
        raise FileNotFoundError(f"Schema file not found: {SCHEMA_PATH}")
    run_migration(SCHEMA_PATH.read_text(encoding="utf-8"))
    print("✅ FARO: Base de datos verificada / migrada correctamente.")

# ── App factory ───────────────────────────────────────────────────────────────

app = FastAPI(
    title="FARO — Sistema de Gestión Ferretera",
    description=(
        "API RESTful para el sistema de control de inventario, ventas y proyección de negocio.\n\n"
        "**Módulos:** Ventas · Productos · Clientes · Alertas · Simulación What-If · Analytics"
    ),
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Startup ───────────────────────────────────────────────────────────────────

@app.on_event("startup")
def on_startup():
    _apply_schema()

# ── API Routers ───────────────────────────────────────────────────────────────

API_PREFIX = "/api/v1"

app.include_router(ventas.router,        prefix=API_PREFIX)
app.include_router(productos.router,     prefix=API_PREFIX)
app.include_router(clientes.router,      prefix=API_PREFIX)
app.include_router(usuarios.router,      prefix=API_PREFIX)
app.include_router(sucursales.router,    prefix=API_PREFIX)
app.include_router(alertas.router,       prefix=API_PREFIX)
app.include_router(simulacion_router,    prefix=API_PREFIX)
app.include_router(predicciones_router,  prefix=API_PREFIX)

# ── Time-series chart endpoint ────────────────────────────────────────────────

@app.get("/api/v1/stats/grafico", tags=["Analytics"])
def grafico_ventas(
    dias: int = Query(30, ge=7, le=365),
    id_sucursal: Optional[int] = Query(None),
):
    """
    Returns daily sales totals for the last `dias` days — used to
    render the line chart on the dashboard and projections page.
    """
    conn = get_connection()
    try:
        sc = "AND id_sucursal = ?" if id_sucursal else ""
        params = [f"-{dias} days"] + ([id_sucursal] if id_sucursal else [])

        rows = conn.execute(
            f"""SELECT
                    DATE(fecha_hora) AS dia,
                    COUNT(*) AS num_ventas,
                    COALESCE(SUM(total), 0) AS ingreso
                FROM ventas
                WHERE fecha_hora >= date('now', 'localtime', ?)
                  AND estado != 'Cancelado'
                  {sc}
                GROUP BY dia
                ORDER BY dia ASC""",
            params,
        ).fetchall()

        # Fill missing days with 0
        result = []
        today = datetime.now().date()
        data_map = {r["dia"]: {"num_ventas": r["num_ventas"], "ingreso": r["ingreso"]} for r in rows}
        for i in range(dias):
            day = (today - timedelta(days=dias - 1 - i)).strftime("%Y-%m-%d")
            entry = data_map.get(day, {"num_ventas": 0, "ingreso": 0})
            result.append({"dia": day, **entry})

        return result
    finally:
        conn.close()

# ── Static frontend ───────────────────────────────────────────────────────────

if FRONTEND.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND)), name="static")

    @app.get("/", include_in_schema=False)
    @app.get("/dashboard", include_in_schema=False)
    @app.get("/sales", include_in_schema=False)
    @app.get("/inventory", include_in_schema=False)
    @app.get("/projections", include_in_schema=False)
    def serve_frontend(path: str = ""):
        return FileResponse(str(FRONTEND / "index.html"))

# ── Health ────────────────────────────────────────────────────────────────────

@app.get("/health", tags=["Health"])
def health():
    return {"status": "ok", "version": "2.0.0"}
