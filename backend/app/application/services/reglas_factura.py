from app.domain.entities.documento import DatosExtraidos
from app.domain.enums import Dependencia, EstadoRadicado

def aplicar_reglas_factura(
    datos: DatosExtraidos,
    proveedor_existe: bool,
    es_duplicado: bool,
    cuenta_coincide: bool,
    correo_raro: bool
):
    # T2.2 y T2.3: implementar
    if es_duplicado:
        return Dependencia.NO_RADICAR, EstadoRadicado.DUPLICADO, "Factura ya radicada NIT+numero en libro"
    if not cuenta_coincide or correo_raro:
        return Dependencia.CLAUDIA_HERRERA, EstadoRadicado.FRAUDE, "Cuenta bancaria no coincide con maestro o correo sospechoso"
    if not proveedor_existe:
        return Dependencia.COMPRAS, EstadoRadicado.RADICADO, "Proveedor no existe en maestro"
    if not datos.orden_compra:
        return Dependencia.COMPRAS, EstadoRadicado.RADICADO, "Factura sin OC, requiere aval Compras"
    return Dependencia.CUENTAS_POR_PAGAR, EstadoRadicado.RADICADO, "Factura con OC, va a pago"
