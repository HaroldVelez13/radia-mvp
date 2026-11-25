# RADIA - Constitution

## Principios no negociables
1. **Martha primero:** Todo lo que haga el sistema debe ser explicable. No autonomia total, human-in-the-loop.
2. **Sabe cuando no sabe:** Si confianza < 0.8, pasa a revision humana con motivo.
3. **Reglas deterministas > LLM:** LLM solo clasifica y extrae. Reglas de negocio (duplicado, fraude, OC, firma, vencimiento) son codigo Python testeable.
4. **Privacidad:** 100% local. Sin APIs externas. .eml nunca sale del contenedor.
5. **Clean Code:** SOLID, DDD, vertical slices, tests para reglas.
6. **MVP rapido pero trazable:** Logs estructurados, libro Excel es source of truth compatible con TAC.
7. **Costo:** Debe correr en laptop 16GB RAM.

## Stack permitido MVP
- Backend: Python 3.12, FastAPI, Pydantic v2, Powertools
- Parser: eml_parser, PyMuPDF, Docling
- LLM: Ollama qwen3:8b (fallback qwen3:4b)
- Vector: ChromaDB + paraphrase-multilingual-MiniLM-L12-v2
- Festivos: habilmente
- DB: Postgres (prod) / SQLite (MVP) + Excel openpyxl
- Frontend: Next.js 14 App Router, Tailwind, shadcn/ui
- Infra: Docker Compose
