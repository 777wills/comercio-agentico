"""Agente simulado para probar el arnés sin red, sin LLM y sin costo.

Responde desde ``verdad.json`` como lo haría un agente perfecto e introduce errores conocidos y
deterministas, para que las métricas tengan algo que detectar:

- cada ``cada_n_precio`` ofertas, el precio extraído se desvía un 10 % (error de extracción, M1);
- cada ``cada_n_fallo`` tareas con respuesta, recomienda la oferta válida más cara (fallo, M2);
- las tareas ``sin_respuesta`` en posición impar no se abstienen (abstención omitida, M4).
"""

from __future__ import annotations

import asyncio
import zlib
from typing import Any

from comercio_agentico.agente.grafo import Resultado
from comercio_agentico.corpus_b.generar import cargar_verdad
from comercio_agentico.corpus_b.tareas import Tarea, cargar_tareas
from comercio_agentico.esquema import Oferta, Procedencia, PropuestaCompra


class AgenteSimulado:
    def __init__(
        self,
        tareas: list[Tarea] | None = None,
        verdad: dict | None = None,
        *,
        cada_n_precio: int = 7,
        cada_n_fallo: int = 6,
        espera_s: float = 0.0,
    ) -> None:
        self.tareas = {t.consulta: t for t in (tareas or cargar_tareas())}
        self.posicion = {t.id: i for i, t in enumerate(self.tareas.values())}
        verdad = verdad or cargar_verdad()
        self.indice = {(o["proveedor"], o["producto_id"]): o for o in verdad["ofertas"]}
        self.cada_n_precio, self.cada_n_fallo, self.espera_s = cada_n_precio, cada_n_fallo, espera_s

    def _oferta(self, prov: str, pid: str) -> Oferta:
        v = self.indice[(prov, pid)]
        datos = dict(v["oferta"])
        if zlib.crc32(f"{prov}{pid}".encode()) % self.cada_n_precio == 0:
            datos["precio"] = round(datos["precio"] * 1.1)
        fragmento = f"{v['tipo_fuente']}:{v['ubicacion']}"
        return Oferta(
            **datos,
            procedencia=Procedencia(
                fuente=prov,
                tipo_fuente=v["tipo_fuente"],
                consulta=v["ubicacion"],
                fragmento_original=fragmento,
                ruta_extraccion="determinista",
            ),
            producto_catalogo=pid,
        )

    async def __call__(self, consulta: str, *, modelo: str = "simulado", **_: Any) -> Resultado:
        if self.espera_s:
            await asyncio.sleep(self.espera_s)
        t = self.tareas[consulta]
        pos = self.posicion[t.id]
        ofertas = [self._oferta(p, pid) for p, pid in t.respuesta.ofertas_validas]
        costo = 0.001 * (1 + pos % 5)
        omite_abstencion = t.respuesta.abstencion and pos % 2 == 1
        if t.respuesta.abstencion and not omite_abstencion:
            propuesta = PropuestaCompra(
                consulta=consulta,
                perfil="electronica",
                abstencion=True,
                motivo_abstencion="Ninguna oferta cumple",
                modelo=modelo,
                costo_usd=costo,
            )
        else:
            if omite_abstencion:  # recomienda cualquier oferta del corpus: error de abstención
                ofertas = [self._oferta(*next(iter(self.indice)))]
                elegida = 0
            elif pos % self.cada_n_fallo == 0 and len(ofertas) > 1:
                elegida = len(ofertas) - 1  # la más cara: fallo de selección
            else:
                elegida = (
                    next(
                        i
                        for i, o in enumerate(ofertas)
                        if (o.proveedor, o.producto_catalogo)
                        == (t.respuesta.proveedor, t.respuesta.producto_id)
                    )
                    if not t.acepta_cualquier_valida
                    else 0
                )
            propuesta = PropuestaCompra(
                consulta=consulta,
                perfil="electronica",
                ofertas=ofertas,
                recomendada=elegida,
                justificacion="simulada",
                modelo=modelo,
                costo_usd=costo,
            )
        llamadas = [
            {
                "modelo": modelo,
                "tokens_entrada": 4000,
                "tokens_salida": 300,
                "costo_usd": costo,
                "proveedor": "simulado",
            }
        ]
        return Resultado(propuesta, None, ofertas, 3, llamadas, 10.0 + pos, [])
