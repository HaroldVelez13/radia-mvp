# RADIA - Radicacion Asistida con IA

MVP local para TNHI - Terminales Andinas Carga

## Stack
- Backend: FastAPI Python 3.12 clean architecture (domain/application/infrastructure/api)
- IA Local: Ollama qwen3:8b + ChromaDB + paraphrase-multilingual-MiniLM
- Festivos: habilmente
- Frontend: Next.js 14 App Router + Tailwind + shadcn/ui
- Docker Compose

## Como correr desde cero
```bash
git clone <repo> radia-mvp
cd radia-mvp
cp .env.example .env
docker compose up -d ollama
docker exec radia-ollama ollama pull qwen3:8b
docker compose up --build
# API: http://localhost:8000/docs
# Frontend: http://localhost:3000
# Login: martha / TAC2026
```

## Estructura
- /specs: Spec-Driven Development (constitution, BRD, PRD, SPEC, SDD, TASKS, RULES)
- /backend: FastAPI clean code
- /frontend: Next.js
- /data: bandeja .eml, maestro, libro (no se sube)

## Tareas para OpenCode
Ver specs/05_TASKS.md - tareas pequenas verificables. Una a la vez.

## Principios
- Martha primero, explicabilidad
- Sabe cuando no sabe (confianza <0.8 -> revision humana)
- Reglas deterministas > LLM
- 100% local, sin APIs externas
