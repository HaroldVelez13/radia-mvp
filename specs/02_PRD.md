# PRD - Que hace RADIA

## MVP Features
1. Ingesta: Lee 16 .eml de data/bandeja con adjuntos PDF nativo/escaneado. Si un correo trae 2 facturas => 2 radicados.
2. Clasificacion: 7 tipos: factura, viatico, derecho_peticion, oficio_control, queja_transporte, cotizacion, publicidad
3. Extraccion: NIT, numero factura, OC, cuenta bancaria, formato TH-F-012, firma jefe, fecha viaje, tipo peticion
4. Reglas Factura: maestro proveedor por NIT, con/sin OC, duplicado NIT+numero, fraude cuenta vs maestro
5. Reglas Viaticos: TH-F-012 + firma jefe + 5 dias habiles antes viaje, si no -> extemporanea
6. Reglas Peticion: siempre Juridica, plazo 10/15/30 dias habiles desde dia habil siguiente, sin sab/dom/festivos. Urgente si Contraloria/Procuraduria/Personeria/Juzgado o amenaza tutela.
7. Libro: Continuar consecutivo TAC-2026-ER-xxxxx y escribir Excel
8. UI: Login basico, lista bandeja con semaforo confianza, modal Por que, y vista vencimientos

## No MVP (mejoras)
- Conexion real M365/Gmail API
- MCP Server para Claudia
- Envio de correos reales
