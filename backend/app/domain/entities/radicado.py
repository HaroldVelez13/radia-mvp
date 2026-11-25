from pydantic import BaseModel
from datetime import datetime

class Radicado(BaseModel):
    consecutivo: str  # TAC-2026-ER-00001
    fecha: datetime
    tipo: str
    proveedor_nit: str | None = None
    numero_factura: str | None = None
    dependencia: str
    estado: str
    vencimiento: datetime | None = None
