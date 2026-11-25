# T3.2: Prompt clasificacion
CLASIFICACION_PROMPT = """
Clasifica este documento en uno de: factura, viatico, derecho_peticion, oficio_control, queja_transporte, cotizacion, publicidad
Responde SOLO JSON: {"tipo": "...", "confianza": 0.0-1.0, "motivo": "..."}
Texto: {texto}
"""
