"""El corpus B es coherente: lo publicado en cada formato coincide con la verdad, y cada tarea tiene
la respuesta que se deriva de ella. Sin red y sin LLM."""

import asyncio
import json
import re
import shutil
from collections import Counter

import pytest
from fastmcp import Client
from pypdf import PdfReader

from comercio_agentico.corpus_b import DIR_CORPUS, RUTA_PERFIL
from comercio_agentico.corpus_b.catalogo import (
    ATRIBUTOS_POR_CATEGORIA,
    cargar_catalogo,
    gtin13,
    reparar,
    validar_catalogo,
)
from comercio_agentico.corpus_b.generar import cargar_verdad, generar
from comercio_agentico.corpus_b.render import DISPONIBILIDAD_SCHEMA, pesos, precio_informal
from comercio_agentico.corpus_b.servidor_mcp import crear_servidor
from comercio_agentico.corpus_b.tareas import (
    CUOTAS,
    Criterios,
    calcular_respuesta,
    cargar_tareas,
)
from comercio_agentico.esquema import OfertaExtraida, cargar_perfil, gtin_valido


@pytest.fixture(scope="module")
def catalogo():
    return cargar_catalogo()


@pytest.fixture(scope="module")
def verdad():
    return cargar_verdad()


def ofertas_de(verdad, proveedor):
    return [o for o in verdad["ofertas"] if o["proveedor"] == proveedor]


# --- Catálogo ---------------------------------------------------------------------------------


def test_catalogo_completo_y_valido(catalogo):
    assert len(catalogo) == 40
    assert Counter(p.categoria for p in catalogo) == dict.fromkeys(ATRIBUTOS_POR_CATEGORIA, 8)
    assert all(gtin_valido(p.gtin) and len(p.gtin) == 13 for p in catalogo)
    validar_catalogo(catalogo, cargar_perfil(RUTA_PERFIL))


def test_gtin_sintetico_y_reparacion():
    assert gtin_valido(gtin13(7)) and gtin13(7).startswith("200")
    reparado = reparar(
        {
            "atributos": {
                "almacenamiento": 2000,
                "tipo_almacenamiento": "SSD",
                "velocidad_lectura": 1050,
                "alias_pdf": "X",
            }
        },
        "almacenamiento",
    )
    assert reparado["atributos"] == {
        "almacenamiento": 2048,
        "tipo_almacenamiento": "SSD",
        "velocidad_lectura": 1050,
    }


# --- Verdad y generación ----------------------------------------------------------------------


def test_verdad_valida_y_reparto(verdad, catalogo):
    for o in verdad["ofertas"]:
        OfertaExtraida.model_validate(o["oferta"])
        assert o["ubicacion"]
    vendidos = {o["producto_id"] for o in verdad["ofertas"]}
    assert vendidos.isdisjoint(verdad["productos_sin_oferta"])
    assert vendidos | set(verdad["productos_sin_oferta"]) == {p.id for p in catalogo}
    assert {o["proveedor"] for o in verdad["ofertas"]} == {"P1", "P2", "P3", "P4", "P5"}
    # Solo los proveedores maduros publican GTIN.
    assert all(
        (o["oferta"]["gtin"] is not None) == (o["proveedor"] in {"P1", "P2"})
        for o in verdad["ofertas"]
    )


def test_generacion_determinista(tmp_path, verdad):
    shutil.copy(DIR_CORPUS / "catalogo.json", tmp_path / "catalogo.json")
    nueva = generar(tmp_path)
    assert nueva["ofertas"] == verdad["ofertas"]
    original = (DIR_CORPUS / "p4_pdf" / "lista_precios.pdf").read_bytes()
    assert (tmp_path / "p4_pdf" / "lista_precios.pdf").read_bytes() == original


# --- Cada proveedor publica exactamente su verdad ---------------------------------------------


def test_p1_mcp_coincide_con_verdad(verdad):
    async def consultar():
        async with Client(crear_servidor()) as cliente:
            herramientas = {h.name for h in await cliente.list_tools()}
            assert herramientas == {"buscar_productos", "detalle_producto"}
            for o in ofertas_de(verdad, "P1"):
                referencia = o["ubicacion"].rsplit("/", 1)[-1]
                ficha = (
                    await cliente.call_tool("detalle_producto", {"referencia": referencia})
                ).data
                assert ficha["ean"] == o["oferta"]["gtin"]
                assert ficha["valor_unitario_cop"] == o["oferta"]["precio"]
                agotado = ficha["existencias"] == 0 and not ficha["a_pedido"]
                assert agotado == (o["oferta"]["disponibilidad"] == "agotado")
            hallados = (await cliente.call_tool("buscar_productos", {"texto": "samsung"})).data
            assert hallados and all("samsung" in h["descripcion"].lower() for h in hallados)

    asyncio.run(consultar())


