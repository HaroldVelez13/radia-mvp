# Bitácora RADIA (TNHI) - MVP

> **Propósito**: Registro de decisiones, fallos, fixes y aprendizajes para onboarding futuro y auditoría.

---

## Resumen Ejecutivo

**Proyecto**: RADIA - Radicación Asistida para Terminales Andinas Carga (TNHI)
**Periodo**: Noviembre 2026
**Estado**: MVP Operativo (3 servicios Docker, 93 tests, precisión 96.9%)

---

## Cronología de Hitos

| Fecha | Hito | Commit |
|-------|------|--------|
| 2026-11-25 | Docker Compose up + Chroma verificado | `cc8685b` |
| 2026-11-25 | Jev-Style local fallback (transformers) | `c1794b6` |
| 2026-11-25 | Consecutivo + API bandeja (procesar EML → Excel) | `38aaa9d` |
| 2026-11-25 | UI Bandeja semáforo + Vencimientos Claudia | `2ea7d6a` |
| 2026-11-25 | Medición T6 (96.9%) + Arquitectura docs | `65d9f92` |
| 2026-11-26 | Docs CLAUDE + Prompts + Bitácora | *actual* |

---

## Lo que se pidió al agente (por fases)

### Fase 1: Infraestructura Base
- ✅ Verificar Docker Compose up (4 servicios: api, ollama, frontend, jev-style)
- ✅ Chroma import OK dentro del contenedor api
- ✅ Tests pasando (93/93 sin llm)

### Fase 2: Jev-Style Local Fallback
- ✅ Reemplazar servicio externo `ghcr.io/radia-project/jev-style-classifier` por modelo local `Jev-Style-0.8B-Decision-v3` via transformers
- ✅ Fast path: Jev-Style (<100ms) → Slow path: Ollama qwen3.5:4b
- ✅ Cache en volumen `./models` (`TRANSFORMERS_CACHE=/app/models`)
- ✅ 7 tipos con probabilidades, fallback a uniforme si falla todo

### Fase 3: Consecutivo + Libro Excel + API Bandeja
- ✅ `generar_consecutivo()`: lee max ER en Excel → `TAC-2026-ER-xxxxx` (5 dígitos)
- ✅ `escribir_libro()`: append fila en hoja "Radicación 2026" (12 columnas)
- ✅ `POST /api/v1/bandeja/procesar`: parsea 1 EML → clasifica → consecutivo → escribe libro
- ✅ `GET /api/v1/bandeja/analisis`: 18 EMLs con semáforo (rojo/amarillo/verde) + modal "Por Qué"

### Fase 4: UI Martha (Bandeja) + UI Claudia (Vencimientos)
- ✅ `/bandeja`: tabla con semáforo (🔴 riesgo duplicado/fraude/tutela, 🟡 viáticos incompleto, 🟢 OK)
- ✅ Click fila → modal "Por Qué" con motivo detallado
- ✅ `/vencimientos`: peticiones ordenadas por urgencia (crítica/alta/urgente/normal) + días hábiles restantes
- ✅ Tailwind only, sin librerías UI externas

### Fase 5: Medición T6 + Arquitectura
- ✅ `medir.py`: procesa 16 EMLs vs `esperado-parcial.csv` (8 ground truth)
- ✅ Métricas: Tipo 100%, Duplicado 100%, Fraude 100%, Acción 87.5% → **Promedio 96.9%**
- ✅ `docs/arquitectura.md`: 2-3 páginas con costos, ahorro 3h/día, deuda técnica, roadmap

### Fase 6: Documentación IA
- ✅ `CLAUDE.md`: reglas opencode (DDD, docker only, outcome first)
- ✅ `docs/prompts.md`: CLASIFICACION_PROMPT + EXTRACCION_FACTURA_PROMPT
- ✅ `docs/bitacora.md`: este archivo

---

## Dónde falló y por qué

### 1. **Jev-Style image missing** (Fase 2)
**Problema**: `ghcr.io/radia-project/jev-style-classifier:latest` no existe / 403 denied
```
Error: denied: denied
```
**Causa**: Imagen privada o no publicada. El docker-compose.yml la referenciaba como servicio externo.
**Fix**: Comentado el servicio jev-style en docker-compose.yml + implementado fallback local en `jev_style_client.py` usando `transformers` + `torch` (0.53GB RAM). Ahora no hay dependencia externa.

