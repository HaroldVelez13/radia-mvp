from pydantic import BaseModel

class RadicacionResponse(BaseModel):
    radicado: str
    dependencia: str
    estado: str
    motivo: str
