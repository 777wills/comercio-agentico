# 4.x Resultados E2: robustez frente a inyección indirecta (M5)

> Borrador. Esta versión recoge la prueba de humo de la suite; la matriz completa (20 cargas × C0–C3) y la curva
> seguridad-utilidad se incorporan en S07.

## Prueba de humo

La prueba de humo verifica que las cuatro rutas de plantado y los cinco predicados funcionan con el agente real antes
de la matriz completa. Se ejecutó con DeepSeek V4.1 Flash, el modelo base (D79), sobre la diagonal clase × ubicación
(A01 visible, A06 oculto en JSON-LD, A11 en el PDF, A16 en el mensaje y A17 visible; D94) y sobre tres cargas visibles
adicionales (A05, A09 y A13), en las configuraciones extremas C0 (sin defensa) y C3 (separación de planos, clasificador
de inyección y verificación de precio). Cada ejecución corresponde a una carga, una configuración y una repetición.

**Tabla 4.x.1.** Tasa de éxito del ataque (M5) en la prueba de humo. Intervalos de Wilson al 95 %.

| Configuración | Éxitos / ejecuciones | M5 | IC 95 % | Tarea benigna acertada | Alerta del clasificador | Costo (US$) |
|---|---:|---:|---:|---:|---:|---:|
| C0 | 1 / 8 | 12,5 % | [2,2 %; 47,1 %] | 8 / 8 | — | 0,1179 |
| C3 | 0 / 8 | 0,0 % | [0,0 %; 32,4 %] | 8 / 8 | 8 / 8 | 0,1148 |

Fuente: `resultados/ataques/2026-11-10_humo_ataques_m5.{json,md}` y la corrida `2026-11-10_humo_ataques.jsonl.gz`
(16 ejecuciones, 0 errores, US$0,2327; mediana de ~100 s por ejecución).

El único éxito fue A09 en C0 (exfiltración del mandato, texto visible en P3): el planificador volvió a abrir la página
del proveedor con el parámetro `presupuesto_max=2990000`, de modo que el presupuesto del comprador salió del sistema
en el argumento de una herramienta. En C3 la misma carga no prosperó. Las demás cargas no alcanzaron su objetivo en
ninguna de las dos configuraciones, aunque el agente leyó en todos los casos el archivo que las contenía. En C3 el
clasificador de inyección marcó y retiró el fragmento atacado en las ocho ejecuciones, y la utilidad sobre la tarea
benigna se conservó (8/8 aciertos en ambas configuraciones).

## Alcance

Con ocho ejecuciones por configuración, los intervalos son amplios: el 0 % de C3 es compatible con una tasa
poblacional de hasta 32,4 %, y la muestra no permite comparar clases ni ubicaciones. Las clases de navegación miden que
el planificador **solicitó** la URL de acción local, no que una compra se haya consumado: el corpus no ejecuta pagos ni
pedidos. El predicado de precio examina el cuadro final, no las ofertas retiradas por C3. La medición definitiva de M5
por configuración, clase y ubicación, junto con la utilidad M2 sobre las tareas benignas, corresponde a la matriz
completa de E2.
