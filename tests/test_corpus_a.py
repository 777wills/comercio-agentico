"""Corpus A sin red: hechos → catálogo, verdad, tiendas reconstruidas y tareas (S04, D70)."""

import json

import pytest

from comercio_agentico.corpus_a import RUTA_HECHOS
from comercio_agentico.corpus_a.construir import (
    _precio_a3,
    atributos_del_titulo,
    construir_catalogo,
    construir_sitio,
    gtin13,
)
from comercio_agentico.corpus_a.recolectar import extraer_hechos, precios_etiquetados
from comercio_agentico.corpus_a.tareas import generar

HECHOS = [json.loads(linea) for linea in RUTA_HECHOS.read_text(encoding="utf-8").splitlines()]


@pytest.fixture(scope="module")
def catalogo():
    import yaml

    from comercio_agentico.corpus_a import RUTA_SEMILLAS

    categorias = {
        s["id"]: s["categoria"] for s in yaml.safe_load(RUTA_SEMILLAS.read_text())["productos"]
    }
    return construir_catalogo(HECHOS, categorias)


def test_upc_de_12_digitos_se_lleva_a_gtin13():
    assert gtin13("887276836881") == "0887276836881"
    assert gtin13("887276836882") is None  # dígito de control inválido


def test_atributos_solo_los_que_el_titulo_publica():
    t = (
        'Computador Portátil ASUS Zenbook S14 OLED 14" Pulgadas - Intel Core Ultra 7 258V - '
        "RAM 32GB - Disco SSD 1 TB SSD - Gris"
    )
    a = atributos_del_titulo(t, "portatil")
    assert a == {
        "tamano_pantalla": 14.0,
        "memoria_ram": 32,
        "almacenamiento": 1024,
        "procesador": "Intel Core Ultra 7 258V",
    }
    assert atributos_del_titulo("iPhone 15 128 GB 5G Azul", "celular") == {"almacenamiento": 128}


def test_precio_de_falabella_excluye_el_de_tarjeta_y_el_tachado():
    html = (
        # Primero, el arreglo de otra variante (no contiene los precios del JSON-LD).
        '{"prices":[{"type":"internetPrice","price":["4.599.900"],"crossed":false}]},'
        '{"prices":[{"type":"cmrPrice","price":["869.900"],"crossed":false,"validity":"15/11/2026"},'
        '{"type":"eventPrice","price":["899.900"],"crossed":false},'
        '{"type":"normalPrice","price":["1.600.000"],"crossed":true}]}'
    )
    etiquetados = precios_etiquetados(html, precios_ld=[899_900, 869_900])
    assert [p["tipo"] for p in etiquetados] == ["cmrPrice", "eventPrice", "normalPrice"]
    assert _precio_a3({"precios_etiquetados": etiquetados, "ofertas": []}) == 899_900


def test_catalogo_un_producto_por_ean_con_gtin_valido(catalogo):
    assert len(catalogo) == 24  # R15 ya no se publica en Alkosto ni en Ktronix
    assert len({p.gtin for p in catalogo}) == 24


def test_la_tienda_reconstruida_conserva_la_estructura_de_la_original(catalogo, tmp_path):
    """El mismo extractor que leyó la tienda real lee igual la reconstruida: microdatos en A1 y
    A2, JSON-LD con dos ofertas sin etiqueta en A3, mismos títulos y precios."""
    construir_sitio(HECHOS, catalogo, tmp_path)
    comparadas = 0
    for h in HECHOS:
        ruta = tmp_path / h["tienda"].lower() / f"{h['producto'].lower()}.html"
        if not ruta.exists() or not h.get("ofertas"):
            continue
        r = extraer_hechos(ruta.read_text(encoding="utf-8"), "http://127.0.0.1/")
        assert r["sintaxis"] == h["sintaxis"]
        assert r["titulo"] == h["titulo"]
        if h["tienda"] != "A3":
            assert r["ofertas"][0]["precio"] == h["ofertas"][0]["precio"]
            assert r["ofertas"][0]["disponibilidad"] == h["ofertas"][0]["disponibilidad"]
        comparadas += 1
    assert comparadas > 40


def test_tareas_clave_del_corpus_a():
    tareas = {t.id: t for t in generar()}
    assert len(tareas) == 20
    # Acer ED270: solo Falabella tiene existencias; vale el precio sin tarjeta CMR.
    assert (tareas["A003"].respuesta.proveedor, tareas["A003"].respuesta.costo_total) == (
        "A3",
        899_900,
    )
    # Lenovo Yoga 7: agotado en todas; el X1 Yoga de Falabella es otro producto.
    assert tareas["A018"].respuesta.abstencion
    assert sum(t.respuesta.abstencion for t in tareas.values()) == 4


def test_lectura_web_agrega_los_datos_schema_org(catalogo, tmp_path):
    """D74: el texto que lee el agente trae los datos schema.org (donde está la disponibilidad),
    tanto en microdatos (A1) como en JSON-LD (A3); el Markdown de crawl4ai los perdía."""
    from comercio_agentico.agente.lectura import datos_estructurados

    construir_sitio(HECHOS, catalogo, tmp_path)
    for tienda in ("a1", "a3"):
        ficha = next(p for p in sorted((tmp_path / tienda).glob("r*.html")))
        bloque = datos_estructurados(ficha.read_text(encoding="utf-8"), "http://127.0.0.1/")
        assert bloque.startswith("Datos estructurados de la página (schema.org):")
        assert "schema.org/InStock" in bloque or "schema.org/OutOfStock" in bloque
        assert '"price"' in bloque


def test_datos_schema_org_vacio_roto_y_recortado():
    from comercio_agentico.agente.lectura import MAX_DATOS_ESTRUCTURADOS, datos_estructurados

    assert datos_estructurados("<html><body><p>Hola</p></body></html>", "http://x/") == ""
    assert datos_estructurados("", "http://x/") == ""
    enorme = json.dumps({"@type": "Product", "description": "x" * 20_000})
    bloque = datos_estructurados(
        f'<script type="application/ld+json">{enorme}</script>', "http://x/"
    )
    assert bloque.count("x") < MAX_DATOS_ESTRUCTURADOS + 100
    assert "…(recortado)" in bloque
