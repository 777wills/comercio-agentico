"""Capas de defensa N4 que se suman a la separación de planos (C1).

- **C2, clasificador de inyección.** Cada fragmento de un proveedor se divide en ventanas de
  líneas. Un clasificador local de Hugging Face (CPU) puntúa cada ventana, y las que superan el
  umbral se retiran antes de que el texto llegue al extractor. El resto del fragmento se procesa
  normalmente y se emite la alerta ``posible_inyeccion``. También se retiran los enlaces que solo
  aparecían en las ventanas retiradas. Es filtrado de entrada (OWASP LLM01:2025, estrategia 3;
  MITRE ATLAS AML.M0020).
- **C3, verificación cruzada de precio.** Después del emparejamiento se excluye toda oferta cuyo
  precio cae fuera de [0,75; 1,30] × el precio de referencia del catálogo o por debajo de 0,80 × la
  mediana de los demás proveedores del mismo producto. Es validación determinista de la salida
  del extractor (OWASP LLM01:2025, estrategia 2; ATLAS AML.M0033). En el corpus B limpio ninguna
  oferta sale de esas bandas (0,871–1,065 frente al catálogo; 0,863 como mínimo frente a la
  mediana).

Ninguna capa usa un LLM: C2 corre en CPU y C3 es aritmética. Ambas cuestan US$0 por consulta.
"""

from __future__ import annotations

import os
import statistics
import threading
from dataclasses import dataclass, field
from typing import Any

from comercio_agentico.esquema import Alerta, Oferta

# Catálogo curado de clasificadores de C2: solo los validados en fragmentos limpios en español
# (0 falsos positivos en 47 ventanas del corpus B, i5-1240P sin GPU, 10-nov-2026;
# ver `resultados/clasificadores/`). Ambos Apache-2.0 y sin acceso restringido en el Hub (D16/D80).
# El producto (CotIA, D82/D83) muestra este catálogo como selector en Configuración.
CLASIFICADORES: dict[str, dict[str, Any]] = {
    "Horizon-Labs/prompt-injection-guard-small": {
        "etiqueta": "Horizon-Labs Guard (small)",
        "descripcion": "Multilingüe (mmBERT, 140M). 0 falsos positivos, el más rápido "
        "(p50 192 ms). Entrenado para contenido agéntico con documentos y cargas plantadas.",
        "parametros": "140M",
        "idiomas": "multilingüe (incluye español)",
        "licencia": "Apache-2.0",
        "latencia_p50_ms": 192,
        "fuente": "huggingface.co/Horizon-Labs/prompt-injection-guard-small",
    },
    "patronus-studio/wolf-defender-prompt-injection": {
        "etiqueta": "Wolf Defender (Patronus)",
        "descripcion": "Multilingüe (mmBERT, 140M). 0 falsos positivos, más lento (p50 419 ms). "
        "Respaldo de Red Hat AI.",
        "parametros": "140M",
        "idiomas": "de/en documentados (mmBERT multilingüe)",
        "licencia": "Apache-2.0",
        "latencia_p50_ms": 419,
        "fuente": "huggingface.co/patronus-studio/wolf-defender-prompt-injection",
    },
}
MODELO_CLASIFICADOR_DEFECTO = "Horizon-Labs/prompt-injection-guard-small"
MODELO_CLASIFICADOR = os.environ.get("MODELO_CLASIFICADOR_INYECCION", MODELO_CLASIFICADOR_DEFECTO)
UMBRAL_INYECCION = 0.5
MAX_CARACTERES_VENTANA = 1_200  # ~300-400 tokens en español: cabe en 512 tokens
BANDA_CATALOGO = (0.75, 1.30)
FRACCION_MEDIANA = 0.80


# --------------------------------------------------------------------------------------------------
# Capas activas (D91): tres interruptores independientes; C0–C3 son los puntos medidos en E2


@dataclass(frozen=True)
class Defensas:
    separacion_planos: bool = True
    clasificador: bool = False
    precio: bool = False
    umbral: float = UMBRAL_INYECCION

    @classmethod
    def de(cls, configuracion: str) -> Defensas:
        separacion, clasificador, precio = PRESETS[configuracion]
        return cls(separacion, clasificador, precio)

    @property
    def configuracion(self) -> str | None:
        """C0–C3 si coincide con un preset medido (umbral del informe); si no, None."""
        if self.umbral != UMBRAL_INYECCION and self.clasificador:
            return None
        capas = (self.separacion_planos, self.clasificador, self.precio)
        return next((c for c, p in PRESETS.items() if p == capas), None)


PRESETS: dict[str, tuple[bool, bool, bool]] = {
    "C0": (False, False, False),
    "C1": (True, False, False),
    "C2": (True, True, False),
    "C3": (True, True, True),
}


# --------------------------------------------------------------------------------------------------
# C2: clasificador de inyección por ventanas


def ventanas(texto: str, max_caracteres: int = MAX_CARACTERES_VENTANA) -> list[str]:
    """Agrupa líneas consecutivas hasta ``max_caracteres``; una línea más larga se corta."""
    salida: list[str] = []
    actual: list[str] = []
    largo = 0
    for linea in texto.splitlines():
        while len(linea) > max_caracteres:
            if actual:
                salida.append("\n".join(actual))
                actual, largo = [], 0
            salida.append(linea[:max_caracteres])
            linea = linea[max_caracteres:]
        if largo + len(linea) + 1 > max_caracteres and actual:
            salida.append("\n".join(actual))
            actual, largo = [], 0
        actual.append(linea)
        largo += len(linea) + 1
    if actual:
        salida.append("\n".join(actual))
    return [v for v in salida if v.strip()]


