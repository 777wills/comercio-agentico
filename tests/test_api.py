"""API de CotIA sin red, sin modelo y a US$0: agente simulado y SQLite en memoria."""

import asyncio
import json
import logging
import uuid

import pytest
from fastapi.testclient import TestClient
from langchain_core.messages import AIMessage, ToolMessage
from sqlalchemy import select

from comercio_agentico.agente.grafo import Resultado
from comercio_agentico.agente.interpretacion import Necesidad
from comercio_agentico.api.app import crear_app
from comercio_agentico.api.bd import ConsultaBD
from comercio_agentico.api.catalogo import clasificar
from comercio_agentico.api.ejecucion import Progreso, Servicio, ocultar
from comercio_agentico.esquema import Alerta, PropuestaCompra

CLAVE = "sk-or-v1-clave-secreta-de-prueba-0123456789"
VISITANTE = str(uuid.uuid4())
CABECERAS = {"X-OpenRouter-Key": CLAVE, "X-Visitante": VISITANTE}


class AgenteSimulado:
    """Recorre los cinco nodos del grafo y responde; guarda los argumentos que recibió."""

    def __init__(self, error: str | None = None, espera: asyncio.Event | None = None):
        self.llamadas: list[dict] = []
        self.error, self.espera = error, espera

    async def __call__(self, consulta, **kw):
        self.llamadas.append({"consulta": consulta, **kw})
        if self.espera is not None:
            await self.espera.wait()
        avanzar = kw["al_avanzar"]
        await avanzar("interpretar", {"necesidad": Necesidad(producto_mencionado="Monitor M8")})
        llamada = {"name": "leer_documento", "args": {"url": "http://p5/chat.txt"}, "id": "t1"}
        await avanzar("planificar", {"messages": [AIMessage("", tool_calls=[llamada])]})
        await avanzar(
            "herramientas",
            {
                "messages": [ToolMessage("{}", tool_call_id="t1")],
                "ofertas": [],
                "alertas": [Alerta(tipo="posible_inyeccion", mensaje="P5: 1 de 3 ventanas")],
            },
        )
        if self.error:
            raise RuntimeError(self.error)
        await avanzar("emparejar", {"ofertas_finales": []})
        propuesta = PropuestaCompra(
            consulta=consulta,
            perfil="electronica",
            abstencion=True,
            motivo_abstencion="Ninguna oferta cumple la necesidad.",
            costo_usd=0.0123,
        )
        await avanzar("proponer", {"propuesta": propuesta})
        return Resultado(propuesta, None, [], 1, [], 0.5, [])


@pytest.fixture
def lista_modelos(tmp_path):
    ruta = tmp_path / "modelos.json"
    ruta.write_text(
        json.dumps(
            {
                "modelos": [
                    {"nombre": "deepseek-flash", "aprobado": True, "costo_usd": 0.015},
                    {"nombre": "lfm3-free", "aprobado": False, "motivo": "respuesta incorrecta"},
                ]
            }
        )
    )
    return ruta


def cliente(lista_modelos, agente, **kw) -> tuple[TestClient, Servicio]:
    servicio = Servicio(
        None,  # type: ignore[arg-type]
        preguntar_fn=agente,
        recursos_fn=lambda corpus: (f"registro-{corpus}", f"emparejador-{corpus}"),
        variante_fn=lambda carga: f"registro-{carga.id}",
        clasificador_fn=lambda nombre: f"clasificador-{nombre}",
        **kw,
    )
    app = crear_app(
        url_bd="sqlite://", servicio=servicio, servir_corpus=False, ruta_modelos=lista_modelos
    )
    return TestClient(app), servicio


def eventos_sse(c: TestClient, id_consulta: str) -> list[dict]:
    salida = []
    with c.stream("GET", f"/api/consultas/{id_consulta}/eventos") as r:
        assert r.headers["content-type"].startswith("text/event-stream")
        for linea in r.iter_lines():
            if linea.startswith("data:"):
                salida.append(json.loads(linea[5:]))
    return salida


