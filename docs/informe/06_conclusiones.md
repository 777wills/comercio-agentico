# 6. Conclusiones

## 6.1 Respuesta a los objetivos

**Arquitectura (objetivo 1).** Un agente de compras puede operar sobre proveedores de madurez digital heterogénea
con un único contrato de fuente: un servidor MCP, páginas con schema.org, páginas planas, documentos PDF y mensajes
entran por la misma interfaz y producen ofertas con el mismo esquema y procedencia completa, como se observó en
las 90 ejecuciones de cada modelo en E3. La separación de planos resultó
ser, además de una decisión de diseño, la defensa más eficaz medida.

**Corpus (objetivo 2).** El corpus sintético, con verdad conocida por construcción, hizo posible medir lo que un
corpus real no permite: la exactitud de cada campo, el éxito de cada ataque por programa y la respuesta correcta en
las tareas sin respuesta. El corpus real de tres tiendas colombianas confirmó que el agente transfiere a páginas de
producción (19 de 20 tareas correctas en E1) sin publicar copias de contenido protegido.

**Evidencia (objetivo 3).** Los tres experimentos responden sus preguntas con intervalos de confianza:

- **La seguridad no costó utilidad.** Sin defensas, la suite de 20 cargas vulneró al agente con DeepSeek V4.1 Flash
  en el 11,7 % de las ejecuciones atacadas (7 de 60; IC 95 %: 5,8–22,2). Con la separación de planos, y con las
  capas que se le suman, el éxito del ataque fue 0 de 60 (IC 95 %: 0–6,0), con una utilidad benigna entre 93,3 % y
  96,7 % en las cuatro configuraciones. Un ataque adaptativo diseñado contra la arquitectura, con la carga en el
  título del producto, tuvo éxito en 3 de 3 ejecuciones sin defensas y en 0 de 9 con ellas.
- **La verificación protege cuando hay errores.** Con los errores naturales de la extracción, la segunda lectura no
  cambió ninguna decisión, pero separó la calidad de las ofertas: la exactitud de los campos fue de 97,2 % en las
  ofertas verificadas frente a 76,0 % en las no verificadas en el corpus sintético, y de 90,5 % frente a 42,2 % en
  el real. Con fallas sembradas en la primera extracción, la verificación detectó 249 de 249 y, con la política de
  abstención, ninguna de las 119 fallas que favorecían a una oferta llegó a la recomendación.
- **El modelo más barato basta para la tarea medida.** DeepSeek V4.1 Flash y Claude Haiku 5.5 obtuvieron una tasa
  de éxito equivalente dentro del ruido (88,9 % y 90,0 %), a US$0,015 y US$0,017 por tarea. La regla de parada,
  fijada antes de medir, detuvo el escalamiento en el segundo modelo y evitó gastar en cuatro modelos más caros sin
  evidencia de que mejoraran el resultado.

**Preparación de las fuentes (objetivo 4).** Se cumplió de forma parcial. El corpus sintético materializa cinco
niveles de madurez digital y el agente opera sobre todos ellos, pero la relación entre la preparación declarada de
una fuente real y el desempeño del agente sobre ella, prevista para el experimento E4, queda propuesta.

## 6.2 Aportes

1. Una arquitectura de agente de compras con procedencia sellada por oferta y separación de planos, con evidencia
   de que la separación de planos elimina el éxito medible de la suite de inyección sin pérdida de utilidad.
2. Un banco de evaluación reproducible por comando único: dos corpus, 80 tareas con verdad conocida y una suite
   pública de 20 cargas de inyección con objetivos comerciales y predicados de éxito evaluados por programa.
3. Una evaluación de la verificación por ruta independiente que distingue su valor como filtro de decisiones (nulo
   con errores naturales, total con errores sembrados) de su valor como señal de calidad por oferta.
4. CotIA, un producto mínimo viable en producción, con las defensas medidas activas por defecto, la clave del
   visitante fuera de toda persistencia y un catálogo de tiendas reales admitidas con un criterio explícito sobre sus
   términos de uso.

## 6.3 Limitaciones

- **Un dominio y pocas tiendas reales.** Los resultados se obtuvieron en electrónica de consumo, con tres tiendas en
  el corpus real; la transferencia a otros dominios no se midió.
- **Suite de ataques propia y en un idioma.** Las 20 cargas están en español y no emplean técnicas de evasión; un
  atacante con acceso a la arquitectura puede diseñar cargas que la suite no cubre. El segundo modelo evaluado bajo
  ataque (Claude Haiku 5.5) no fue vulnerado ni sin defensas, de modo que la suite no discrimina entre defensas en
  ese modelo.
- **Muestras pequeñas.** Treinta tareas con tres repeticiones dan intervalos de unos ±6 puntos en la tasa de éxito;
  diferencias reales menores que el ruido no se detectan.
- **Verificación limitada a la ganadora.** La segunda lectura solo verifica la oferta recomendada; un error que
  saque de la comparación a la oferta correcta no se recupera.
- **Dos de seis modelos medidos.** La regla de parada no evalúa ventajas de los modelos más caros que la tasa de
  éxito y la abstención no capturan.

## 6.4 Trabajo futuro

La hoja de ruta (sección 6.y) detalla lo propuesto: el experimento de transferencia y preparación de fuentes, la
extracción determinista como herramienta propia del planificador, los adaptadores a los protocolos de comercio
agéntico (ACP, UCP y AP2), la verificación de las ofertas descartadas que habrían ganado, el autohospedaje de un
modelo de pesos abiertos y un catálogo de referencia gestionado con búsqueda vectorial.
