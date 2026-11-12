# 4.z Validez externa de C2: el clasificador en páginas reales de tiendas colombianas

C2 se eligió y se midió sobre texto del corpus: 0 falsos positivos en 47 fragmentos limpios del corpus B y 0/80 en
el control limpio de E2. La primera consulta en vivo de CotIA mostró otra cosa: el clasificador retiró hasta 21 de
26 ventanas de una ficha real de Falabella. Esta sección mide esa diferencia con una muestra fija de páginas reales,
encuentra su causa y evalúa la corrección adoptada (D115 b, D120).

## Diseño

**Muestra.** Las 12 primeras fichas semilla del corpus A en Alkosto, Ktronix y Falabella y, en las
cinco tiendas de la lista blanca del modo en vivo (D112), la portada y los ocho primeros enlaces que vería el
planificador, en el orden de prioridad de CotIA. En total, 81 páginas (5 portadas, 70 fichas y 6 páginas
institucionales), leídas el 11 de noviembre de 2026 entre las 20:42 y las 21:52 (hora de Colombia) con el mismo
lector del modo en vivo: agente de usuario identificable, robots.txt respetado y 2 s de pausa por sitio.

**Medida.** Las tiendas reales no contienen cargas plantadas, de modo que toda ventana retirada es un falso
positivo. Para cada página se cuentan las ventanas retiradas con el umbral de producción (0,5), si la página pierde
alguna ventana y qué fracción del texto se pierde. Se reporta además si las ventanas retiradas contenían un precio,
que es la pérdida que afecta a la compra. Los dos clasificadores del catálogo de C2 (Horizon-Labs Guard, el de
producción, y Wolf Defender) puntúan las mismas ventanas.

**Condiciones pareadas.** Cada página se leyó una vez y su texto se preparó de dos formas: **crudo** (el recorte de
D112, como estaba en producción) y **saneado** (el saneamiento de D120 seguido del recorte). Comparar cada página
consigo misma elimina la variación entre páginas y entre días.

**Registro.** Por la restricción legal del corpus A (D70) no se conserva el texto: se guarda el SHA-256 de cada
versión y, por ventana, su largo, sus puntajes y tres rasgos sin contenido (`resultados/c2_reales/paginas.jsonl`).
El costo es US$0: no interviene ningún LLM.

## Causa: ruido codificado, no texto comercial

La lectura de las ventanas marcadas descartó la hipótesis inicial, según la cual los llamados a la acción y las
promociones se parecen a una instrucción. De las 289 ventanas marcadas en crudo por alguno de los dos
clasificadores, 231 contenían imágenes SVG incrustadas como `data:` URI (sobre todo el logotipo de la tarjeta CMR
en las fichas de Falabella, cuyo trazo vectorial llega al Markdown codificado en porcentaje y ocupa decenas de
ventanas) y 52 contenían tokens base64 o JWT en URL de rastreo y de
formularios. Las seis restantes eran restos de esas mismas URL, píxeles de seguimiento y el bloque JSON schema.org.
Ninguna contenía lenguaje natural con forma de instrucción. La conversión de HTML a Markdown conserva ese ruido, que
no informa la compra y se parece a la ofuscación con la que se esconden las inyecciones, una señal que los
clasificadores aprenden a marcar.

El saneamiento de D120 actúa sobre esa causa. Antes del recorte, en las fuentes abiertas, cada imagen `![alt](url)`
queda como su texto alternativo y se eliminan los `data:` URI, los parámetros de las URL y las cadenas base64 de 40
o más caracteres. Las rutas de las fichas, los precios y el bloque schema.org no cambian.

## Resultados

**Tabla 4.z.1.** Falsos positivos de C2 en 81 páginas reales, umbral 0,5. Intervalos de Wilson al 95 %.

