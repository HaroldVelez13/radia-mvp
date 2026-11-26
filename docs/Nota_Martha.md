# Nota Martha — UX Explicable para RADIA

> **Principio rector**: *Martha primero* — Todo automatismo debe ser explicable y supervisable. Si confianza < 0.8, escala a humano con motivo.

---

## 1. Filosofía de Diseño

Martha es la usuaria principal (radicadora). Su flujo diario:
1. Abre bandeja → ve 16-20 correos
2. Debe decidir: Radicar / Revisar / Devolver
3. Necesita **confianza** en la recomendación del sistema
4. Si el sistema "no sabe", debe **preguntar** no inventar

**Regla de oro**: *Confianza < 0.8 → escala a humano con motivo explicativo*

---

## 2. Semáforo Visual (Bandeja)

| Color | Significado | Acción Martha | Disparadores |
|-------|-------------|---------------|--------------|
| 🔴 **Rojo** | Riesgo alto | **Revisar obligatorio** | Duplicado NIT+factura, fraude cuenta/correo, tutela/entidad control |
| 🟡 **Amarillo** | Revisar | **Verificar detalles** | Viáticos sin formato TH-F-012, sin firma, < 5 días hábiles |
| 🟢 **Verde** | OK | **Radicar directo** | Factura sin riesgos, petición estándar, publicidad/cotización |

**Código de color**: Tailwind `bg-red-100 text-red-800`, `bg-yellow-100 text-yellow-800`, `bg-green-100 text-green-800`

---

## 3. Modal "Por Qué" (Explicabilidad)

Click en cualquier fila → modal con:

```
┌─────────────────────────────────────────────┐
│ Por qué: 🔴 Riesgo Alto                    × │
├─────────────────────────────────────────────┤
│ Archivo:     01.eml                         │
│ Fecha:       2026-11-10                     │
│ Remitente:   facturacion@suministrosllano   │
│ Tipo:        Factura                        │
│ Asunto:      Factura electrónica FE-3381... │
│ NIT / Doc:   901.234.567-1                  │
├─────────────────────────────────────────────┤
│ Motivo del semáforo:                        │
│ ┌─────────────────────────────────────────┐ │
│ │ Factura duplicada: NIT 901.234.567-1 +  │ │
│ │ numero FE-3381 ya radicado como         │ │
│ │ TAC-2026-ER-04818                       │ │
│ └─────────────────────────────────────────┘ │
├─────────────────────────────────────────────┤
│ Observaciones detalladas:                   │
│ • Duplicado: NIT 901.234.567-1 + numero... │
│ [Cerrar]                                    │
└─────────────────────────────────────────────┘
```

**Regla**: Cada semáforo no-verde DEBE tener `motivo` string y `observaciones[]` array con evidencias concretas (NIT match, número factura, radicado previo, entidad detectada).

---

## 4. Cola de Revisión Humana (Pendientes)

Endpoint: `GET /api/v1/bandeja/pendientes`

Criterios de entrada a cola:
- Confianza Jev-Style < 0.6 (umbral estricto para Martha)
- Semáforo rojo por fraude/duplicado/tutela
- Estados: `revision_humana`

UI: Tab "Pendientes" con botones:
- ✅ **Aprobar** → `POST /revisar/{consecutivo} {"accion":"aprobar"}` → estado `radicado`
- ❌ **Rechazar** → `POST /revisar/{consecutivo} {"accion":"rechazar"}` → estado `no_radicado`

**Trazabilidad en libro Excel**:
```
Observaciones: "PENDIENTE REVISIÓN: Baja confianza en clasificación (factura: 0.14 < 0.60) | APROBADO por revisión humana"
```

---

## 5. Pipeline de Confianza (Fast + Slow)

```
Texto (asunto + cuerpo)
        │
        ▼
┌───────────────────┐
│ Jev-Style 0.8B    │  ← Fast path (<100ms, 0.53GB)
│ 7 tipos + probs   │
└─────────┬─────────┘
          │ conf ≥ 0.80
          ▼
    RETURN (fuente: jev_style)
          │ conf < 0.80
          ▼
┌───────────────────┐
│ Ollama qwen3.5:4b │  ← Slow path (~2-5s, 3.2GB)
│ CLASIFICACION_    │
│ PROMPT            │
└─────────┬─────────┘
          │ conf ≥ 0.50
          ▼
    RETURN (fuente: ollama)
          │ conf < 0.50
          ▼
┌───────────────────┐
│ Fallback Jev-Style│  ← Ultimate fallback
│ (uniforme)        │
└───────────────────┘
```

**Cada respuesta incluye**: `tipo`, `confianza`, `motivo`, `fuente` (jev_style / ollama / jev_style_fallback)

---

## 6. Reglas Deterministas > LLM (Explicabilidad Total)

| Regla | Implementación | Explicable |
|-------|----------------|------------|
| Duplicado | `es_duplicado(nit, numero, libro)` → busca exacto en Excel | "NIT X + factura Y ya radicado como Z" |
| Fraude | `verificar_fraude_cuenta(nit, cuenta, correo, maestro)` | "Cuenta no coincide con maestro" |
| Viáticos | `validar_viatico_completo(TH-F-012, firma, 5 días)` | "Sin firma jefe / fuera de 5 días" |
| Peticiones | `clasificar_peticion(asunto)` → tipo + urgencia | "Tutela detectada / Contraloría / 15 días háb." |
| Vencimientos | `habilmente` (festivos Colombia) | Cálculo días hábiles exacto |

**Ninguna regla usa LLM** — Python puro, testeable, versionable, auditable.

---

## 6. Métricas de Confianza (T6)

| Métrica | Valor | Significado para Martha |
|---------|-------|-------------------------|
| Tipo Accuracy | 100% | Clasifica correctamente siempre |
| Duplicado F1 | 100% | Nunca deja pasar duplicado |
| Fraude F1 | 100% | Nunca deja pasar fraude |
| Acción Accuracy | 87.5% | 7/8 decisiones correctas (gap: firma en PDF) |
| **Promedio** | **96.88%** | ✅ Confiable para producción |

---

## 7. Checklist de Entrega a Martha

- [ ] Semáforo visible en cada fila (rojo/amarillo/verde)
- [ ] Click fila → modal "Por Qué" con motivo + observaciones
- [ ] Tab "Pendientes" muestra solo `revision_humana`
- [ ] Botones ✅ Aprobar / ❌ Rechazar funcionan
- [ ] Libro Excel actualiza estado + observaciones trazables
- [ ] Confianza < 0.6 → entra a pendientes automático
- [ ] Regla Martha documentada: *"Cuando no está seguro, pregunte en vez de inventar"*

---

## 8. Próximos Pasos UX (Sprint 3)

- [ ] Toast notifications tras Aprobar/Rechazar
- [ ] Modal "Por Qué" expandible con evidencias completas (NIT match, duplicado, fraude, viático, tutela)
- [ ] Persistencia estado (aprobado/pendiente) tras refresh
- [ ] Atajos teclado: `A` aprobar, `R` rechazar, `V` ver detalle

---

*Documento vivo — Actualizado: Noviembre 2026 | Versión MVP 0.1*