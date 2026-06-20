from __future__ import annotations
from pydantic import BaseModel, Field
from typing import Optional


class UsuarioResponse(BaseModel):
    id_usuario: int
    nombre: str
    apellido: Optional[str]
    rol: str
    id_sucursal: int
    activo: int

    model_config = {"from_attributes": True}
