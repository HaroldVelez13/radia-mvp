# Prompts de RADIA (TNHI)

> **Ubicación en código**: `backend/app/application/services/clasificador.py` y `backend/app/application/services/extractor.py`

---

## CLASIFICACION_PROMPT

**Uso**: Slow path (Ollama qwen3.5:4b) cuando Jev-Style fast path tiene confianza < 0.8 o hay petición implícita.

**Archivo**: `backend/app/application/services/clasificador.py` (líneas 13-17)

```python
CLASIFICACION_PROMPT = """
Clasifica este documento en uno de: factura, viatico, derecho_peticion, oficio_control, queja_transporte, cotizacion, publicidad
Responde SOLO JSON: {"tipo": "...", "confianza": 0.0-1.0, "motivo": "..."}
Texto: {texto}
"""
```

### Variables de plantilla

| Variable | Descripción | Límite |
|----------|-------------|--------|
| `{texto}` | Texto del documento (asunto + cuerpo + OCR PDF si disponible) | 4000 chars |

### Tipos válidos (7)

| Tipo | Descripción |
|------|-------------|
| `factura` | Factura electrónica de proveedor |
| `viatico` | Solicitud de viáticos (formato TH-F-012) |
| `derecho_peticion` | Derecho de petición (general, copias, consulta, copias_otras) |
| `oficio_control` | Oficio de entidad de control (Contraloría, Procuraduría, Personería, Juzgado) |
| `queja_transporte` | Queja o reclamo de transporte |
| `cotizacion` | Cotización comercial |
| `publicidad` | Boletín comercial, publicidad, novedades |

### Formato de respuesta esperado

```json
{
  "tipo": "factura",
  "confianza": 0.95,
  "motivo": "Detectado NIT proveedor, número factura FE-XXXX, asunto menciona factura electrónica"
}
```

### Reglas de validación post-LLM

1. `tipo` debe ser uno de los 7 válidos → si no, `desconocido` + confianza 0.0
2. `confianza` float 0.0-1.0
3. `motivo` string explicativo

---

## EXTRACCION_FACTURA_PROMPT

**Uso**: Extracción de campos estructurados de factura (Ollama qwen3.5:4b).

**Archivo**: `backend/app/application/services/extractor.py` (líneas 8-29)

```python
EXTRACCION_FACTURA_PROMPT = """
Extrae los siguientes campos de esta factura y responde SOLO con JSON válido:
{
  "nit": "string o null",
  "numero_factura": "string o null",
  "orden_compra": "string o null",
  "cuenta_bancaria": "string o null",
  "valor_total": "number o null"
}

Reglas:
- NIT: solo dígitos, sin puntos ni guiones (ej: 900123456)
- numero_factura: formato de factura electrónica (ej: FE-3381, FV-12345)
- orden_compra: formato OC-YYYY-NNNN (ej: OC-2026-0412)
- cuenta_bancaria: número de cuenta bancaria colombiana (ej: 123456789012)
- valor_total: número decimal (ej: 1250000.00)

Si un campo no se encuentra, usa null.

Texto:
{texto}
"""
```

### Variables de plantilla

| Variable | Descripción | Límite |
|----------|-------------|--------|
| `{texto}` | Texto completo del documento (asunto + cuerpo + OCR PDF) | 8000 chars |

### Campos a extraer (5)

| Campo | Tipo | Normalización | Ejemplo |
|-------|------|---------------|---------|
| `nit` | string/null | Solo dígitos (`re.sub(r"[^\d]", "", nit)`) | `"900123456"` |
| `numero_factura` | string/null | Uppercase, strip | `"FE-3381"` |
| `orden_compra` | string/null | Formato OC-YYYY-NNNN | `"OC-2026-0412"` |
| `cuenta_bancaria` | string/null | Solo dígitos | `"123456789012"` |
| `valor_total` | number/null | Float (maneja formatos CO: 1.250.000, 1,250,000.00, 1250000,00) | `1250000.0` |

### Normalización post-LLM (Python)

```python
# En extractor.py - funciones _normalizar_*

def _normalizar_nit(nit: str | None) -> str | None:
    """Solo dígitos."""
    if not nit: return None
    return re.sub(r"[^\d]", "", str(nit)) or None

def _normalizar_numero_factura(num: str | None) -> str | None:
    """Uppercase, strip."""
    if not num: return None
    return str(num).strip().upper()

def _normalizar_orden_compra(oc: str | None) -> str | None:
    """Formato OC-YYYY-NNNN."""
    if not oc: return None
    oc = str(oc).strip().upper()
    if not re.match(r"^OC-\d{4}-\d{4}$", oc):
        return oc  # devolver tal cual si no match
    return oc

def _normalizar_cuenta_bancaria(cuenta: str | None) -> str | None:
    """Solo dígitos."""
    if not cuenta: return None
    return re.sub(r"[^\d]", "", str(cuenta)) or None

def _normalizar_valor_total(valor: str | float | int | None) -> float | None:
    """Parsea formatos colombianos: 1.250.000 | 1,250,000.00 | 1250000,00 | 1250000"""
    # Lógica compleja: detecta separador decimal por última coma/punto
    # Ver extractor.py líneas 71-110
```

### Formato de respuesta esperado del LLM

```json
{
  "nit": "900123456",
  "numero_factura": "FE-3381",
  "orden_compra": "OC-2026-0412",
  "cuenta_bancaria": "123456789012",
  "valor_total": 1250000.00
}
```

### Manejo de campos faltantes

- Si el LLM no encuentra un campo → devuelve `null`
- El normalizador Python convierte `null` → `None`
- Resultado final: dict con 5 keys, valores `str|float|None`

---

## Flujo completo de clasificación + extracción

```
EML → parse_eml() → texto (asunto + cuerpo)
                    ↓
            ┌───────┴───────┐
            ▼               ▼
      Jev-Style           (si factura)
      classify()               ↓
      probs 7 tipos      extraer_datos_factura()
            ↓                    ↓
      conf >= 0.8?         Ollama Qwen
            │                    │
      Sí ──→ RETURN          EXTRACCION_PROMPT
            │                    │
            ▼                    ▼
         tipo, conf,        normalizar_*()
         motivo, fuente     → dict 5 campos
```

---

## Notas de implementación

1. **Escaping JSON en prompts**: Usar llaves dobles `{{` y `}}` en f-strings Python para que el template tenga llaves simples en el prompt final.

2. **Límites de tokens**:
   - Clasificación: 4000 chars (asunto + cuerpo truncado)
   - Extracción: 8000 chars (incluye OCR PDF si disponible)

3. **Modelos usados**:
   - Fast path: Jev-Style-0.8B (transformers local, 0.53GB, <100ms)
   - Slow path: Ollama qwen3.5:4b (3.2GB RAM, ~2-5s)
   - Fallback: Ollama qwen3:8b (si 4b falla)

4. **Petición implícita**: Si texto contiene keywords (`solicito`, `derecho de peticion`, `requiero`, etc.) y Jev-Style no clasifica como `derecho_peticion`, fuerza slow path para validar.

5. **Trazabilidad**: Cada respuesta incluye `fuente`: `jev_style`, `ollama`, o `jev_style_fallback`.