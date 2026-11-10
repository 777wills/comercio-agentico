"""Arnés y métricas sin red ni LLM: el agente simulado siembra errores conocidos y las métricas
deben encontrarlos exactamente."""

import asyncio
import json

import pytest

from comercio_agentico.arnes import metricas
from comercio_agentico.arnes.correr import (
    ConfigCorrida,
    correr,
    hash_corpus,
    version_prompt,
)
from comercio_agentico.arnes.simulado import AgenteSimulado
from comercio_agentico.corpus_b.generar import cargar_verdad
from comercio_agentico.corpus_b.tareas import cargar_tareas

TAREAS = cargar_tareas()
VERDAD = cargar_verdad()
CONFIG = ConfigCorrida(nombre="prueba", concurrencia_tareas=8, concurrencia_llm=2)


def _correr(salida, tareas=TAREAS, reps=1, agente=None):
    agente = agente or AgenteSimulado(TAREAS, VERDAD)
    return asyncio.run(
        correr(CONFIG, tareas, reps, salida, preguntar_fn=agente, emparejador="no se usa")
    )


def test_wilson_y_bootstrap():
    w = metricas.wilson(7, 10)
    assert w["p"] == 0.7 and 0.39 < w["bajo"] < 0.40 and 0.89 < w["alto"] < 0.90
    assert metricas.wilson(0, 0)["p"] is None
    b = metricas.bootstrap([1.0, 2.0, 3.0, 4.0])
    assert b["valor"] == 2.5 and b["bajo"] < 2.5 < b["alto"]
    assert metricas.bootstrap([5.0])["bajo"] == 5.0


def test_huellas_estables():
    assert version_prompt() == version_prompt() and len(version_prompt()) == 12
    assert len(hash_corpus()) == 12


def test_corrida_registra_todo_y_reanuda(tmp_path):
    salida = tmp_path / "c.jsonl"
    filas = _correr(salida, TAREAS[:10], reps=2)
    assert len(filas) == 20
    fila = json.loads(salida.read_text().splitlines()[0])
    for clave in (
        "repeticion",
        "categoria",
        "evaluacion",
        "ofertas_todas",
        "costo_usd",
        "segundos",
    ):
        assert clave in fila
    assert "fragmento_original" not in json.dumps(fila["ofertas_todas"])
    # Reanudar no repite lo ya registrado.
    assert _correr(salida, TAREAS[:10], reps=2) == []
    assert len(_correr(salida, TAREAS[:12], reps=2)) == 4


def test_error_de_una_tarea_no_detiene_la_corrida(tmp_path):
    simulado = AgenteSimulado(TAREAS, VERDAD)

    async def fallon(consulta, **kw):
        if consulta == TAREAS[1].consulta:
            raise RuntimeError("se cayó el proveedor")
        return await simulado(consulta, **kw)

    filas = _correr(tmp_path / "e.jsonl", TAREAS[:3], agente=fallon)
    errores = [f for f in filas if f["error"]]
    assert len(filas) == 3 and len(errores) == 1
    m = metricas.calcular(filas, TAREAS, VERDAD)
    assert m["M2"]["errores"] == 1


@pytest.fixture(scope="module")
def corrida(tmp_path_factory):
    salida = tmp_path_factory.mktemp("c") / "sim.jsonl"
    filas = _correr(salida, reps=2)
    return filas, metricas.calcular(filas, TAREAS, VERDAD)


def test_m1_detecta_exactamente_los_precios_desviados(corrida):
    filas, m = corrida
    simulado = AgenteSimulado(TAREAS, VERDAD)
    desviadas = sum(
        o["precio"]
        != simulado.indice[(o["procedencia"]["fuente"], o["producto_catalogo"])]["oferta"]["precio"]
        for f in filas
        for o in f["ofertas_todas"]
    )
    precio = [d["campos"]["precio"] for d in m["M1"]["por_fuente"].values()]
    assert sum(w["n"] - w["k"] for w in precio) == desviadas > 0
    # Los demás campos salen de la verdad tal cual: exactitud perfecta.
    for d in m["M1"]["por_fuente"].values():
        for campo, w in d["campos"].items():
            if campo != "precio":
                assert w["k"] == w["n"]
    assert m["M1"]["recoleccion"]["p"] == 1.0


