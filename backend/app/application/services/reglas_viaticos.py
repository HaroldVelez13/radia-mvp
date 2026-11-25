from app.domain.entities.documento import DatosExtraidos
from app.domain.enums import Dependencia, EstadoRadicado
from datetime import datetime

def aplicar_reglas_viaticos(datos: DatosExtraidos, dias_habiles_para_viaje: int):
    if not datos.formato_viatico:
        return Dependencia.NO_RADICAR, EstadoRadicado.NO_RADICADO, "Sin formato TH-F-012, devolver"
    if not datos.firma_jefe:
        return Dependencia.NO_RADICAR, EstadoRadicado.NO_RADICADO, "Sin firma jefe, devolver"
    if dias_habiles_para_viaje < 5:
        return Dependencia.TALENTO_HUMANO, EstadoRadicado.RADICADO, "Viático extemporáneo (<5 dias habiles), requiere autorización especial"
    return Dependencia.TALENTO_HUMANO, EstadoRadicado.RADICADO, "Viático OK"
