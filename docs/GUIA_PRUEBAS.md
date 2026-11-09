# Guía de pruebas: qué se construyó y cómo probarlo

Una sección por sesión. Cada comando declara su **costo estimado**. Orden de preferencia: sin costo → modelo gratuito
de OpenRouter → una sola llamada al modelo más barato. Las pruebas manuales nunca usan Sonnet, Kimi ni Opus.

Todos los comandos se ejecutan desde la raíz del repositorio. Requisito único: `uv` instalado y, para los que llaman
a un modelo, el `.env` con las claves (`cp .env.example .env`).

---

## S00 — Arranque técnico (9-nov)

### Qué se construyó y por qué

| Componente | Qué hace | Concepto de IA / decisión |
|---|---|---|
| `pyproject.toml` + `uv.lock` | Entorno reproducible en Python 3.13 con LangGraph, LangChain, crawl4ai y Streamlit. | Cualquiera reproduce exactamente las mismas versiones (Cr8, R.7.2). |
| `src/comercio_agentico/modelos.py` | Fábrica `obtener_modelo("haiku")` para los 6 modelos: los Claude van directo a Anthropic; DeepSeek y Kimi por OpenRouter con el proveedor **DeepInfra fijado** (D34). `RegistroCosto` es un *callback* de LangChain que anota tokens, costo y proveedor de cada llamada, y **corta la tarea si supera el tope** de `COSTO_MAXIMO_POR_TAREA_USD`. | Comparar modelos exige que el único cambio sea el modelo: mismo proveedor siempre (reproducibilidad) y costo medido por llamada (métrica M6). El tope protege los créditos si el agente entra en bucle. |
| `obtener_extractor(...)` | Devuelve el modelo configurado para **salida estructurada por JSON Schema**: el LLM no responde texto libre sino un objeto que cumple el esquema de `ListaOfertas`. | Así la extracción es validable por programa. Se usa `json_schema` en los 6 porque DeepSeek V4 Pro no admite el método por herramienta forzada (D35): todos compiten en igualdad de condiciones. |
| `src/comercio_agentico/esquema.py` | `OfertaExtraida` es **lo único que produce el LLM** (título, precio, GTIN, disponibilidad...). `Procedencia` la escribe **el código**, nunca el modelo: fuente, consulta, hora, fragmento original y su **SHA-256**. `Oferta` = las dos juntas. | Trazabilidad que el modelo no puede inventar ni alterar: cada dato de la propuesta apunta al fragmento exacto de donde salió, y la suma de verificación prueba que ese fragmento no cambió. Es la base de la capa de verificación (N3). |
| Validación de GTIN | `gtin_valido()` comprueba el dígito de control del código de barras. | Si el LLM "alucina" un GTIN, casi siempre falla el dígito de control y se descarta por programa. |
| `perfiles/electronica.yaml` | Perfil de categoría declarativo: atributos comparables, sinónimos, unidades y su normalización, restricciones duras. | Agregar una categoría es escribir un YAML, no código (base del experimento de transferencia, que queda propuesto). |
| `ping.py` | Llama a cada modelo con una herramienta falsa (`consultar_precio`) y verifica que el modelo **decida usarla** con el GTIN correcto. | *Tool calling*: el agente de N2 depende de que el modelo sepa invocar herramientas. |
| Ruff, pre-commit, Makefile, CI en GitHub Actions | Calidad automática en cada commit y cada push. | Prácticas MLOps mínimas (R.7.2), adoptadas del estándar del profesor (D52). |

Hallazgos de S00 que se usarán después: los Claude 5.5 rechazan el parámetro `temperature`, así que la variabilidad
se mide repitiendo corridas (D36). En una extracción de prueba, DeepSeek Flash sacó 13 ofertas en vez de 12 y no
marcó las agotadas, y los otros cinco acertaron: es la clase de diferencia que mide E3.

### Cómo probarlo

**1. Instalar y correr las pruebas — costo US$0 (sin red)**

```bash
make install        # crea .venv con las versiones exactas de uv.lock
make test           # 34 pruebas; ninguna llama a un modelo
make check          # lint + formato + pruebas: lo mismo que corre la CI en GitHub
make help           # lista todas las tareas disponibles
```

