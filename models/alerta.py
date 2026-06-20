from __future__ import annotations
from pydantic import BaseModel
from typing import Optional


class AlertaResponse(BaseModel):
    id_alerta: int
    tipo: str             # 'stock_minimo' | 'limite_credito'
    id_referencia: int
    id_sucursal: Optional[int]
    mensaje: str
    activa: int
    fecha_hora: str

    model_config = {"from_attributes": True}
