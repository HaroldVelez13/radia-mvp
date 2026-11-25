from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from app.domain.enums import TipoDocumento, Dependencia, EstadoRadicado

class DocumentoEntrada(BaseModel):
    id: str
    eml_path: str
    remitente: str
    asunto: str
    fecha_recepcion: datetime
    cuerpo_texto: str
    adjuntos: List[str] = []

class DatosExtraidos(BaseModel):
    tipo: TipoDocumento
    confianza: float = Field(ge=0, le=1)
    nit_proveedor: Optional[str] = None
    numero_factura: Optional[str] = None
    orden_compra: Optional[str] = None
    cuenta_bancaria: Optional[str] = None
    formato_viatico: bool = False
    firma_jefe: bool = False
    fecha_viaje: Optional[datetime] = None
    tipo_peticion: Optional[str] = None  # general, copias, consulta, copias+otras
    es_urgente: bool = False
    motivo_urgente: Optional[str] = None

class ResultadoRadicacion(BaseModel):
    documento_id: str
    radicado: Optional[str] = None  # TAC-2026-ER-xxxxx
    dependencia: Dependencia
    estado: EstadoRadicado
    vencimiento: Optional[datetime] = None
    motivo: str  # Explicabilidad para Martha
    confianza: float
    datos: DatosExtraidos
