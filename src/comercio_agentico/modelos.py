"""Fábrica de modelos de lenguaje y registro de tokens y costo por llamada.

Los seis modelos del experimento E3 (D31) se obtienen por un nombre corto. Los de Anthropic se usan
por su API directa; los de pesos abiertos, por OpenRouter con el proveedor fijado y sin respaldo a
otros (D32), para que cada corrida sea reproducible. El costo de OpenRouter es el que devuelve la
propia API en cada respuesta; el de Anthropic se calcula con la tabla de precios registrada en
`docs/DECISIONES.md`.
"""

from __future__ import annotations

import os
import threading
import time
from dataclasses import asdict, dataclass, field
from typing import Any, Literal

from dotenv import load_dotenv
from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.exceptions import OutputParserException
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage
from langchain_core.outputs import ChatGeneration, LLMResult
from pydantic import ValidationError

Plataforma = Literal["anthropic", "openrouter"]


@dataclass(frozen=True)
class ConfigModelo:
    """Ficha de un modelo: dónde se llama, con qué identificador y a qué precio."""

    nombre: str
    plataforma: Plataforma
    id_modelo: str
    precio_entrada: float  # US$ por millón de tokens
    precio_salida: float  # US$ por millón de tokens
    proveedor: str | None = None  # slug del endpoint en OpenRouter (D32)
    nivel: str = ""


# Orden de costo de D31. Precios del 9-nov-2026, US$ por millón de tokens
# (Anthropic: tabla de DECISIONES; OpenRouter: endpoint fijado).
MODELOS: dict[str, ConfigModelo] = {
    m.nombre: m
    for m in [
        ConfigModelo(
            "deepseek-flash",
            "openrouter",
            "deepseek/deepseek-v4.1-flash",
            0.14,
            0.42,
            proveedor="deepinfra/fp8",
            nivel="económico",
        ),
        ConfigModelo("haiku", "anthropic", "claude-haiku-5-5", 0.10, 0.50, nivel="económico"),
        ConfigModelo(
            "deepseek-pro",
            "openrouter",
            "deepseek/deepseek-v4-pro",
            1.30,
            2.60,
            proveedor="deepinfra/fp8",
            nivel="medio",
        ),
        ConfigModelo(
            "kimi",
            "openrouter",
            "moonshotai/kimi-k3.1-pro",
            1.90,
            9.50,
            proveedor="deepinfra/bf16",
            nivel="tope",
        ),
        ConfigModelo("sonnet", "anthropic", "claude-sonnet-5-5", 2.00, 10.00, nivel="medio"),
        ConfigModelo("opus", "anthropic", "claude-opus-5-5", 4.00, 20.00, nivel="tope"),
    ]
}


ESFUERZO_RAZONAMIENTO = "low"  # D60: condición uniforme del agente en los seis modelos
MAX_TOKENS_SALIDA = 8000  # corta generaciones desbocadas (un modelo barato puede repetir sin fin)
TIEMPO_MAXIMO_S = 120


def obtener_modelo(
    nombre: str,
    *,
    temperatura: float | None = 0.0,
    razonamiento: str | None = ESFUERZO_RAZONAMIENTO,
    **kwargs: Any,
) -> BaseChatModel:
    """Devuelve el modelo de chat de LangChain para el nombre corto dado (p. ej. ``"haiku"``).

    La temperatura y el esfuerzo de razonamiento solo se aplican a los modelos de OpenRouter; a
    Claude 5.5 no se le activa el pensamiento extendido (D60). ``razonamiento=None`` deja el valor
    por defecto del modelo.
    """
    load_dotenv()
    if nombre not in MODELOS:
        raise KeyError(f"Modelo desconocido: {nombre!r}. Opciones: {', '.join(MODELOS)}")
    cfg = MODELOS[nombre]

    if cfg.plataforma == "anthropic":
        # Claude 5.5 rechaza `temperature`; la variabilidad se mide con corridas repetidas (D42).
        from langchain_anthropic import ChatAnthropic

        kwargs.setdefault("max_tokens", MAX_TOKENS_SALIDA)
        kwargs.setdefault("timeout", TIEMPO_MAXIMO_S)
        return ChatAnthropic(model=cfg.id_modelo, **kwargs)

    from langchain_openrouter import ChatOpenRouter

    if temperatura is not None:
        kwargs.setdefault("temperature", temperatura)
    if razonamiento is not None:
        kwargs.setdefault("reasoning", {"effort": razonamiento})
    kwargs.setdefault("max_tokens", MAX_TOKENS_SALIDA)
    kwargs.setdefault("timeout", TIEMPO_MAXIMO_S * 1000)  # milisegundos en el SDK de OpenRouter
    return ChatOpenRouter(
        model=cfg.id_modelo,
        openrouter_provider={
            "order": [cfg.proveedor],
            "allow_fallbacks": False,
            "require_parameters": True,
        },
        app_title="comercio-agentico",
        **kwargs,
    )


