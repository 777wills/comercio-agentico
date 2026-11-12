"""D115 b y D120 (C2 en páginas reales) sin red ni modelo: rasgos, tipos de página y análisis."""

import json

from comercio_agentico.agente.defensa import CLASIFICADORES
from comercio_agentico.agente.fuentes import TIENDAS_EN_VIVO
from comercio_agentico.ataques.c2_reales import (
    a_markdown,
    calcular,
    cargar_paginas,
    rasgos,
    semillas,
    tipo_pagina,
)

H, W = list(CLASIFICADORES)


def ventana(h, w, precio=False):
    return {
        "caracteres": 100,
        "precio": precio,
        "schema": False,
        "fraccion_enlaces": 0.5,
        "puntajes": {H: h, W: w},
    }


def pagina(url, tienda, tipo, crudo, saneado=(), error=None):
    fila = {
        "url": url,
        "tienda": tienda,
        "tipo": tipo,
        "fecha": "2026-11-11T12:00:00+00:00",
        "error": error,
    }
    if not error:
        fila["condiciones"] = {
            "crudo": {"caracteres": 100 * len(crudo), "ventanas": list(crudo)},
            "saneado": {"caracteres": 100 * len(saneado), "ventanas": list(saneado)},
        }
    return fila


def test_rasgos_no_guardan_texto():
    r = rasgos("Datos estructurados de la página (schema.org):\n[Celular](/p/1) $ 1.599.900")
    assert r["precio"] and r["schema"]
    assert 0 < r["fraccion_enlaces"] < 1
    assert set(r) == {"caracteres", "precio", "schema", "fraccion_enlaces"}


def test_tipo_de_pagina_por_url():
    alkosto = TIENDAS_EN_VIVO[0]
    assert tipo_pagina(alkosto.url, alkosto) == "portada"
    assert tipo_pagina("https://www.alkosto.com/x/p/123", alkosto) == "ficha"
    assert tipo_pagina("https://www.alkosto.com/celulares/c/BI_101", alkosto) == "categoría"


def test_semillas_van_a_las_tres_tiendas_del_corpus_a():
    s = semillas()
    assert set(s) == {"V1", "V2", "V3"}
    assert len(s["V1"]) == len(s["V2"]) == len(s["V3"]) == 12


def test_calcular_cuenta_ventanas_paginas_curva_y_pareo():
    limpia = ventana(0.1, 0.1, precio=True)
    filas = [
        pagina(
            "u1", "V1", "portada", [ventana(0.9, 0.1, precio=True), ventana(0.1, 0.1)], [limpia]
        ),
        pagina("u2", "V1", "ficha", [ventana(0.2, 0.0), ventana(0.55, 0.0)], [ventana(0.6, 0.0)]),
        pagina("u3", "V3", "ficha", [], error="UrlNoPermitida: robots"),
    ]
    r = calcular(filas)
    assert r["paginas_leidas"] == 2 and r["errores"] == {"UrlNoPermitida": 1}
    assert r["caracteres"] == {"crudo": 400, "saneado": 200}
    h = r["clasificadores"][H]
    g = h["crudo"]["global"]
    assert (g["ventanas"]["k"], g["ventanas"]["n"]) == (2, 4)
    assert g["paginas_con_retiro"]["k"] == 2
    assert g["ventanas_con_precio"]["k"] == 1
    assert h["saneado"]["global"]["ventanas"]["k"] == 1
    assert h["pareo_paginas"] == {"solo_crudo": 1, "ambas": 1, "solo_saneado": 0, "ninguna": 0}
    assert r["clasificadores"][W]["crudo"]["global"]["ventanas"]["k"] == 0
    assert h["crudo"]["curva_umbral"]["0.6"]["ventanas"] == 0.25
    assert h["crudo"]["por_tipo"]["ficha"]["paginas"] == 1
    assert "Total" in a_markdown(r)


def test_reanudar_se_queda_con_la_ultima_lectura_por_url(tmp_path):
    ruta = tmp_path / "paginas.jsonl"
    filas = [pagina("u1", "V1", "ficha", [], error="OSError: x"), pagina("u1", "V1", "ficha", [])]
    ruta.write_text("\n".join(json.dumps(f) for f in filas) + "\n", encoding="utf-8")
    assert cargar_paginas(ruta) == [filas[1]]