Si funciona: `34 passed`.

**2. Ver el esquema y la procedencia en acción — costo US$0 (sin red)**

Simula lo que hará el agente: el "LLM" entrega una `OfertaExtraida` y el código le agrega la `Procedencia` con su
huella SHA-256.

```bash
uv run python - <<'EOF'
from comercio_agentico.esquema import gtin_valido, OfertaExtraida, Oferta, Procedencia, cargar_perfil

print("GTIN 7702004003508 válido:", gtin_valido("7702004003508"))   # True
print("GTIN 7702004003509 válido:", gtin_valido("7702004003509"))   # False: dígito de control alterado

fragmento = "Portátil Lenovo IdeaPad 3 15'' Ryzen 5 8GB 512GB — $2.499.900 — Envío gratis"
extraida = OfertaExtraida(titulo="Portátil Lenovo IdeaPad 3 15 Ryzen 5 8GB 512GB",
                          precio=2499900, marca="Lenovo", disponibilidad="en_stock")
proc = Procedencia(fuente="proveedor-demo", tipo_fuente="web_plana", consulta="abrir_pagina(demo)",
                   fragmento_original=fragmento, ruta_extraccion="llm", modelo_extraccion="deepseek-flash")
print(Oferta(**extraida.model_dump(), procedencia=proc).model_dump_json(indent=2))

perfil = cargar_perfil("perfiles/electronica.yaml")
print("Perfil:", perfil.nombre, "| atributos:", [a.nombre for a in perfil.atributos])
EOF
```

Qué observar: el bloque `procedencia` con `suma_verificacion` (64 caracteres hexadecimales). Cambia una letra del
`fragmento` y vuelve a correrlo: la suma cambia por completo. Así se detecta que un dato ya no corresponde a su
fuente.

**3. Probar que un modelo usa herramientas — costo < US$0,001 por modelo**

```bash
uv run python -m comercio_agentico.ping deepseek-flash
uv run python -m comercio_agentico.ping haiku
```

Si funciona: una línea `OK` por modelo con latencia, tokens, costo en US$, proveedor y `gtin=7702004003508`.
Evita `make ping` sin argumentos: llama también a Sonnet, Kimi y Opus (unos centavos; innecesario para probar).

---

## S01 — Corpus B sintético y tareas (9-nov)

### Qué se construyó y por qué

| Componente | Qué hace | Concepto de IA / decisión |
|---|---|---|
| `corpus_b/catalogo.py` → `corpus/b_sintetico/catalogo.json` | DeepSeek Flash propone 40 productos (8 por categoría) con atributos, precio y tres alias: comercial, de PDF y de WhatsApp. El **código** asigna el GTIN-13 y valida cada atributo contra el perfil. | **Generación sintética con LLM + validación por programa:** el LLM aporta verosimilitud; lo que hace mal (dígitos de control, unidades) lo hace o lo corrige el código. El catálogo se congela en git: el resto no vuelve a gastar. |
| `perfiles/electronica.yaml` | Ahora cubre las 5 categorías: `tipo_producto`, `procesador`, `frecuencia_refresco`, `cancelacion_ruido`, `inalambrico`, `autonomia`, `tipo_almacenamiento`, `velocidad_lectura`. | Configuración declarativa: ampliar el dominio no tocó código. |
| `corpus_b/generar.py` + `render.py` | Con semilla fija, reparte el catálogo entre 5 proveedores con precios, envío, plazo y existencias propios. **Primero escribe `verdad.json`** y después renderiza cada formato desde ella. | **Verdad de referencia por construcción:** como el contenido sale de la verdad, se sabe exactamente qué debería extraerse de cada página, PDF o mensaje. |
| P1 `servidor_mcp.py` | Mayorista por **MCP** (FastMCP) con `buscar_productos` y `detalle_producto`, con nombres de campo propios. | Herramienta externa real para el agente (MCP). Traducir `valor_unitario_cop` a `precio` es trabajo del agente. |
| P2 a P5 | P2: HTML con **JSON-LD** schema.org. P3: HTML plano con nombres comerciales y sin GTIN. P4: **PDF** mayorista con abreviaturas. P5: **chat tipo WhatsApp** con precios como "2'350.000" o "2350 mil". | **Heterogeneidad de fuentes:** del dato estructurado al texto informal. Cuanto menos madura la fuente, más depende el sistema del LLM y del emparejamiento por embeddings (S02). |
| `corpus_b/servir.py` | Un solo comando sirve P2 a P5 en `:8800` y P1 en `:8801/mcp`. | El agente accede a cada fuente como lo haría en la realidad. |
| `corpus_b/tareas.py` → `tareas/tareas_b.jsonl` | 60 tareas: específica 12, más barato 12, restricciones 15, vaga 12, sin respuesta 9. Cada una trae consulta, criterios y respuesta, calculada por `calcular_respuesta`. | **Evaluación con verdad derivada:** ninguna respuesta se escribe a mano. Las 9 sin respuesta miden la **abstención**. |
| `tests/test_corpus_b.py` | 18 pruebas nuevas: cada formato coincide con la verdad, la regeneración es idéntica byte a byte y cada tarea tiene la respuesta que se deriva de la verdad. | Validez del instrumento de medición antes de medir nada. |