def test_consulta_de_punta_a_punta_con_progreso_sse(lista_modelos):
    agente = AgenteSimulado()
    c, _ = cliente(lista_modelos, agente)
    with c:
        r = c.post("/api/consultas", json={"consulta": "Monitor Samsung M8"}, headers=CABECERAS)
        assert r.status_code == 202
        id_consulta = r.json()["id"]
        etapas = [e["etapa"] for e in eventos_sse(c, id_consulta)]
        assert etapas == [
            "inicio",
            "interpretacion",
            "plan",
            "lecturas",
            "emparejamiento",
            "propuesta",
            "fin",
        ]
        detalle = c.get(f"/api/consultas/{id_consulta}").json()
        assert detalle["estado"] == "terminada" and detalle["propuesta"]["abstencion"]
        assert detalle["opciones"]["configuracion"] == "C2"  # D106
        # Terminada, el flujo se repite desde la base
        assert [e["etapa"] for e in eventos_sse(c, id_consulta)] == etapas
    kw = agente.llamadas[0]
    assert kw["clave_openrouter"] == CLAVE and kw["modelo_verificador"] == "haiku-or"  # D105
    assert kw["defensas"].configuracion == "C2" and kw["clasificador"].startswith("clasificador-")
    assert kw["registro"] == "registro-b"


def test_la_clave_no_se_guarda_ni_se_registra(lista_modelos, caplog):
    caplog.set_level(logging.DEBUG)
    c, servicio = cliente(lista_modelos, AgenteSimulado(error=f"401 clave inválida {CLAVE}"))
    with c:
        id_consulta = c.post(
            "/api/consultas", json={"consulta": "Monitor Samsung M8"}, headers=CABECERAS
        ).json()["id"]
        eventos = eventos_sse(c, id_consulta)
        respuestas = [
            c.get(f"/api/consultas/{id_consulta}").text,
            c.get("/api/consultas", headers={"X-Visitante": VISITANTE}).text,
        ]
        with servicio.sesiones() as s:
            filas = s.scalars(select(ConsultaBD)).all()
            volcado = json.dumps(
                [{k: str(v) for k, v in vars(f).items() if not k.startswith("_")} for f in filas]
            )
    assert eventos[-1]["estado"] == "error" and "[clave oculta]" in eventos[-1]["error"]
    for texto in [volcado, *respuestas, json.dumps(eventos), caplog.text]:
        assert CLAVE not in texto


def test_validaciones_de_la_peticion(lista_modelos):
    c, _ = cliente(lista_modelos, AgenteSimulado())
    with c:
        cuerpo = {"consulta": "Monitor Samsung M8"}
        sin_clave = c.post("/api/consultas", json=cuerpo, headers={"X-Visitante": VISITANTE})
        assert sin_clave.status_code == 401
        assert (
            c.post("/api/consultas", json=cuerpo, headers={"X-OpenRouter-Key": CLAVE}).status_code
            == 422
        )
        no_curado = c.post(
            "/api/consultas", json=cuerpo | {"modelo": "lfm3-free"}, headers=CABECERAS
        )
        assert no_curado.status_code == 422
        assert c.post("/api/consultas", json={}, headers=CABECERAS).status_code == 422
        lab_a = c.post("/api/consultas", json={"carga": "A01", "corpus": "a"}, headers=CABECERAS)
        assert lab_a.status_code == 422
        umbral = c.post(
            "/api/consultas", json=cuerpo | {"defensas": {"umbral": 2}}, headers=CABECERAS
        )
        assert umbral.status_code == 422
        assert c.get("/api/consultas/no-existe/eventos").status_code == 404


def test_laboratorio_usa_la_variante_atacada_y_evalua_el_predicado(lista_modelos):
    agente = AgenteSimulado()
    c, _ = cliente(lista_modelos, agente)
    with c:
        cuerpo = {"carga": "A01", "defensas": {"clasificador": False}}  # exploratorio no: C1
        id_consulta = c.post("/api/consultas", json=cuerpo, headers=CABECERAS).json()["id"]
        fin = eventos_sse(c, id_consulta)[-1]
        detalle = c.get(f"/api/consultas/{id_consulta}").json()
    assert agente.llamadas[0]["registro"] == "registro-A01"
    ejemplo = next(e for e in c.get("/api/ejemplos").json()["laboratorio"] if e["carga"] == "A01")
    assert agente.llamadas[0]["consulta"] == ejemplo["consulta"]
    assert fin["exito_ataque"] is False and detalle["detalle"]["exito_ataque"] is False
    assert detalle["opciones"]["configuracion"] == "C1"