def nombre_por_id(id_modelo: str) -> str | None:
    """Traduce el identificador que devuelve la API al nombre corto (tolera sufijos de versión)."""
    for cfg in MODELOS.values():
        if id_modelo == cfg.id_modelo or id_modelo.startswith(cfg.id_modelo):
            return cfg.nombre
    return None


def costo_estimado(nombre: str, tokens_entrada: int, tokens_salida: int) -> float:
    """Costo en US$ según la tabla de precios (sin descuentos de caché)."""
    cfg = MODELOS[nombre]
    return (tokens_entrada * cfg.precio_entrada + tokens_salida * cfg.precio_salida) / 1_000_000


class CostoExcedido(RuntimeError):
    """Se superó el tope de gasto por tarea (protege los créditos ante bucles del agente)."""


@dataclass
class LlamadaLLM:
    """Una llamada al modelo, con lo necesario para la métrica de costo (M6) y la trazabilidad."""

    modelo: str
    id_respuesta: str | None
    tokens_entrada: int
    tokens_salida: int
    costo_usd: float
    costo_fuente: Literal["api", "tabla"]
    proveedor: str | None
    marca_tiempo: float = field(default_factory=time.time)


class RegistroCosto(BaseCallbackHandler):
    """Callback que acumula tokens y costo de cada llamada y corta si se excede el tope.

    Uso: ``modelo.invoke(..., config={"callbacks": [registro]})``.
    """

    raise_error = True  # para que CostoExcedido detenga la ejecución

    def __init__(self, tope_usd: float | None = None) -> None:
        super().__init__()
        load_dotenv()
        if tope_usd is None:
            tope_usd = float(os.getenv("COSTO_MAXIMO_POR_TAREA_USD", "0.50"))
        self.tope_usd = tope_usd
        self.llamadas: list[LlamadaLLM] = []
        self._lock = threading.Lock()

    @property
    def costo_total(self) -> float:
        return sum(llamada.costo_usd for llamada in self.llamadas)

    @property
    def tokens_totales(self) -> tuple[int, int]:
        return (
            sum(llamada.tokens_entrada for llamada in self.llamadas),
            sum(llamada.tokens_salida for llamada in self.llamadas),
        )

    def on_llm_end(self, response: LLMResult, **kwargs: Any) -> None:
        try:
            generacion = response.generations[0][0]
        except IndexError:
            return
        if not isinstance(generacion, ChatGeneration) or not isinstance(
            generacion.message, AIMessage
        ):
            return
        mensaje = generacion.message
        uso = mensaje.usage_metadata or {}
        meta = mensaje.response_metadata or {}
        id_modelo = meta.get("model_name") or meta.get("model") or ""
        nombre = nombre_por_id(id_modelo) or id_modelo
        entrada, salida = uso.get("input_tokens", 0), uso.get("output_tokens", 0)

        if "cost" in meta:
            costo, fuente = float(meta["cost"]), "api"
        elif nombre in MODELOS:
            costo, fuente = costo_estimado(nombre, entrada, salida), "tabla"
        else:
            costo, fuente = 0.0, "tabla"

        llamada = LlamadaLLM(
            modelo=nombre,
            id_respuesta=meta.get("id") or mensaje.id,
            tokens_entrada=entrada,
            tokens_salida=salida,
            costo_usd=costo,
            costo_fuente=fuente,
            # OpenRouter no siempre informa el proveedor; con allow_fallbacks=False es el fijado.
            proveedor=meta.get("provider")
            or (MODELOS[nombre].proveedor if nombre in MODELOS else None)
            or meta.get("model_provider"),
        )
        with self._lock:
            self.llamadas.append(llamada)
            total = self.costo_total
        if total > self.tope_usd:
            raise CostoExcedido(f"Gasto US${total:.4f} supera el tope de US${self.tope_usd:.2f}")

    def como_dicts(self) -> list[dict[str, Any]]:
        return [asdict(llamada) for llamada in self.llamadas]


def obtener_extractor(nombre: str, esquema: type, *, include_raw: bool = False, **kwargs: Any):
    """Modelo con salida estructurada por JSON Schema nativo.

    Se usa el mismo método en los seis modelos para que E3 compare en igualdad de condiciones;
    el método por herramienta forzada (``tool_choice``) no lo admite DeepSeek V4 Pro en OpenRouter.
    Con ``include_raw=True`` devuelve también el mensaje crudo, para validar elemento por elemento.
    """
    return obtener_modelo(nombre, **kwargs).with_structured_output(
        esquema, method="json_schema", include_raw=include_raw
    )


async def invocar_estructurado(
    estructurado: Any, mensajes: list, config: dict | None = None, intentos: int = 2
) -> Any | None:
    """Llamada con salida estructurada que tolera JSON inválido o truncado.

    Algunos proveedores de OpenRouter (DeepInfra) no restringen la decodificación al esquema, así
    que la salida puede no parsear. Se reintenta y, si sigue fallando, se devuelve ``None`` para
    que quien llama degrade de forma controlada en vez de abortar la tarea.
    """
    for _ in range(intentos):
        try:
            return await estructurado.ainvoke(mensajes, config=config)
        except (OutputParserException, ValidationError):
            continue
    return None
