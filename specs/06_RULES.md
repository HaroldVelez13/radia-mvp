# RULES para OpenCode

1. Nunca escribas codigo sin leer specs/00_constitution.md y specs/03_SPEC.md
2. Una tarea = un PR pequeno, verificable, con test si es regla
3. No uses APIs externas. Todo local.
4. LLM solo JSON, nunca texto libre
5. Reglas de negocio siempre Python puro, no LLM
6. Antes de implementar, pregunta: ¿esto lo puede explicar Martha?
7. Si confianza <0.8 => revision humana con motivo
8. Cada commit: `feat:`, `fix:`, `test:` + descripcion
9. No hagas tareas complejas de un solo prompt. Divide.
10. Al final de cada tarea, escribe en specs/VERIFICACION.md como se probo
