from fastapi import APIRouter
from typing import List

from models import UsuarioResponse
from db.connection import get_connection

router = APIRouter(prefix="/usuarios", tags=["Usuarios"])


@router.get("", response_model=List[UsuarioResponse])
def listar():
    """Lista todos los usuarios activos del sistema."""
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT * FROM usuarios WHERE activo = 1 ORDER BY nombre"
        ).fetchall()
        return [
            UsuarioResponse(
                id_usuario=r["id_usuario"],
                nombre=r["nombre"],
                apellido=r["apellido"],
                rol=r["rol"],
                id_sucursal=r["id_sucursal"],
                activo=r["activo"],
            )
            for r in rows
        ]
    finally:
        conn.close()
