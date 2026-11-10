"""N3 sin red y sin LLM: ruta determinista contra la verdad del corpus, correspondencia entre rutas,
comparación de campos (D101), políticas de E1 (D102) y el detector de errores de E1."""

import asyncio
import json
from pathlib import Path

import pytest
from langchain_core.messages import AIMessage

from comercio_agentico.agente import extraccion
from comercio_agentico.agente.grafo import proponer_con_n3
from comercio_agentico.agente.interpretacion import Necesidad
from comercio_agentico.agente.lectura import datos_estructurados
from comercio_agentico.arnes.e1 import campos_erroneos, detector
from comercio_agentico.corpus_b import DIR_CORPUS, RUTA_PERFIL
from comercio_agentico.corpus_b.catalogo import cargar_catalogo
from comercio_agentico.esquema import Oferta, OfertaExtraida, Procedencia, cargar_perfil
from comercio_agentico.verificacion import (
    INSTRUCCIONES_N3,
    Contraparte,
    contraparte_de,
    discrepancias,
    lectura_determinista,
    mensajes_n3,
    reextraer,
    verificar_oferta,
)

VERDAD = json.loads((DIR_CORPUS / "verdad.json").read_text(encoding="utf-8"))
PRODUCTOS = {p.id: p for p in cargar_catalogo()}
PERFIL = cargar_perfil(RUTA_PERFIL)
TODOS = frozenset({"precio", "costo_envio", "disponibilidad", "plazo_entrega_dias", "gtin"})


def _campos(o) -> tuple:
    return (o.precio, o.costo_envio, o.plazo_entrega_dias, o.disponibilidad, o.gtin)


def _verdad(proveedor: str) -> list[dict]:
    return [o for o in VERDAD["ofertas"] if o["proveedor"] == proveedor]


def test_ruta_determinista_de_p2_coincide_con_la_verdad_en_todas_las_fichas():
    for v in _verdad("P2"):
        nombre = Path(v["ubicacion"]).name
        html = (DIR_CORPUS / "p2_web_schema" / nombre).read_text(encoding="utf-8")
        fragmento = datos_estructurados(html, v["ubicacion"]) + "# ficha"
        (c,) = lectura_determinista(fragmento, "web_schema")
        o = v["oferta"]
        assert _campos(c) == (
            o["precio"],
            o["costo_envio"],
            o["plazo_entrega_dias"],
            o["disponibilidad"],
            o["gtin"],
        ), nombre


def test_ruta_determinista_de_p1_coincide_con_la_verdad():
    inventario = json.loads((DIR_CORPUS / "p1_mcp" / "inventario.json").read_text("utf-8"))
    fragmento = json.dumps(inventario["articulos"], ensure_ascii=False)
    por_gtin = {c.gtin: c for c in lectura_determinista(fragmento, "mcp")}
    for v in _verdad("P1"):
        o = v["oferta"]
        c = por_gtin[o["gtin"]]
        assert _campos(c) == (
            o["precio"],
            o["costo_envio"],
            o["plazo_entrega_dias"],
            o["disponibilidad"],
            o["gtin"],
        )


def _bloque(objetos) -> str:
    return (
        "Datos estructurados de la página (schema.org):\n"
        + json.dumps(objetos)
        + "\n\nContenido de la página:\ntexto"
    )


def test_varias_ofertas_con_precios_distintos_son_ambiguas_y_van_al_llm():
    falabella = {
        "@type": "Product",
        "name": "iPhone",
        "offers": [{"price": "2799900"}, {"price": "3599900"}],
    }
    assert lectura_determinista(_bloque([falabella]), "web_schema") is None
    recortado = _bloque([falabella])[:80] + " …(recortado)\n\nContenido de la página:\n"
    assert lectura_determinista(recortado, "web_schema") is None
    assert lectura_determinista("# Listado sin datos estructurados", "web_plana") is None


def test_campo_que_el_parser_no_publica_no_se_verifica():
    alkosto = {
        "@type": "Product",
        "name": "Yoga 7",
        "offers": {"price": "10599000.0", "availability": "https://schema.org/OutOfStock"},
    }
    (c,) = lectura_determinista(_bloque([alkosto]), "web_schema")
    assert c.publicados == {"precio", "disponibilidad"}
    o = OfertaExtraida(titulo="Yoga 7", precio=10_599_000, disponibilidad="agotado", costo_envio=0)
    assert discrepancias(o, c) == []  # el envío no lo publica el parser: no cuenta
    assert discrepancias(o.model_copy(update={"precio": 9_999_000}), c) == ["precio"]


def test_con_el_llm_un_nulo_frente_a_un_valor_si_es_discrepancia():
    c = Contraparte(
        titulo="m8", precio=100, costo_envio=None, disponibilidad="desconocida", publicados=TODOS
    )
    o = OfertaExtraida(titulo="m8", precio=100, costo_envio=25_000)
    assert discrepancias(o, c) == ["costo_envio"]
    # el GTIN solo se compara si ambas rutas lo traen
    con_gtin = OfertaExtraida(titulo="m8", precio=100, gtin="9520000000011")
    sin_gtin = Contraparte(titulo="m8", precio=100, disponibilidad="desconocida", publicados=TODOS)
    assert discrepancias(con_gtin, sin_gtin) == []


