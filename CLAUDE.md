# CLAUDE.md - Reglas de trabajo para RADIA (TNHI)

## Principios no negociables

1. **DDD estricto**: Capas separadas (domain, application, infrastructure). No imports cruzados hacia arriba.
2. **Docker only**: Todo corre en contenedores. `docker compose exec api` para comandos. No `pip install` local.
3. **Outcome first**: Definir qué se espera (test, endpoint, métrica) antes de escribir código.
4. **Reglas > LLM**: Lógica de negocio en Python puro (testeable). LLM solo para clasificación/extracción.
5. **Privacidad 100% local**: Cero APIs externas. Modelos en Ollama/transformers locales.
6. **Martha primero**: UX explicable. Si confianza < 0.8 → escala a humano con motivo.
7. **Laptop 16GB**: Stack debe caber (Qwen3.5 3GB + Jev 0.53GB + embeddings 0.12GB).

---

## Stack y Versiones

| Componente | Versión | Notas |
|------------|---------|-------|
| Python | 3.12 | slim |
| FastAPI | 0.115 | |
| Ollama | latest | qwen3.5:4b (principal), qwen3:8b (fallback) |
| Jev-Style | 0.8B | transformers local, 0.53GB |
| ChromaDB | 0.5.5 | persistente en ./chroma_db |
| Embeddings | MiniLM-L12-v2 | sentence-transformers |
| Frontend | Next.js 14 | App Router + Tailwind |

---

## Comandos canónicos

```bash
# Levantar todo
docker compose up -d --build

# Tests (93 pasando)
docker compose exec api python -m pytest app/tests/ -v -k "not llm"

# Medición T6 (precision > 0.8)
docker compose exec api python app/scripts/medir.py

# API endpoints
curl http://localhost:8000/api/v1/bandeja/analisis
curl http://localhost:8000/api/v1/vencimientos/
curl -X POST http://localhost:8000/api/v1/bandeja/procesar

# Logs
docker compose logs -f api
```

---

## Estructura de capas (DDD)

```
app/
├── domain/           # Entidades, enums, reglas puras (sin deps externas)
├── application/      # Casos de uso, servicios de aplicación
│   ├── services/     # Reglas de negocio (reglas_factura, reglas_peticion, etc.)
│   └── use_cases/    # Orquestación (procesar_bandeja)
├── infrastructure/   # Adaptadores externos
│   ├── llm/          # ollama_client, jev_style_client
│   ├── vector/       # chroma_client
│   ├── excel/        # libro.py (openpyxl)
│   ├── eml/          # parser.py
│   └── db/           # models, session
├── api/              # FastAPI routes, deps
└── scripts/          # medir.py (evaluación)
```

---

## Reglas de código

- **Imports**: Relativos dentro de `app.*`. No `sys.path` hacks en prod.
- **Tipado**: Type hints obligatorios en funciones públicas.
- **Tests**: `pytest` con fixtures en `conftest.py`. 93 tests pasando (`-k "not llm"`).
- **Config**: `.env.example` → variables de entorno. No hardcodear URLs.
- **Volúmenes Docker**: `./data:/data`, `./backend:/app`, `./chroma_db:/app/chroma_db`, `models:/app/models`

---

## Modelos LLM (16GB RAM)

| Modelo | Tamaño | Uso | Memoria |
|--------|--------|-----|---------|
| qwen3.5:4b (Ollama) | ~3 GB | Principal: clasificación + extracción | 3.2 GB |
| qwen3:8b (Ollama) | ~4.7 GB | Fallback si 4b falla | 3.2 GB |
| Jev-Style-0.8B | 0.53 GB | Fast path: 7-tipos <100ms | 0.53 GB |
| MiniLM-L12-v2 | 120 MB | Embeddings Chroma | 120 MB |

**Decisión**: Qwen3.5 4b (no 8b) como principal para dejar margen. Jev-Style local evita red.

---

## Flujo de clasificación (Fast + Slow)

```
texto → Jev-Style (0.53GB) → probabilidades 7 tipos
         ↓ conf >= 0.8
      RETURN (fuente: jev_style)
         ↓ conf < 0.8 O petición implícita
      Ollama qwen3.5:4b (CLASIFICACION_PROMPT)
         ↓ conf >= 0.5
      RETURN (fuente: ollama)
         ↓ conf < 0.5
      Fallback a Jev-Style (fuente: jev_style_fallback)
```

---

## Endpoints clave

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/api/v1/bandeja/analisis` | 18 EMLs con semáforo (rojo/amarillo/verde) |
| POST | `/api/v1/bandeja/procesar` | Procesa 1 EML → consecutivo + libro |
| GET | `/api/v1/vencimientos/` | Peticiones ordenadas por urgencia (Claudia) |
| GET | `/api/v1/health` | Health check |

---

## Métricas T6 (medir.py)

```bash
docker compose exec api python app/scripts/medir.py
```

**Objetivo**: Precisión ponderada > 80%
- Tipo Accuracy: 100%
- Duplicado F1: 100%
- Fraude F1: 100%
- Acción Accuracy: 87.5%
- **Promedio: 96.9% ✅**

---

## Deuda técnica conocida

- DT-01: PDF OCR (Docling) para NIT/cuenta/firma en adjuntos
- DT-02: Chroma sync automático tras escribir libro
- DT-03: Jev-Style no está en HF público (requiere auth/mirror)
- DT-04: Auth frontend hardcoded
- DT-05: Tests E2E parse→clasificar→reglas→libro

---

## Qué NO hacer

- ❌ `pip install` fuera de Dockerfile
- ❌ Importar `infrastructure` desde `domain`
- ❌ Llamar APIs externas (OpenAI, HF inference, etc.)
- ❌ Hardcodear `http://localhost:11434` (usar `http://ollama:11434`)
- ❌ Cambiar `data/libro/libro-radicacion-2026.xlsx` sin `git restore` antes de commit
- ❌ Ejecutar tests sin `docker compose exec api`