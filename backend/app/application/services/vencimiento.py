from datetime import datetime, timedelta
# Usaremos habilmente
# from habilmente import sumar_dias_habiles

def calcular_vencimiento(fecha_recepcion: datetime, dias_habiles: int) -> datetime:
    # TODO T2.5: implementar con habilmente
    # Placeholder simple sin festivos
    return fecha_recepcion + timedelta(days=dias_habiles)

def dias_habiles_para_peticion(tipo_peticion: str) -> int:
    mapping = {
        "general": 15,
        "copias": 10,
        "consulta": 30,
        "copias+otras": 15
    }
    return mapping.get(tipo_peticion, 15)
