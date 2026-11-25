# TASKS - Breakdown para OpenCode (tareas pequenas verificables)

## FASE 0 - Bootstrap (Hoy)
- [ ] T0.1: Crear docker-compose.yml con api, frontend, ollama, chroma volumen. Verificacion: `docker compose config` OK
- [ ] T0.2: Backend scaffold FastAPI con /health. Verificacion: `curl localhost:8000/health -> 200`
- [ ] T0.3: Frontend scaffold Next.js con /login y /dashboard. Verificacion: `npm run dev` muestra login

## FASE 1 - Ingesta
- [ ] T1.1: EML parser lee 1 .eml de data/bandeja y lista remitente/asunto/adjuntos. Verificacion: test con 1 archivo
- [ ] T1.2: EML parser maneja multiples docs por correo (2 facturas en mismo correo => 2 items)
- [ ] T1.3: OCR Docling extrae texto de PDF nativo y escaneado

## FASE 2 - Dominio y Reglas
- [ ] T2.1: Modelo Documento, Proveedor, Radicado (Pydantic)
- [ ] T2.2: Regla duplicado factura: NIT+numero en libro
- [ ] T2.3: Regla fraude cuenta
- [ ] T2.4: Regla viaticos formato y firma
- [ ] T2.5: Regla peticion plazo con habilmente (festivos Colombia)
- [ ] T2.6: Tests unitarios para cada regla

## FASE 3 - IA Local
- [ ] T3.1: Ollama client qwen3:8b con JSON mode
- [ ] T3.2: Prompt clasificacion 7 tipos con confianza
- [ ] T3.3: Prompt extraccion datos factura
- [ ] T3.4: Vector DB Chroma para proveedores y duplicados

## FASE 4 - Libro y API
- [ ] T4.1: Generar consecutivo TAC-2026-ER-xxxxx
- [ ] T4.2: Escribir en Excel libro con openpyxl
- [ ] T4.3: API POST /bandeja/procesar y GET /radicados

## FASE 5 - Frontend
- [ ] T5.1: Login basico martha/TAC2026
- [ ] T5.2: Tabla bandeja con semaforo confianza
- [ ] T5.3: Modal Por que con trazabilidad
- [ ] T5.4: Vista vencimientos semanal

## FASE 6 - Medicion
- [ ] T6.1: Comparar contra material/4-para-medirte y calcular precision
- [ ] T6.2: README con instrucciones desde cero + doc arquitectura 2 paginas