def test_p2_jsonld_coincide_con_verdad(verdad):
    for o in ofertas_de(verdad, "P2"):
        html = (DIR_CORPUS / o["ubicacion"]).read_text(encoding="utf-8")
        bloque = re.search(r'<script type="application/ld\+json">(.*?)</script>', html, re.S)
        datos = json.loads(bloque.group(1).replace("<\\/", "</"))
        of = o["oferta"]
        assert datos["gtin13"] == of["gtin"]
        assert datos["offers"]["price"] == of["precio"]
        assert datos["offers"]["availability"] == DISPONIBILIDAD_SCHEMA[of["disponibilidad"]]
        envio = datos["offers"]["shippingDetails"]
        assert envio["shippingRate"]["value"] == of["costo_envio"]
        assert envio["deliveryTime"]["transitTime"]["maxValue"] == of["plazo_entrega_dias"]


def test_p3_tarjeta_coincide_con_verdad(verdad):
    for o in ofertas_de(verdad, "P3"):
        ruta, ancla = o["ubicacion"].split("#")
        html = (DIR_CORPUS / ruta).read_text(encoding="utf-8")
        tarjeta = html.split(f'id="{ancla}"')[1].split('<div class="card"')[0]
        of = o["oferta"]
        assert f"$ {pesos(of['precio'])}" in tarjeta
        assert f"{of['plazo_entrega_dias']} días hábiles" in tarjeta
        assert "EAN" not in tarjeta and "ld+json" not in html


def test_p4_pdf_coincide_con_verdad(verdad):
    texto = PdfReader(DIR_CORPUS / "p4_pdf" / "lista_precios.pdf").pages[0].extract_text()
    filas = {linea.split(" ", 1)[0]: linea for linea in texto.splitlines()}
    for o in ofertas_de(verdad, "P4"):
        codigo = o["ubicacion"].split("#")[1]
        assert o["oferta"]["titulo"] in filas[codigo]
        assert pesos(o["oferta"]["precio"]) in filas[codigo]


def leer_precio_informal(texto: str) -> int:
    """Inversa de los formatos de chat, para comprobar que todos son exactos."""
    if m := re.search(r"(\d+)'(\d{3})\.(\d{3})", texto):
        return int("".join(m.groups()))
    if m := re.search(r"(\d+) mil\b", texto):
        return int(m.group(1)) * 1000
    m = re.search(r"\$?(\d{1,3}(?:\.\d{3})+)", texto)
    return int(m.group(1).replace(".", ""))


@pytest.mark.parametrize("valor", [2_350_000, 500_000, 45_000, 12_005_000, 1_000_000])
def test_precio_informal_es_exacto(valor):
    import random

    azar = random.Random(valor)
    for _ in range(20):
        assert leer_precio_informal(precio_informal(valor, azar)) == valor


def test_p5_mensaje_coincide_con_verdad(verdad):
    lineas = (DIR_CORPUS / "p5_mensaje" / "chat.txt").read_text(encoding="utf-8").splitlines()
    for o in ofertas_de(verdad, "P5"):
        numero = int(o["ubicacion"].split("#L")[1])
        mensaje = lineas[numero - 1].split(": ", 1)[1]
        assert o["oferta"]["titulo"] in mensaje
        assert (
            leer_precio_informal(mensaje.replace(o["oferta"]["titulo"], ""))
            == o["oferta"]["precio"]
        )


# --- Tareas -----------------------------------------------------------------------------------


@pytest.fixture(scope="module")
def tareas():
    return cargar_tareas()


def test_sesenta_tareas_por_categoria(tareas):
    assert len(tareas) == 60
    assert len({t.id for t in tareas}) == len({t.consulta for t in tareas}) == 60
    conteo = Counter(t.categoria for t in tareas)
    for categoria, cuota in CUOTAS.items():
        assert conteo[categoria] == cuota
    assert conteo["restricciones"] == 60 - sum(CUOTAS.values())


def test_respuesta_derivable_de_la_verdad(tareas, verdad, catalogo):
    for t in tareas:
        assert calcular_respuesta(t.criterios, verdad, catalogo) == t.respuesta, t.id
        assert t.respuesta.abstencion == (t.categoria == "sin_respuesta"), t.id


def test_minimo_unico_en_tareas_de_respuesta_exacta(tareas, verdad):
    costo = {
        (o["proveedor"], o["producto_id"]): o["oferta"]["precio"] + o["oferta"]["costo_envio"]
        for o in verdad["ofertas"]
    }
    for t in tareas:
        if t.respuesta.abstencion or t.acepta_cualquier_valida:
            continue
        costos = [costo[tuple(v)] for v in t.respuesta.ofertas_validas]
        assert costos == sorted(costos)
        assert len(costos) < 2 or costos[0] < costos[1], t.id


def test_criterios_filtran_agotados(verdad, catalogo):
    for pid in verdad["productos_solo_agotados"]:
        assert calcular_respuesta(Criterios(productos=[pid]), verdad, catalogo).abstencion
