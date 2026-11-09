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
