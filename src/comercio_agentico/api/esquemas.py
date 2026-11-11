"""Contrato de la API de CotIA (Pydantic; FastAPI genera el OpenAPI a partir de aquí)."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from comercio_agentico.agente.defensa import (
    CLASIFICADORES,
    MODELO_CLASIFICADOR_DEFECTO,
    UMBRAL_INYECCION,
    Defensas,
)


class DefensasPeticion(BaseModel):
    """Capas de defensa (D91). Por defecto, C2 (D106)."""

    model_config = ConfigDict(extra="forbid")

    separacion_planos: bool = True
    clasificador: bool = True
    precio: bool = False
    umbral: float = Field(default=UMBRAL_INYECCION, ge=0.05, le=0.95)

    def a_defensas(self) -> Defensas:
        return Defensas(self.separacion_planos, self.clasificador, self.precio, self.umbral)


class PeticionConsulta(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    consulta: str | None = Field(
        default=None,
        min_length=3,
        max_length=500,
        description="Consulta en lenguaje natural; en el laboratorio se usa la tarea de la carga.",
    )
    corpus: Literal["b", "a", "vivo"] = "b"  # vivo: tiendas reales y fuentes del visitante
    carga: str | None = Field(
        default=None,
        pattern=r"^A(?:0[1-9]|1[0-9]|20)$",
        description="Laboratorio: ID de la carga plantada (solo corpus B).",
    )
    modelo: str = Field(default="deepseek-flash", max_length=40)
    defensas: DefensasPeticion = Field(default_factory=DefensasPeticion)
    clasificador: str = MODELO_CLASIFICADOR_DEFECTO
    verificar: bool = Field(default=False, description="N3: segunda lectura con Haiku 5.5.")
    politica_n3: Literal["abstener", "excluir"] = "abstener"

    @field_validator("clasificador")
    @classmethod
    def _clasificador_validado(cls, valor: str) -> str:
        if valor not in CLASIFICADORES:
            raise ValueError(f"Clasificador no validado; opciones: {', '.join(CLASIFICADORES)}")
        return valor

    def opciones(self) -> dict[str, Any]:
        return {
            "defensas": self.defensas.model_dump(),
            "configuracion": self.defensas.a_defensas().configuracion or "exploratorio",
            "clasificador": self.clasificador,
            "verificar": self.verificar,
            "politica_n3": self.politica_n3,
        }


class CambioFuente(BaseModel):
    model_config = ConfigDict(extra="forbid")

    activa: bool


class NuevaUrl(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    url: str = Field(min_length=8, max_length=500)
    nombre: str | None = Field(default=None, max_length=120)


class ConsultaCreada(BaseModel):
    id: str
    eventos: str


class ResumenConsulta(BaseModel):
    id: str
    consulta: str
    corpus: str
    carga: str | None
    modelo: str
    opciones: dict[str, Any]
    estado: str
    costo_usd: float
    segundos: float | None
    creada: str


class DetalleConsulta(ResumenConsulta):
    propuesta: dict[str, Any] | None
    detalle: dict[str, Any] | None
    error: str | None


class Historial(BaseModel):
    consultas: list[ResumenConsulta]
    total_consultas: int
    gasto_usd: float  # D90