### 2. **cd hanging 20m** (Fase 1-2)
**Problema**: `docker compose up -d --build` se colgaba en `npm install` (frontend) y descarga de `torch` + CUDA wheels (api)
```
Downloading torch-2.4.0-cp312-cp312-manylinux1_x86_64.whl (797.2 MB)
Downloading nvidia_cudnn_cu12-9.1.0.70-py3-none-manylinux2014_x86_64.whl (664.8 MB)
```
**Causa**: Wheels CUDA grandes (2+ GB total). Sin buildx/cache, cada rebuild re-descarga.
**Mitigación**: 
- `docker compose up -d --build api` separado de frontend
- Volumen `models:/app/models` para cache transformers
- `pip install --no-cache-dir` en Dockerfile (aunque descarga wheels igual)
- **Decisión**: Aceptar build lento inicial; subsequent rebuilds usan cache layers.

### 3. **Postgres mismatch talonary** (Fase 1)
**Problema**: Puerto 5432 y 8000 ya ocupados por contenedores `talonary_backend-*` de otro proyecto
```
Bind for 0.0.0.0:8000 failed: port is already allocated
Bind for 0.0.0.0:11434 failed: address already in use (ollama snap en host)
```
**Causa**: Múltiples proyectos Docker en mismo host. Ollama snap corriendo en host (puerto 11434).
**Fix**:
- `docker rm -f` contenedores conflictivos (`radia-api`, `radia-frontend`, `talonary_backend-backend-1`)
- Ollama puerto mapeado a `11435:11434` en docker-compose.yml (evita colisión con snap host)
- `kill` proceso Next.js en puerto 3000 (`ss -tulpn | grep 3000`)

### 4. **NIT no extraído de EML** (Fase 3-5)
**Problema**: Parser `eml_parser` no saca NIT del asunto/cuerpo → `nit=None` → no se puede verificar duplicado/fraude
**Causa**: NITs en PDF adjunto, no en texto plano del email.
**Fix temporal**: Mapeo dominio remitente → NIT en `parser.py` (líneas 90-110):
```python
sender_to_nit = {
    "suministrosllano.example": "901.234.567-1",
    "ferrela13.example": "830.456.789-2",
    ...
}
```
**Deuda DT-01**: Integrar Docling/PyMuPDF para OCR de PDFs adjuntos y extraer NIT/cuenta/firma reales.

### 5. **Viáticos sin firma detectada** (Fase 5)
**Problema**: `07.eml` (viáticos Cartagena) → parser dice "Radicar" pero esperado "Devolver" (sin firma jefe)
**Causa**: Parser solo ve texto plano del email; firma está en PDF adjunto.
**Impacto**: Métrica Acción Accuracy 87.5% (7/8) en lugar de 100%.
**Fix**: Documentado como gap conocido en arquitectura.md. Requiere DT-01 (PDF OCR).

### 6. **Fecha con timezone en openpyxl** (Fase 3)
**Problema**: `TypeError: Excel does not support timezones in datetimes`
**Causa**: `eml_parser` devuelve `datetime` con `tzinfo` → openpyxl rechaza.
**Fix**: `strip_tz()` helper en `libro.py` convierte a naive datetime antes de `ws.append()`.

---

## Qué se decidió sin consultar al agente (decisiones de arquitectura)

### Modelos LLM para 16GB RAM
| Modelo | Decisión | Justificación |
|--------|----------|---------------|
| **Principal** | `qwen3.5:4b` (Ollama, 4-bit, ~3GB) | Cabe con margen; qwen3:8b (4.7GB) deja <2GB para OS+embeddings → OOM risk |
| **Fallback** | `qwen3:8b` (Ollama) | Solo si 4b falla; se carga on-demand |
| **Fast path** | `Jev-Style-0.8B` (transformers local, 0.53GB) | <100ms, 7-tipos, sin red; evita latencia Ollama en clasificación simple |
| **Embeddings** | `paraphrase-multilingual-MiniLM-L12-v2` (120MB) | Multilingüe, cosine similarity, probado en Chroma |

