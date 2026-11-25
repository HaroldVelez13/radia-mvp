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
    COMPRAS = "COMPRAS"
    CUENTAS_POR_PAGAR = "CUENTAS_POR_PAGAR"
    TALENTO_HUMANO = "TALENTO_HUMANO"
    JURIDICA = "JURIDICA"
    ATENCION_USUARIO = "ATENCION_USUARIO"
    CLAUDIA_HERRERA = "CLAUDIA_HERRERA"
    NO_RADICAR = "NO_RADICAR"

class EstadoRadicado(str, Enum):
    RADICADO = "radicado"
    NO_RADICADO = "no_radicado"
    REVISION_HUMANA = "revision_humana"
    FRAUDE = "fraude"
    DUPLICADO = "duplicado"