### Cómo probarlo

**1. Pruebas completas — costo US$0 (sin red)**

```bash
make check          # lint + formato + 52 pruebas (34 de S00 + 18 de S01)
```

Si funciona: `52 passed`. Las de S01 levantan el servidor MCP en memoria y leen el PDF.

**2. Regenerar el corpus y las tareas — costo US$0 (sin red)**

```bash
make corpus-b
git status --short corpus tareas    # debe quedar vacío: la generación es determinista
```

Si funciona: el resumen por proveedor (21/20/19/22/13 ofertas, 95 en total), los productos sin oferta y los que
solo están agotados, y luego `60 tareas ... {'especifica': 12, ...}`. Si `git status` muestra cambios, se rompió
el determinismo.

**3. Ver los cinco proveedores en el navegador — costo US$0 (solo local)**

```bash
make corpus-b-servir                # deja la terminal ocupada; Ctrl+C para detener
```

Abre <http://127.0.0.1:8800/p2_web_schema/index.html>, `/p3_web_plana/index.html`, `/p4_pdf/lista_precios.pdf` y
`/p5_mensaje/chat.txt`. En P2, "Ver código fuente" muestra el bloque `application/ld+json`. En P3 el mismo producto
aparece con otro nombre y sin EAN. Para P1 (MCP), en otra terminal:

```bash
uv run python -c "
import asyncio
from fastmcp import Client
async def m():
    async with Client('http://127.0.0.1:8801/mcp') as c:
        r = await c.call_tool('buscar_productos', {'texto': 'vivobook'})
        print(r.data)
asyncio.run(m())"
```

Qué observar: solo aparece una de las dos variantes del Vivobook (8 GB). La otra (16 GB) la venden P2, P3 y P4.
En P3 las dos variantes solo se distinguen por "8GB/512GB" frente a "16GB/512GB": es el caso difícil del
emparejamiento.

**4. Inspeccionar una tarea y su respuesta — costo US$0**

```bash
uv run python -c "
from comercio_agentico.corpus_b.tareas import cargar_tareas
for t in cargar_tareas()[::12]:
    print(t.id, t.categoria, '|', t.consulta); print('   →', t.respuesta.model_dump())"
```

Interpretación: `ofertas_validas` es la lista (proveedor, producto) ordenada por costo total. La primera es la
respuesta exacta. En las tareas vagas vale cualquiera de la lista, y en las de `sin_respuesta` la respuesta es
`abstencion: True`.

**5. (Opcional) Regenerar el catálogo con el LLM — costo ~US$0,03**

No hace falta: el catálogo está congelado en git. Si lo regeneras, cambian los productos y, con ellos, todo el
corpus. Para ver la validación sin gastar, usa `uv run python -m comercio_agentico.corpus_b.catalogo --reparar`
(US$0).

---
