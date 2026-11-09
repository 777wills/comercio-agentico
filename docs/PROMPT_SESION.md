# Prompt de arranque de sesión

Copia y pega este texto al iniciar cada sesión nueva de Claude Code en esta carpeta. Es el mismo siempre: la sesión
sabe qué toca por `docs/ESTADO.md`.

---

```
Iniciamos una sesión de trabajo del Proyecto III.

1. Sigue el "Arranque obligatorio" de CLAUDE.md: lee docs/ESTADO.md y, en docs/PLAN.md, solo la sección de la
   sesión que toca. Consulta docs/DECISIONES.md cuando la tarea toque algo ya decidido.
2. Dime en 3–5 líneas: qué sesión toca, qué vas a entregar hoy, qué necesitas de mí (claves, créditos, archivos,
   decisiones) y cualquier riesgo de atraso frente a la fecha objetivo. Espera mi visto bueno.
3. Trabaja aplicando los principios de CLAUDE.md: simplicidad y librerías existentes, la IA primero, cuidar los
   créditos, Context7 antes de usar cualquier API de librería, y ninguna decisión nueva sin debatirla conmigo
   (pregúntame con opciones y una recomendada).
4. Si el contexto se está llenando, no sigas: haz corte limpio en el último punto estable.
5. Mientras trabajas, explícame lo que construyes y el concepto de IA que aplica (ver "Explicar y enseñar a probar"
   en CLAUDE.md).
6. Al terminar, haz el "Cierre obligatorio" de CLAUDE.md (ESTADO, casillas del PLAN, DECISIONES, borrador del informe,
   entrada nueva en privado/ENTENDER_EL_PROYECTO.md, sección nueva en docs/GUIA_PRUEBAS.md, commit y push) y dime: qué quedó hecho y por qué, cómo lo pruebo yo mismo
   sin gastar presupuesto (cada comando con su costo), qué quedó pendiente, el gasto y cuál es la siguiente sesión.

Notas para hoy (opcional): <escribe aquí cualquier novedad: tiempo disponible, cambios, problemas>
```

---

## Variantes útiles

- **Retomar una sesión cortada:** el mismo prompt sirve; `docs/ESTADO.md` indica el paso exacto donde quedó.
- **Sesión corta (poco tiempo):** en "Notas para hoy" escribe el tiempo disponible; la sesión debe proponer el
  subconjunto de tareas que cabe y cerrar limpio.
- **Cambiar una decisión:** en "Notas para hoy" escribe la decisión a revisar; la sesión la debate contigo antes de
  tocar código y registra la nueva entrada en `docs/DECISIONES.md`.