def _indice_inyeccion(id2label: dict[int, str]) -> int:
    """Clase positiva del modelo: INJECTION, JAILBREAK, MALICIOUS, UNSAFE; si no, la 1."""
    for i, etiqueta in id2label.items():
        if any(p in str(etiqueta).upper() for p in ("INJECT", "JAILBREAK", "MALICIOUS", "UNSAFE")):
            return int(i)
    return 1


class ClasificadorInyeccion:
    """Clasificador binario de Hugging Face en CPU. Se carga la primera vez que se usa y se
    comparte entre tareas; las inferencias se serializan con un cerrojo (CPU y RAM acotadas)."""

    def __init__(
        self,
        modelo: str = MODELO_CLASIFICADOR,
        umbral: float = UMBRAL_INYECCION,
        max_tokens: int = 512,
        lote: int = 8,
    ) -> None:
        self.modelo, self.umbral, self.max_tokens, self.lote = modelo, umbral, max_tokens, lote
        self._tok: Any = None
        self._red: Any = None
        self._positiva = 1
        self._cerrojo = threading.Lock()

    def _cargar(self) -> None:
        if self._red is not None:
            return
        from transformers import AutoModelForSequenceClassification, AutoTokenizer

        self._tok = AutoTokenizer.from_pretrained(self.modelo)
        self._red = AutoModelForSequenceClassification.from_pretrained(self.modelo).eval()
        self._positiva = _indice_inyeccion(self._red.config.id2label)

    def puntuar(self, textos: list[str]) -> list[float]:
        """Probabilidad de inyección de cada texto (0 a 1)."""
        if not textos:
            return []
        import torch

        with self._cerrojo:
            self._cargar()
            puntajes: list[float] = []
            for i in range(0, len(textos), self.lote):
                entrada = self._tok(
                    textos[i : i + self.lote],
                    truncation=True,
                    max_length=self.max_tokens,
                    padding=True,
                    return_tensors="pt",
                )
                entrada.pop("token_type_ids", None)  # ModernBERT no lo usa
                with torch.no_grad():
                    logits = self._red(**entrada).logits
                puntajes += torch.softmax(logits, dim=-1)[:, self._positiva].tolist()
            return puntajes


@dataclass
class Filtrado:
    texto: str
    enlaces: list[str]
    total: int
    retiradas: int
    puntaje_max: float
    puntajes: list[float] = field(default_factory=list)


def filtrar(
    texto: str, enlaces: list[str], clasificador: Any, umbral: float | None = None
) -> Filtrado:
    """Retira las ventanas marcadas por el clasificador y los enlaces que solo aparecían en ellas.

    ``clasificador`` es cualquier objeto con ``puntuar(list[str]) -> list[float]`` y ``umbral``
    (las pruebas usan un doble sin red ni modelo). ``umbral`` reemplaza el del clasificador, que
    se comparte entre consultas con umbrales distintos.
    """
    umbral = clasificador.umbral if umbral is None else umbral
    partes = ventanas(texto)
    puntajes = clasificador.puntuar(partes)
    limpias = [v for v, p in zip(partes, puntajes, strict=True) if p < umbral]
    marcadas = [v for v, p in zip(partes, puntajes, strict=True) if p >= umbral]
    if not marcadas:
        return Filtrado(texto, enlaces, len(partes), 0, max(puntajes, default=0.0), puntajes)
    retirado, conservado = "\n".join(marcadas), "\n".join(limpias)

    def solo_en_retirado(enlace: str) -> bool:
        relativo = enlace.rsplit("/", 1)[-1]
        en = lambda t: enlace in t or (bool(relativo) and relativo in t)  # noqa: E731
        return en(retirado) and not en(conservado)

    return Filtrado(
        texto=conservado,
        enlaces=[e for e in enlaces if not solo_en_retirado(e)],
        total=len(partes),
        retiradas=len(marcadas),
        puntaje_max=max(puntajes),
        puntajes=puntajes,
    )


# --------------------------------------------------------------------------------------------------
# C3: verificación cruzada de precio


def motivo_precio_atipico(
    oferta: Oferta, ofertas: list[Oferta], precio_referencia: float | None
) -> str | None:
    """None si el precio es plausible; si no, por qué se excluye."""
    if precio_referencia:
        razon = oferta.precio / precio_referencia
        bajo, alto = BANDA_CATALOGO
        if not bajo <= razon <= alto:
            return f"precio {razon:.2f} × la referencia del catálogo (banda {bajo:.2f}–{alto:.2f})"
    otros = [
        o.precio
        for o in ofertas
        if o.producto_catalogo == oferta.producto_catalogo and o.proveedor != oferta.proveedor
    ]
    if otros:
        mediana = statistics.median(otros)
        if oferta.precio < FRACCION_MEDIANA * mediana:
            return (
                f"precio {oferta.precio / mediana:.2f} × la mediana de los demás proveedores "
                f"(mínimo {FRACCION_MEDIANA:.2f})"
            )
    return None


def verificar_precios(
    ofertas: list[Oferta], precios_referencia: dict[str, float]
) -> tuple[list[Oferta], list[Alerta]]:
    """Separa las ofertas con precio atípico. Las no emparejadas pasan: la propuesta ya no las
    considera."""
    conservadas, alertas = [], []
    for o in ofertas:
        if o.producto_catalogo is None:
            conservadas.append(o)
            continue
        motivo = motivo_precio_atipico(o, ofertas, precios_referencia.get(o.producto_catalogo))
        if motivo is None:
            conservadas.append(o)
        else:
            alertas.append(
                Alerta(
                    tipo="precio_atipico",
                    mensaje=f"Se excluye «{o.titulo}» de {o.proveedor} "
                    f"({o.precio:,.0f} COP): {motivo}.".replace(",", "."),
                )
            )
    return conservadas, alertas
