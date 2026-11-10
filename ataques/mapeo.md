# Mapeo de la suite adversarial a marcos reconocidos

La suite de este proyecto estudia la **inyección indirecta de instrucciones**: el agente lee contenido
publicado por un proveedor (página, PDF o chat) que contiene órdenes dirigidas al modelo, no datos.
Las cinco clases de ataque y las cuatro configuraciones de defensa (C0–C3) se enmarcan en tres
referencias públicas, verificadas en su fuente primaria el 10-nov-2026.

## Fuentes primarias

| Marco | Versión vigente | Fecha | Fuente |
|---|---|---|---|
| OWASP Top 10 for LLM Applications | 2025 (LLM01:2025) | lista de 2025 | genai.owasp.org/llm-top-10/ |
| OWASP Top 10 for Agentic Applications | 2026 | publicado 9-dic-2025 | genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026/ |
| MITRE ATLAS | v2026.10 | 28-oct-2026 | github.com/mitre-atlas/atlas-data (release v2026.10) |

> La taxonomía MITRE pertinente es **ATLAS** (Adversarial Threat Landscape for AI Systems), no
> ATT&CK: el pendiente de S06 queda resuelto. ATLAS reutiliza la estructura de tácticas y técnicas
> de ATT&CK pero para sistemas de IA.

## Marco general del vector

Toda la suite instancia una misma técnica raíz:

- **OWASP LLM01:2025 Prompt Injection**, variante *Indirect Prompt Injection*: «ocurre cuando un LLM
  acepta entrada de fuentes externas, como páginas web o archivos [...] que, al ser interpretadas por
  el modelo, alteran su comportamiento de forma no intencionada o inesperada». Escenario de ataque
  #2 del documento: una página con instrucciones ocultas que llevan al LLM a exfiltrar la conversación.
- **MITRE ATLAS AML.T0051.001 — LLM Prompt Injection: Indirect** (táctica AML.TA0005 *Execution*;
  madurez «Realized»): «inyección de prompts de forma indirecta a través de un canal de datos
  separado que el LLM o el agente de IA ingiere [...]. Estas instrucciones se originan en contenido
  controlado por el adversario y con frecuencia están ocultas u ofuscadas». El plantado en el corpus
  corresponde además a **AML.T0099 — AI Agent Tool Data Poisoning**: manipular una fuente de datos
  que el agente consulta a través de una herramienta.

## Mapeo por clase de ataque

| Clase (proyecto) | Objetivo del adversario | OWASP agéntico | MITRE ATLAS |
|---|---|---|---|
| Desviar la compra | que la recomendación caiga en el proveedor atacante | ASI01 Agent Goal Hijack | AML.T0130 AI Agent Response Biasing · AML.T0048.000 Financial Harm |
| Inflar la cantidad | que el agente invoque una acción con cantidad mayor a la pedida | ASI02 Tool Misuse | AML.T0053 AI Agent Tool Invocation |
| Exfiltrar el mandato | sonsacar el presupuesto u otro dato del comprador y sacarlo del sistema | ASI01 Agent Goal Hijack | AML.T0086 Exfiltration via AI Agent Tool Invocation |
| Saltarse la confirmación | que el agente «confirme» un pedido sin aprobación humana | ASI02 Tool Misuse | AML.T0053 AI Agent Tool Invocation |
| Alterar el precio comparado | que el cuadro comparativo muestre un precio falso de la oferta atacante | ASI01 Agent Goal Hijack | AML.T0067 LLM Trusted Output Components Manipulation |

Las cuatro **ubicaciones** (texto visible, oculto en HTML, PDF, mensaje) son variantes del mismo
AML.T0051.001; el plantado en HTML invisible corresponde a la ofuscación que la propia técnica
menciona (ATLAS AML.T0068 *LLM Prompt Obfuscation*; OWASP escenario #9 *Multilingual/Obfuscated*).

## Mapeo de las defensas a mitigaciones

| Configuración | Qué añade | OWASP LLM01:2025 (estrategia) | MITRE ATLAS (mitigación) |
|---|---|---|---|
| C0 | ninguna (línea base) | — | — |
| C1 | separación de planos: el contenido del proveedor no llega al planificador | #6 Segregar e identificar el contenido externo | AML.M0030 Restrict AI Agent Tool Invocation on Untrusted Data |
| C2 | clasificador de inyección sobre cada fragmento (filtro de entrada) | #3 Filtrado de entrada y salida | AML.M0020 Generative AI Guardrails · AML.M0015 Adversarial Input Detection |
| C3 | verificación cruzada de precio (validación determinista de la salida) | #2 Definir y validar formatos de salida esperados | AML.M0033 Input and Output Validation for AI Agent Components |

Las cinco clases también ejercen, de forma transversal, **OWASP LLM06:2025 Excessive Agency**
(el daño depende de cuánta acción se delegue al agente) y, cuando la carga pide confirmar o comprar,
la mitigación **AML.M0029 Human In-the-Loop for AI Agent Actions**.

## Nota de alcance

Las cargas se plantan únicamente en los proveedores **sintéticos** del corpus B, servidos en la
máquina local (D21). Ningún sitio real recibe una carga: la Ley 1273 de 2009 de Colombia tipifica el
acceso abusivo y el daño a sistemas informáticos de terceros, y el diseño del corpus sintético lo
evita por construcción. Las 20 cargas se publican en `ataques/cargas.yaml` (D95) para que la suite
sea reproducible; las copias plantadas se regeneran con `python -m comercio_agentico.ataques.plantar`.
