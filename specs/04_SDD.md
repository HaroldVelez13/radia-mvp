# SDD - Como esta construido

## Arquitectura
```
M365 API (futuro) / data/bandeja (.eml)
  -> EML Parser (eml_parser)
  -> OCR (PyMuPDF + Docling)
  -> LLM Extractor (Ollama qwen3:8b, JSON mode) => {tipo, confianza, datos}
  -> Vector Search (Chroma) para proveedor/duplicado
  -> Rules Engine (Python puro, testeable)
  -> Vencimiento (habilmente)
  -> DB + Excel libro
  -> API FastAPI -> Next.js UI
```

## Donde interviene IA y donde NO
- IA SI: Clasificacion tipo doc, extraccion NIT/num/OC/cuenta, deteccion peticion implicita
- IA NO: Validacion NIT en maestro, duplicado, fraude cuenta vs maestro, calculo dias habiles, consecutivo radicado. Por que: determinista, auditable, evita alucinacion.

## Servicios
- api: FastAPI
- vectordb: Chroma persistente en ./chroma_db
- llm: Ollama container (opcional, puede correr en host)
- frontend: Next.js

## Seguridad
- .eml nunca sale del host
- Logs estructurados con radicado
- Excel sigue siendo compatible con Contabilidad/Juridica
