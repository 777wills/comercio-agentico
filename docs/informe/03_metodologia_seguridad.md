# Metodología: defensa frente a inyección indirecta y suite adversarial

El agente de compras lee contenido publicado por proveedores heterogéneos (páginas, documentos PDF y
mensajes). Ese contenido no es de confianza: puede incluir instrucciones dirigidas al modelo en lugar
de datos. Esta sección describe el vector estudiado, las cuatro configuraciones de defensa que se
comparan y la elección empírica del clasificador de una de ellas. La medición de la eficacia de cada
defensa frente a las cargas (curva seguridad-utilidad) se reporta en la sección de resultados E2.

## Vector: inyección indirecta de instrucciones

El ataque estudiado es la **inyección indirecta de instrucciones** (OWASP LLM01:2025, *Indirect
Prompt Injection*; MITRE ATLAS AML.T0051.001, madurez «Realized»): el adversario no interactúa con el
agente, sino que inserta instrucciones en contenido que el agente ingiere al consultar una fuente. El
plantado de esas instrucciones en una fuente consultada por el agente corresponde además a ATLAS
AML.T0099 (*AI Agent Tool Data Poisoning*). El mapeo completo de las cinco clases de ataque y de las
defensas a OWASP (Top 10 for LLM 2025 y Top 10 for Agentic Applications 2026) y a MITRE ATLAS v2026.10
está en `ataques/mapeo.md`, verificado contra las fuentes primarias el 10-nov-2026.

## Cuatro configuraciones de defensa (C0–C3)

Cada configuración añade una capa a la anterior, de modo que la curva seguridad-utilidad tiene cuatro
puntos comparables con el mismo modelo base (DeepSeek Flash, D79):

| Config. | Capa añadida | Mitigación (OWASP LLM01:2025 / MITRE ATLAS) |
|---|---|---|
| **C0** | ninguna: el texto del proveedor llega al planificador | línea base |
| **C1** | **separación de planos**: el contenido del proveedor solo llega a un extractor acotado con salida estructurada; al planificador vuelven ofertas en JSON, nunca prosa de terceros | #6 Segregar el contenido externo / AML.M0030 |
| **C2** | **clasificador de inyección**: cada fragmento se divide en ventanas y un clasificador local marca y retira las que son instrucciones antes de extraer | #3 Filtrado de entrada / AML.M0020, AML.M0015 |
| **C3** | **verificación cruzada de precio**: se excluye toda oferta con precio fuera de banda respecto al catálogo y a la mediana de los demás proveedores | #2 Validar la salida / AML.M0033 |

La separación de planos (C1) es la pieza central: hace *medible* el ataque, porque la navegación del
planificador es secuestrable en C0 y no en C1 (D59). C2 y C3 no usan ningún LLM —el clasificador
corre en CPU y la verificación de precio es aritmética—, así que su costo por consulta es US$0 y su
latencia es acotada.

### C2: clasificador por ventanas

El fragmento de cada fuente se divide en ventanas de líneas consecutivas (hasta ~1.200 caracteres,
que caben en 512 tokens). El clasificador puntúa cada ventana; las que superan 0,5 se retiran, junto
con los enlaces que solo aparecían en ellas, y el resto del fragmento se extrae con normalidad. Se
emite la alerta `posible_inyeccion` con el proveedor, el número de ventanas retiradas y el puntaje
máximo. Retirar solo las ventanas marcadas —en lugar de descartar el fragmento entero— conserva la
utilidad cuando la inyección convive con ofertas legítimas.

### C3: verificación cruzada de precio

Tras el emparejamiento, se excluye como `precio_atipico` toda oferta cuyo precio cae fuera de
[0,75; 1,30] × el precio de referencia del catálogo, o por debajo de 0,80 × la mediana de los demás
proveedores del mismo producto. Las bandas se fijaron con los datos del corpus B limpio, donde las
ofertas legítimas caen entre 0,871 y 1,065 × la referencia (mínimo 0,863 × la mediana): ninguna oferta
limpia se excluye. C3 cierra específicamente la clase de ataque «alterar el precio comparado».

## Elección del clasificador de C2

El clasificador de C2 debía cumplir cuatro requisitos: licencia permisiva, **sin acceso restringido**
en el Hub (para que cualquiera que clone el repositorio público o despliegue la demo lo descargue sin
pedir permiso), funcionamiento en CPU con latencia aceptable en el equipo de desarrollo (Intel
i5-1240P, sin GPU) y, de forma crítica, **baja tasa de falsas alarmas sobre texto comercial legítimo
en español**: un clasificador que marca texto limpio como ataque destruiría la utilidad del agente.

Se midieron tres candidatos Apache-2.0 y sin acceso restringido sobre 47 ventanas de fragmentos
limpios del corpus B (proveedores P2–P5, español real). Al ser todas limpias, todo puntaje ≥ 0,5 es un
falso positivo. El experimento es reproducible con
`uv run python -m comercio_agentico.ataques.elegir_clasificador` (US$0); los datos quedan en
`resultados/clasificadores/2026-11-10_falsos_positivos.json`.

| Clasificador | Falsos positivos | Puntaje máx. | p50 (ms) | p90 (ms) |
|---|---|---|---|---|
| **Horizon-Labs/prompt-injection-guard-small** (mmBERT, multilingüe) | **0/47** | 0,009 | **192** | 314 |
| patronus-studio/wolf-defender-prompt-injection (mmBERT, multilingüe) | 0/47 | 0,000 | 419 | 683 |
| protectai/deberta-v3-base-prompt-injection-v2 (DeBERTa-v3, inglés) | 6/47 (12,8 %) | 0,997 | 810 | 1.130 |

El clasificador en inglés más difundido (protectai, DeBERTa-v3) marcó **6 de 47** fragmentos limpios
en español como inyección, uno con puntaje 0,997 —un listado de especificaciones de producto—, y fue
el más lento. Esto confirma que un modelo entrenado solo en inglés es inadecuado para el escenario y
motiva la elección de un clasificador multilingüe. Los dos modelos multilingües (ambos sobre la
arquitectura mmBERT) obtuvieron 0 falsos positivos; **Horizon-Labs Guard (small)** se adoptó como
predeterminado por ser más de dos veces más rápido. La configuración del producto (CotIA) permite al
usuario elegir entre los dos modelos validados (`CLASIFICADORES` en `agente/defensa.py`).

> Nota de alcance: esta tabla mide **falsas alarmas**, no la detección de ataques. La detección se
> mide con la suite de cargas (métrica M5) en los resultados E2. Un clasificador con pocas falsas
> alarmas pero baja detección se descartaría en esa segunda medición.