def test_correspondencia_escalonada():
    a = Contraparte(titulo="Otro nombre", precio=1, gtin="9520000000011")
    b = Contraparte(titulo="x", precio=2, url_detalle="http://t/c02.html")
    c = Contraparte(titulo="Samsung Smart Monitor M8 64GB", precio=3)
    candidatas = [a, b, c]
    assert (
        contraparte_de(OfertaExtraida(titulo="z", precio=1, gtin="9520000000011"), candidatas) is a
    )
    assert (
        contraparte_de(
            OfertaExtraida(titulo="z", precio=1, url_detalle="http://t/c02.html"), candidatas
        )
        is b
    )
    assert (
        contraparte_de(
            OfertaExtraida(titulo="samsung smart monitor m8 64 gb", precio=1), candidatas
        )
        is c
    )
    sola = OfertaExtraida(titulo="Audífonos JBL Tune", precio=1)
    assert verificar_oferta(sola, "reextraccion", candidatas).estado == "sin_contraparte"


class Doble:
    def __init__(self, respuesta):
        self.respuesta, self.vistos = respuesta, []

    async def ainvoke(self, mensajes, config=None):
        self.vistos.append(mensajes)
        return self.respuesta


def test_reextraccion_usa_otro_prompt_y_tolera_salida_cruda():
    crudo = AIMessage(json.dumps({"ofertas": [{"titulo": "monitor", "precio": 2500000}]}))
    doble = Doble({"parsed": None, "raw": crudo})
    (c,) = asyncio.run(reextraer("carlos: monitor a 2.500.000", doble))
    assert c.precio == 2_500_000 and c.publicados == TODOS
    sistema = doble.vistos[0][0].content
    assert sistema == INSTRUCCIONES_N3 and extraccion.INSTRUCCIONES not in sistema
    assert "Proveedor:" not in mensajes_n3("x")[1].content  # no recibe los metadatos del extractor


# --------------------------------------------------------------------------------------------------
# Políticas de D102


def _oferta(proveedor: str, precio: float, verificacion: str) -> Oferta:
    return Oferta(
        titulo=PRODUCTOS["C11"].titulo,
        precio=precio,
        costo_envio=0,
        disponibilidad="en_stock",
        plazo_entrega_dias=2,
        procedencia=Procedencia(
            fuente=proveedor,
            tipo_fuente="mensaje",
            consulta="u",
            fragmento_original="f",
            ruta_extraccion="llm",
            modelo_extraccion="doble",
        ),
        producto_catalogo="C11",
        verificacion=verificacion,
    )


NECESIDAD = Necesidad(producto_mencionado="Samsung M8 64GB", producto_id="C11")


@pytest.mark.parametrize(
    ("politica", "abstencion", "proveedor"),
    [("abstener", True, None), ("excluir", False, "P1")],
)
def test_politicas_ante_la_ganadora_no_verificada(politica, abstencion, proveedor):
    ofertas = [_oferta("P5", 2_000_000, "discrepancia"), _oferta("P1", 2_100_000, "verificada")]
    p = proponer_con_n3("q", NECESIDAD, ofertas, PERFIL, PRODUCTOS, [], "d", 0.0, politica=politica)
    assert p.abstencion is abstencion
    assert any(a.tipo == "sin_verificar" for a in p.alertas)
    if proveedor:
        assert p.ofertas[p.recomendada].proveedor == proveedor


def test_abstener_no_cambia_nada_si_la_ganadora_esta_verificada():
    ofertas = [_oferta("P5", 2_000_000, "verificada"), _oferta("P1", 2_100_000, "discrepancia")]
    p = proponer_con_n3("q", NECESIDAD, ofertas, PERFIL, PRODUCTOS, [], "d", 0.0)
    assert not p.abstencion and p.ofertas[p.recomendada].proveedor == "P5"


# --------------------------------------------------------------------------------------------------
# E1: detector de errores de extracción


def test_detector_cruza_marcadas_con_errores_frente_a_la_verdad():
    v = _verdad("P1")[0]
    buena = {
        **v["oferta"],
        "producto_catalogo": v["producto_id"],
        "procedencia": {"fuente": "P1", "tipo_fuente": "mcp", "consulta": "mcp://P1"},
    }
    mala = {**buena, "precio": buena["precio"] + 1000}
    assert campos_erroneos(buena, VERDAD) == []
    assert campos_erroneos(mala, VERDAD) == ["precio"]
    filas = [
        {"oferta": mala, "estado": "discrepancia"},  # VP
        {"oferta": buena, "estado": "sin_contraparte"},  # FP
        {"oferta": mala, "estado": "verificada"},  # FN
        {"oferta": buena, "estado": "verificada"},  # VN
    ]
    d = detector(filas, VERDAD)
    assert (d["vp"], d["fp"], d["fn"], d["vn"]) == (1, 1, 1, 1)