def test_m2_m4_cuentan_los_fallos_sembrados(corrida):
    _, m = corrida
    sin_resp = [t for t in TAREAS if t.respuesta.abstencion]
    pos = {t.id: i for i, t in enumerate(TAREAS)}
    omitidas = sum(pos[t.id] % 2 == 1 for t in sin_resp)
    assert m["M4"]["abstencion_correcta"]["k"] == 2 * (len(sin_resp) - omitidas)
    assert m["M4"]["abstencion_indebida"]["k"] == 0
    fallos_seleccion = sum(
        pos[t.id] % 6 == 0
        and len(t.respuesta.ofertas_validas) > 1
        and not t.acepta_cualquier_valida
        for t in TAREAS
        if not t.respuesta.abstencion
    )
    assert m["M2"]["global"]["n"] - m["M2"]["global"]["k"] == 2 * (omitidas + fallos_seleccion)


def test_m3_acuerdo_perfecto_con_agente_determinista(corrida):
    _, m = corrida
    assert m["M3"]["aplica"] and m["M3"]["acuerdo_total"]["p"] == 1.0
    assert m["M3"]["m2_rango"] == 0


def test_informe_markdown_y_graficos(corrida, tmp_path):
    filas, m = corrida
    texto = metricas.a_markdown({**m, "meta": {**m["meta"], "commit": ["abc"]}})
    assert "## M1" in texto and "## M6" in texto
    assert "," in texto and not __import__("re").search(r"\d\.\d", texto)  # coma decimal
    rutas = metricas.graficos(m, tmp_path, filas)
    assert all(r.exists() and r.stat().st_size > 1000 for r in rutas)


def test_app_streamlit_modo_simulado():
    from streamlit.testing.v1 import AppTest

    from comercio_agentico.corpus_b import RAIZ

    at = AppTest.from_file(str(RAIZ / "src" / "comercio_agentico" / "app.py"), default_timeout=60)
    at.run()
    assert not at.exception
    at.radio[0].set_value("simulado").run()
    at.selectbox[0].set_value("B013").run()
    at.button[0].click().run()
    assert not at.exception
    assert at.success and "Recomendación" in at.success[0].value
    assert len(at.dataframe[0].value) >= 2
    assert any("SHA-256" in m.value for m in at.markdown)


def test_subconjunto_e3_congelado_y_proporcional():
    from collections import Counter

    from comercio_agentico.arnes.subconjunto import CUOTAS, RUTA_SUBCONJUNTO_E3, elegir

    congelado = cargar_tareas(RUTA_SUBCONJUNTO_E3)
    assert [t.id for t in congelado] == [t.id for t in elegir(TAREAS)]  # reproducible
    assert Counter(t.categoria for t in congelado) == Counter(CUOTAS)


def test_esquema_del_extractor_exige_todos_los_campos():
    from comercio_agentico.esquema import ListaOfertas, OfertaExtraida

    esquema = ListaOfertas.model_json_schema()["$defs"]["OfertaExtraida"]
    assert {"gtin", "mpn", "marca", "costo_envio"} <= set(esquema["required"])
    OfertaExtraida(titulo="x", precio=1)  # en el código, los valores por defecto siguen valiendo


def test_m1_oferta_de_listado_solo_compara_precio():
    v = next(o for o in VERDAD["ofertas"] if o["proveedor"] == "P2")
    base = {
        "precio": v["oferta"]["precio"],
        "producto_catalogo": v["producto_id"],
        "procedencia": {
            "fuente": "P2",
            "tipo_fuente": "web_schema",
            "consulta": "http://127.0.0.1:8800/p2_web_schema/index.html",
        },
    }
    callada = {**base, "costo_envio": None, "disponibilidad": "desconocida"}
    inventa = {**base, "costo_envio": None, "disponibilidad": "en_stock"}
    for oferta, esperado in ((callada, (1, 1)), (inventa, (1, 2))):
        fila = {"tarea": "X", "ofertas_todas": [oferta]}
        d = metricas.m1_extraccion([fila], VERDAD, {})["por_fuente"]["web_schema"]
        assert d["de_listado"] == 1
        assert (d["global"]["k"], d["global"]["n"]) == esperado


