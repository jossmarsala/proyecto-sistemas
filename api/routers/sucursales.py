from fastapi import APIRouter
from db.connection import get_connection

router = APIRouter(prefix="/sucursales", tags=["Sucursales"])


@router.get("")
def listar():
    """Lista todas las sucursales activas."""
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT * FROM sucursales WHERE activa = 1 ORDER BY nombre"
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()
