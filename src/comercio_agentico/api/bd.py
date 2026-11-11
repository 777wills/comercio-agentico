"""Persistencia de consultas y propuestas con SQLAlchemy 2.x.

PostgreSQL en local (``docker compose up -d bd``) y en el despliegue; SQLite en memoria en las
pruebas, con el mismo código. La clave de OpenRouter del visitante nunca se guarda (D82).
"""

from __future__ import annotations

import os
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import JSON, DateTime, Float, String, Text, create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker
from sqlalchemy.pool import StaticPool

URL_BD_LOCAL = "postgresql+psycopg://cotia:cotia@127.0.0.1:5433/cotia"


class Base(DeclarativeBase):
    pass


class ConsultaBD(Base):
    __tablename__ = "consultas"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    visitante: Mapped[str] = mapped_column(String(36), index=True)
    consulta: Mapped[str] = mapped_column(Text)
    corpus: Mapped[str] = mapped_column(String(4))
    carga: Mapped[str | None] = mapped_column(String(4))
    modelo: Mapped[str] = mapped_column(String(40))
    opciones: Mapped[dict[str, Any]] = mapped_column(JSON)  # defensas, clasificador, N3
    estado: Mapped[str] = mapped_column(String(12))  # en_cola, en_curso, terminada, error
    propuesta: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    detalle: Mapped[dict[str, Any] | None] = mapped_column(JSON)  # necesidad, herramientas...
    eventos: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    costo_usd: Mapped[float] = mapped_column(Float, default=0.0)
    segundos: Mapped[float | None] = mapped_column(Float)
    error: Mapped[str | None] = mapped_column(Text)
    creada: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )


def crear_motor(url: str | None = None) -> Engine:
    url = url or os.getenv("COTIA_BD_URL", URL_BD_LOCAL)
    if url in ("sqlite://", "sqlite:///:memory:"):  # una sola conexión compartida entre hilos
        motor = create_engine(url, connect_args={"check_same_thread": False}, poolclass=StaticPool)
    else:
        motor = create_engine(url, pool_pre_ping=True)
    Base.metadata.create_all(motor)
    return motor


def fabrica_sesiones(motor: Engine) -> sessionmaker:
    return sessionmaker(motor, expire_on_commit=False)
