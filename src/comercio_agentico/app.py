"""Interfaz mínima del agente de compras (Streamlit).

    uv run streamlit run src/comercio_agentico/app.py      (o ``make app``)

Dos modos:

- **Consulta libre:** el agente real (N2) con un modelo económico; requiere el corpus B servido
  (``make corpus-b-servir``) y la clave en ``.env``. Cuesta del orden de US$0,01-0,03.
- **Tarea del corpus, agente simulado:** responde desde la verdad, sin red ni LLM (US$0); sirve
  para revisar la interfaz y la procedencia sin gastar.
"""

from __future__ import annotations

import asyncio

import pandas as pd
import streamlit as st

from comercio_agentico.agente.grafo import Resultado, pesos, preguntar
from comercio_agentico.arnes.simulado import AgenteSimulado
from comercio_agentico.corpus_b.catalogo import cargar_catalogo
from comercio_agentico.corpus_b.tareas import cargar_tareas
from comercio_agentico.emparejamiento import Emparejador

MODELOS_APP = ["deepseek-flash", "haiku"]  # solo económicos en la interfaz (D: cuidar créditos)
TOPE_USD = 0.10


@st.cache_resource
def emparejador() -> Emparejador:
    return Emparejador(cargar_catalogo())


@st.cache_resource
def simulado() -> AgenteSimulado:
    return AgenteSimulado()


@st.cache_data
def tareas() -> dict[str, str]:
    return {t.id: t.consulta for t in cargar_tareas()}


def cuadro(r: Resultado) -> pd.DataFrame:
    p = r.propuesta
    return pd.DataFrame(
        [
            {
                "": "→" if i == p.recomendada else "",
                "Proveedor": o.proveedor,
                "Producto": o.producto_catalogo or "?",
                "Título publicado": o.titulo,
                "Precio": pesos(o.precio),
                "Envío": "?" if o.costo_envio is None else pesos(o.costo_envio),
                "Total": pesos(o.costo_total),
                "Disponibilidad": o.disponibilidad,
                "Plazo (días)": o.plazo_entrega_dias,
            }
            for i, o in enumerate(p.ofertas)
        ]
    )


def mostrar(r: Resultado) -> None:
    p = r.propuesta
    if p.abstencion:
        st.warning(f"**El agente se abstiene.** {p.motivo_abstencion}")
    else:
        o = p.ofertas[p.recomendada]
        st.success(
            f"**Recomendación:** {o.titulo} en {o.proveedor} por {pesos(o.costo_total)} "
            "(precio + envío)."
        )
    if r.necesidad:
        with st.expander("Necesidad interpretada"):
            st.json(r.necesidad.model_dump(mode="json", exclude_none=True))
    if p.ofertas:
        st.subheader(f"Cuadro comparativo ({len(p.ofertas)} ofertas válidas de {len(r.ofertas)})")
        st.dataframe(cuadro(r), hide_index=True, width="stretch")
    if p.justificacion:
        st.write(p.justificacion)
    for a in p.alertas:
        st.info(f"[{a.tipo}] {a.mensaje}")

    if p.ofertas:
        st.subheader("Procedencia")
        st.caption(
            "Cada cifra apunta al fragmento que la sustenta y a su suma SHA-256: cualquiera "
            "puede volver a la fuente y verificarla."
        )
        for o in p.ofertas:
            pr = o.procedencia
            with st.expander(f"{o.proveedor} · {o.titulo[:70]}"):
                st.markdown(
                    f"- **Fuente:** {pr.fuente} ({pr.tipo_fuente})\n"
                    f"- **Consulta:** `{pr.consulta}`\n"
                    f"- **Extracción:** {pr.ruta_extraccion}"
                    + (f" con `{pr.modelo_extraccion}`" if pr.modelo_extraccion else "")
                    + f"\n- **Marca de tiempo:** {pr.marca_tiempo:%Y-%m-%d %H:%M:%S} UTC"
                    f"\n- **SHA-256:** `{pr.suma_verificacion}`"
                )
                st.code(pr.fragmento_original[:3000], language=None, wrap_lines=True)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Costo", f"US${p.costo_usd:.4f}")
    c2.metric("Tiempo", f"{r.segundos:.0f} s")
    c3.metric("Llamadas al LLM", len(r.llamadas_llm))
    c4.metric("Herramientas", r.llamadas_herramientas)


def main() -> None:
    st.set_page_config(page_title="Comercio agéntico", page_icon="🛒", layout="wide")
    st.title("Agente de compras verificable")
    st.caption("Corpus B sintético · cinco proveedores heterogéneos · separación de planos (C1)")

    modo = st.radio(
        "Modo",
        ["libre", "simulado"],
        format_func=lambda m: {
            "libre": "Consulta libre (agente real, ~US$0,02)",
            "simulado": "Tarea del corpus con agente simulado (US$0)",
        }[m],
        horizontal=True,
    )
    with st.form("consulta"):
        if modo == "libre":
            consulta = st.text_input(
                "¿Qué quiere comprar?",
                placeholder="¿Dónde compro más barato el monitor Samsung M8 de 32 pulgadas?",
            )
            modelo = st.selectbox("Modelo", MODELOS_APP)
        else:
            ids = tareas()
            tarea = st.selectbox("Tarea", list(ids), format_func=lambda i: f"{i} · {ids[i]}")
            consulta, modelo = ids[tarea], "simulado"
        enviar = st.form_submit_button("Buscar", type="primary")

    if enviar and consulta:
        with st.spinner("El agente está consultando a los proveedores..."):
            if modo == "libre":
                r = asyncio.run(
                    preguntar(consulta, modelo=modelo, tope_usd=TOPE_USD, emparejador=emparejador())
                )
            else:
                r = asyncio.run(simulado()(consulta))
        mostrar(r)


main()