def test_corrida_comprimida_se_lee_igual(tmp_path):
    from comercio_agentico.arnes.correr import comprimir

    salida = tmp_path / "2026-01-01_x.jsonl"
    _correr(salida, TAREAS[:3])
    gz = comprimir(salida)
    assert gz.name == "2026-01-01_x.jsonl.gz" and comprimir(salida).read_bytes() == gz.read_bytes()
    assert metricas.cargar_corrida(gz) == metricas.cargar_corrida(salida)
    assert metricas.nombre_corrida(gz) == "2026-01-01_x"


# --------------------------------------------------------------------------------------------------
# E3: regla de parada D77 y frontera


def _paso(modelo, m2, rango, abst=0.5, costo=0.01):
    from comercio_agentico.arnes.e3 import Paso

    return Paso(modelo, f"e3_{modelo}", m2, rango, m2 - 0.1, m2 + 0.1, 90, abst, 0.8, costo, 150.0)


def test_regla_d77_sube_solo_si_supera_el_ruido():
    from comercio_agentico.arnes.e3 import regla_parada

    flash, haiku = _paso("deepseek-flash", 0.80, 0.05), _paso("haiku", 0.84, 0.03)
    assert [v.sube for v in regla_parada([flash, haiku])] == [False]  # +4 pp < 5 pp de ruido
    haiku = _paso("haiku", 0.87, 0.03)
    assert [v.sube for v in regla_parada([flash, haiku])] == [True]  # +7 pp > 5 pp
    # La abstención correcta también justifica subir aunque M2 empate.
    haiku = _paso("haiku", 0.80, 0.03, abst=0.70)
    assert regla_parada([flash, haiku])[0].sube


def test_regla_d77_compara_con_el_mejor_ya_medido():
    from comercio_agentico.arnes.e3 import regla_parada

    pasos = [
        _paso("deepseek-flash", 0.80, 0.02),
        _paso("haiku", 0.70, 0.02),  # peor: el mejor sigue siendo Flash
        _paso("deepseek-pro", 0.81, 0.02),  # mejora a Haiku, no a Flash
    ]
    v = regla_parada(pasos)
    assert [x.frente_a for x in v] == ["deepseek-flash", "deepseek-flash"]
    assert [x.sube for x in v] == [False, False]


def test_frontera_de_pareto():
    from comercio_agentico.arnes.e3 import frontera_pareto

    pasos = [
        _paso("deepseek-flash", 0.80, 0.0, costo=0.015),
        _paso("haiku", 0.78, 0.0, costo=0.02),  # dominado por Flash
        _paso("sonnet", 0.90, 0.0, costo=0.25),
    ]
    assert frontera_pareto(pasos) == ["deepseek-flash", "sonnet"]


def test_una_corrida_que_cruza_la_medianoche_se_reanuda(tmp_path):
    import datetime as dt

    from comercio_agentico.arnes.correr import ruta_salida

    hoy = dt.date(2026, 11, 10)
    assert ruta_salida("e3_pro", tmp_path, hoy).name == "2026-11-10_e3_pro.jsonl"
    ayer = tmp_path / "2026-11-09_e3_pro.jsonl"
    ayer.write_text("{}\n")
    assert ruta_salida("e3_pro", tmp_path, hoy) == ayer  # sin terminar: se reanuda
    (tmp_path / "2026-11-09_e3_pro.jsonl.gz").write_bytes(b"")
    assert ruta_salida("e3_pro", tmp_path, hoy).name == "2026-11-10_e3_pro.jsonl"  # terminada
    assert ruta_salida("e3_pro_v1", tmp_path, hoy).name == "2026-11-10_e3_pro_v1.jsonl"
