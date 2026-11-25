from enum import Enum

class TipoDocumento(str, Enum):
    FACTURA = "factura"
    VIATICO = "viatico"
    DERECHO_PETICION = "derecho_peticion"
    OFICIO_CONTROL = "oficio_control"
    QUEJA_TRANSPORTE = "queja_transporte"
    COTIZACION = "cotizacion"
    PUBLICIDAD = "publicidad"
    DESCONOCIDO = "desconocido"

class Dependencia(str, Enum):
    COMPRAS = "Compras"
    CUENTAS_POR_PAGAR = "Cuentas por pagar"
    TALENTO_HUMANO = "Talento Humano"
    JURIDICA = "Juridica"
    ATENCION_USUARIO = "Atencion al usuario"
    CLAUDIA_HERRERA = "Claudia Herrera"
    NO_RADICAR = "No radicar"

class EstadoRadicado(str, Enum):
    RADICADO = "radicado"
    NO_RADICADO = "no_radicado"
    REVISION_HUMANA = "revision_humana"
    FRAUDE = "fraude"
    DUPLICADO = "duplicado"