| Clasificador | Condición | Ventanas retiradas              | Páginas con algún retiro    | Texto retirado |
| ------------ | --------- | ------------------------------- | --------------------------- | -------------- |
| Horizon      | crudo     | 289/1.463 = 19,8 % [17,8; 21,9] | 33/81 = 40,7 % [30,7; 51,6] | 21,3 %         |
| Horizon      | saneado   | 5/1.213 = 0,4 % [0,2; 1,0]      | 5/81 = 6,2 % [2,7; 13,6]    | 0,4 %          |
| Wolf         | crudo     | 232/1.463 = 15,9 % [14,1; 17,8] | 19/81 = 23,5 % [15,6; 33,8] | 17,7 %         |
| Wolf         | saneado   | 1/1.213 = 0,1 % [0,0; 0,5]      | 1/81 = 1,2 % [0,2; 6,7]     | 0,1 %          |

En crudo, el clasificador de producción retiraba una de cada cinco ventanas y tocaba el 40,7 % de las páginas. El
caso extremo era Falabella: 237 de 451 ventanas (52,5 %) y el 56,6 % del texto de sus fichas, por el logotipo
incrustado. Saneado, Horizon retira 5 de 1.213 ventanas (0,4 %) y Falabella
ninguna. El efecto es pareado y en una sola dirección: 28 páginas perdieron ventanas solo en crudo, 5 en ambas
condiciones, ninguna solo saneada y 48 en ninguna (prueba exacta de McNemar, p < 0,001). Wolf Defender, entrenado
por otro equipo, muestra el mismo patrón, así que la falla no es propia de un modelo. Las cinco ventanas residuales
de Horizon (y la única de Wolf) son contenido legítimo: fragmentos de fichas de Ktronix, entre ellos su bloque JSON
schema.org, un carrusel de productos con precios y textos alternativos largos de imágenes de Samsung.

El saneamiento reduce además en un 15,2 % el texto que llega al clasificador y al extractor (de 1.529.884 a
1.296.964 caracteres), es decir, menos tokens por consulta. Las ventanas con precio retiradas eran pocas en crudo
(8 de 590 con Horizon): la pérdida de utilidad en crudo no venía de quitar precios, sino de quitar el contexto
alrededor del producto y de emitir alertas de inyección falsas.

**Subir el umbral no era la solución.** En crudo, Horizon con umbral 0,99 aún retira el 6,1 % de las ventanas y
toca el 14,8 % de las páginas. Un umbral más alto también deja pasar ataques reales. Saneado, Horizon ya no retira
ninguna ventana desde 0,95 (figura `resultados/informes/c2_reales/c2_reales_umbral.png`).

## El saneamiento no le quita a C2 la detección

Las 20 cargas de la suite, la variante adaptativa de política falsificada y los 47 fragmentos limpios del corpus B
se puntuaron en crudo y saneados. Horizon detecta 21 de 21 en ambas condiciones y Wolf 15 de 21 en ambas, con 0
falsos positivos de 47. El saneamiento solo modifica nueve cargas, a las que quita los parámetros de la URL de
acción (`?producto=…&cantidad=…`). En el modo en vivo eso también desarma el canal: una URL de acción sin parámetros
no puede inflar la cantidad ni exfiltrar el presupuesto. El saneamiento no reemplaza al clasificador. Una instrucción
en lenguaje natural sigue llegando a C2, y la separación de planos (C1) sigue siendo la defensa principal (sección
4.x).

## Alcance

La muestra cubre cinco tiendas en un día y 12 de las 25 fichas semilla por tienda; las páginas cambian y la
medición no se reproduce exacta, aunque el procedimiento sí (`make c2-reales`). Las ventanas de una misma página no
son independientes, por lo que el intervalo por ventana es optimista y el de páginas es el conservador. El supuesto
de que las páginas reales no contienen inyecciones se comprobó leyendo a mano las ventanas marcadas, y ninguna
contenía una instrucción. El saneamiento solo se aplica a las fuentes abiertas: el corpus congelado, E1, E2 y E3
no cambian. Con los textos alternativos ahora visibles, una carga escondida en el `alt` de una imagen llega a C2 como
texto, igual que una carga visible.