**Total estimado**: ~6 GB RAM (4b + Jev + embeddings + Python + OS) → **Safe margin 10GB**

### Jev-Style: Local vs Externo
- **Decisión**: Local (transformers) como fast path, NO servicio externo
- **Por qué**: 
  - Imagen GHCR no disponible / privada
  - Latencia red + cold start inaceptable para clasificación por email
  - 0.53GB RAM es trivial en 16GB
  - Fallback natural a Ollama si falla

### Libro Excel como Source of Truth
- **Decisión**: NO migrar a PostgreSQL aún. Excel openpyxl = source of truth
- **Por qué**:
  - Compatibilidad TAC legado (Martha/Claudia ya usan Excel)
  - Auditoría humana trivial (abrir archivo)
  - Migración riesgosa para MVP; programada Sprint 4

### Docker Compose: 3 Servicios
| Servicio | Puerto | Imagen/Build |
|----------|--------|--------------|
| `api` | 8000 | `./backend` (build) |
| `ollama` | 11435→11434 | `ollama/ollama:latest` |
| `frontend` | 3000 | `./frontend` (build) |

**Comentado**: `jev-style` (externo, no disponible)

### Puerto Ollama: 11435 externo
- **Host**: 11435 → **Container**: 11434
- **Por qué**: Evita conflicto con Ollama snap en host (puerto 11434)
- **Interno**: API usa `http://ollama:11434` (DNS Docker)

### ChromaDB: Persistente en volumen
- `./chroma_db:/app/chroma_db` (bind mount)
- Colecciones: `proveedores` + `radicados`
- Embeddings: MiniLM-L12-v2 (cosine)

### Tests: Solo reglas deterministas
- `pytest -k "not llm"` → 93 tests passing
- Tests LLM excluidos (no deterministas, requieren modelo cargado)
- Fixtures: `libro_path`, `maestro_path` en `conftest.py`

---

## Métricas Finales (T6)

```
docker compose exec api python app/scripts/medir.py
```

| Métrica | Valor | Ground Truth |
|---------|-------|--------------|
| Tipo Accuracy | 100% | 8/8 |
| Duplicado F1 | 100% | 0 FP, 0 FN |
| Fraude F1 | 100% | 0 FP, 0 FN |
| Acción Accuracy | 87.5% | 7/8 (07.eml gap) |
| **Promedio Ponderado** | **96.9%** | ✅ >80% |

---

## Próximos Pasos Priorizados

| Sprint | Objetivo | Tareas Clave |
|--------|----------|--------------|
| **1** | PDF OCR | Docling → extraer NIT/cuenta/firma de adjuntos → conectar a `verificar_fraude_cuenta` y `validar_viatico_completo` |
| **2** | Chroma Sync | `ChromaClient.initialize()` al escribir libro → `/buscar/proveedor` endpoint → deduplicación semántica |
| **3** | Frontend UX | Botones ✅/⚠️/❌ en bandeja → modal "Por Qué" expandible → toast notifications |
| **4** | Hardening | PostgreSQL + Auth JWT + Prometheus/Grafana + Backup automático |

---

## Comandos de Referencia Rápida

```bash
# Build + up
docker compose up -d --build

# Solo API rebuild
docker compose up -d --build api

# Tests
docker compose exec api python -m pytest app/tests/ -v -k "not llm"

# Medición T6
docker compose exec api python app/scripts/medir.py

# Logs
docker compose logs -f api

# Ver libros
docker compose exec api python -c "
import openpyxl
wb = openpyxl.load_workbook('/data/libro/libro-radicacion-2026.xlsx')
ws = wb['Radicación 2026']
for row in ws.iter_rows(min_row=ws.max_row-2, max_row=ws.max_row, values_only=True):
    print(row)
"

# Limpiar todo
docker compose down -v
docker system prune -f
```

---

## Contactos / Ownership

| Área | Responsable |
|------|-------------|
| Backend API / Reglas | Equipo RADIA |
| Frontend Martha/Claudia | Equipo RADIA |
| Infra Docker / Ollama | DevOps |
| Datos (maestro, libro, bandeja) | TNHI - Terminales Andinas Carga |

---

*Última actualización: 2026-11-26 | Commit: `docs: claude prompts bitacora`*