def test_modo_exploratorio_y_clasificador_no_validado(lista_modelos):
    agente = AgenteSimulado()
    c, _ = cliente(lista_modelos, agente)
    with c:
        cuerpo = {"consulta": "Monitor", "defensas": {"separacion_planos": False}}
        id_consulta = c.post("/api/consultas", json=cuerpo, headers=CABECERAS).json()["id"]
        eventos_sse(c, id_consulta)
        assert c.get(f"/api/consultas/{id_consulta}").json()["opciones"]["configuracion"] == (
            "exploratorio"
        )
        otro = c.post(
            "/api/consultas", json=cuerpo | {"clasificador": "otro/modelo"}, headers=CABECERAS
        )
        assert otro.status_code == 422


def test_historial_y_gasto_de_la_visita(lista_modelos):
    c, _ = cliente(lista_modelos, AgenteSimulado())
    with c:
        for _ in range(2):
            i = c.post("/api/consultas", json={"consulta": "Monitor"}, headers=CABECERAS).json()
            eventos_sse(c, i["id"])
        h = c.get("/api/consultas", headers={"X-Visitante": VISITANTE}).json()
        otro = c.get("/api/consultas", headers={"X-Visitante": str(uuid.uuid4())}).json()
    assert h["total_consultas"] == 2 and h["gasto_usd"] == pytest.approx(0.0246)
    assert otro["total_consultas"] == 0


def test_cola_llena_responde_429(lista_modelos):
    async def nunca(*_, **__):
        await asyncio.Event().wait()

    c, servicio = cliente(lista_modelos, nunca, max_simultaneas=1, max_en_cola=0)
    with c:
        assert (
            c.post("/api/consultas", json={"consulta": "uno"}, headers=CABECERAS).status_code == 202
        )
        r = c.post("/api/consultas", json={"consulta": "dos"}, headers=CABECERAS)
        assert r.status_code == 429
        for t in list(servicio.tareas):
            t.get_loop().call_soon_threadsafe(t.cancel)


def test_catalogos_resultados_y_salud(lista_modelos):
    c, _ = cliente(lista_modelos, AgenteSimulado())
    with c:
        m = c.get("/api/modelos").json()
        assert [x["nombre"] for x in m["modelos"]] == ["deepseek-flash"]
        assert m["por_defecto"] == "deepseek-flash" and m["defensas_por_defecto"] == "C2"
        ej = c.get("/api/ejemplos").json()
        assert len(ej["laboratorio"]) == 20 and ej["b"] and ej["a"]
        res = c.get("/api/resultados").json()
        assert set(res) == {"e1", "e2", "e3"} and res["e2"]["datos"] is not None
        figura = res["e2"]["figuras"][0]
        assert c.get(figura).headers["content-type"] == "image/png"
        assert c.get("/api/resultados/figuras/e2/..%2F..%2Fe2.json").status_code == 404
        assert c.get("/api/resultados/figuras/x/a.png").status_code == 404
        salud = c.get("/api/salud").json()
        assert salud["bd"] is True and salud["modelos"] == 1


def test_progreso_emite_latidos_mientras_espera():
    async def correr():
        p = Progreso()
        flujo = p.seguir(latido_s=0.01)
        assert await anext(flujo) is None  # sin eventos todavía: latido
        await p.emitir({"etapa": "inicio"})
        await p.cerrar()
        return [e async for e in flujo]

    assert asyncio.run(correr()) == [{"etapa": "inicio"}]


def test_criterio_de_la_lista_curada():
    e3 = {"haiku": {"m2_media": 0.9, "m2_bajo": 0.82, "m2_alto": 0.95}}
    fallo = {"acierto": False, "motivo": "respuesta incorrecta"}
    assert clasificar({"nombre": "haiku-or"} | fallo, e3)["aprobado"]  # M2 de E3
    assert not clasificar({"nombre": "dots-free"} | fallo, e3)["aprobado"]  # sin evidencia
    assert clasificar({"nombre": "x", "acierto": True, "motivo": None}, e3)["aprobado"]
    caido = {"nombre": "haiku-or", "motivo": "no terminó en 10 minutos"}
    assert not clasificar(caido, e3)["aprobado"]  # no funciona aunque tenga E3


def test_ocultar_la_clave():
    assert ocultar(f"error {CLAVE} x", CLAVE) == "error [clave oculta] x"
    assert ocultar("sin clave", None) == "sin clave"
