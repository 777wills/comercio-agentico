"""Consulta en vivo y lista blanca por visitante (D112, D113). Sin red y sin costo."""

import asyncio
import time

import httpx
import pytest
from fpdf import FPDF

from comercio_agentico.agente.comparacion_abierta import (
    Juicio,
    Juicios,
    comparar,
    pistas,
    proponer_abierto,
)
from comercio_agentico.agente.fuentes import TIENDAS_EN_VIVO, Fuente, RegistroFuentes
from comercio_agentico.agente.interpretacion import Necesidad
from comercio_agentico.agente.lectura import Lector
from comercio_agentico.agente.web_abierta import (
    MAX_ENLACES_ABIERTA,
    MAX_TEXTO_ABIERTA,
    Cortesia,
    UrlNoPermitida,
    recortar,
    sanear,
    validar_url_publica,
)
from comercio_agentico.api.fuentes_visitante import FuenteInvalida, texto_pdf
from comercio_agentico.esquema import ListaOfertas, OfertaExtraida
from test_agente import PERFIL, Doble, codificador_trigramas
from test_api import CABECERAS, VISITANTE, AgenteSimulado, cliente, lista_modelos  # noqa: F401

# --------------------------------------------------------------------------------------------------
# Salvaguardas de la web abierta


@pytest.mark.parametrize(
    "url",
    [
        "http://127.0.0.1:8000/api/salud",
        "http://localhost/",
        "http://10.0.0.5/precios",
        "http://192.168.1.1/",
        "http://169.254.169.254/latest/meta-data/",  # metadatos de la nube
        "http://[::1]/",
        "file:///etc/passwd",
        "ftp://8.8.8.8/lista.pdf",
    ],
)
def test_ssrf_rechaza_direcciones_internas_y_esquemas_raros(url):
    with pytest.raises(UrlNoPermitida):
        validar_url_publica(url)


def test_ssrf_acepta_una_direccion_publica():
    assert validar_url_publica("https://8.8.8.8/p/1") == "https://8.8.8.8/p/1"


def _cortesia(robots: str, pausa_s: float = 0.0) -> Cortesia:
    def responder(peticion: httpx.Request) -> httpx.Response:
        assert peticion.headers["User-Agent"].startswith("ComercioAgenticoBot")
        return httpx.Response(200, text=robots)

    return Cortesia(httpx.AsyncClient(transport=httpx.MockTransport(responder)), pausa_s)


def test_robots_txt_se_respeta():
    c = _cortesia("User-agent: *\nDisallow: /search/\n")
    asyncio.run(c.permitir("https://8.8.8.8/p/123"))
    with pytest.raises(UrlNoPermitida, match=r"robots\.txt"):
        asyncio.run(c.permitir("https://8.8.8.8/search/portatil"))


def test_pausa_entre_peticiones_al_mismo_sitio():
    c = _cortesia("", pausa_s=0.2)

    async def dos():
        inicio = time.monotonic()
        await c.permitir("https://8.8.8.8/a")
        await c.permitir("https://8.8.8.8/b")
        return time.monotonic() - inicio

    assert asyncio.run(dos()) >= 0.19


def test_recorte_de_paginas_reales():
    largo = "texto " * ((MAX_TEXTO_ABIERTA + 500) // 6)
    texto, enlaces = recortar(largo, [f"/c/{i}" for i in range(200)])
    assert len(texto) < MAX_TEXTO_ABIERTA + 20 and texto.endswith("(recortado)")
    assert len(enlaces) == MAX_ENLACES_ABIERTA
    assert recortar("t", ["/a?orden=1", "/b"])[1] == ["/b"]  # los filtros con parámetros se van

    # El menú largo del inicio se descarta; los productos con precio quedan
    menu = "\n".join(f"[Categoría {i}](/c/{i})" for i in range(3000))
    productos = "Portátil ASUS Vivobook 15\n$2.499.900\nEnvío gratis"
    texto, enlaces = recortar(menu + "\n" + productos, ["/c/1", "/portatil-asus/p/123", "/x"])
    assert "$2.499.900" in texto and "Vivobook" in texto and "Categoría 5" not in texto
    assert enlaces[0] == "/portatil-asus/p/123"  # las fichas primero


def test_saneamiento_quita_el_ruido_codificado_y_conserva_la_oferta():
    svg = "data:image/svg+xml,%3Csvg%20width='34'%3E%3Cpath%20d='M32.49%200.03H1.50'/%3E%3C/svg%3E"
    token = "eyJhbGciOiJSUzI1NiJ9eyJmb3JtSWQiOiI2MjBmMzNiYzIxYzgwNTRkYTM0ODMzMDkiLCJzdWIi"
    crudo = (
        f"[![Cmr logo]({svg})](https://www.falabella.com.co/cmr)\n"
        "![Galaxy A57](https://cdn.tienda.com/a57.webp?scale.option=fill&w=500)\n"
        "[Samsung Galaxy A57 256 GB](https://www.falabella.com.co/falabella-co/product/"
        "73262421/Samsung-Galaxy-A57-256GB-8GB-RAM-Camara-posterior-50MP/73262421?sid=HO)\n"
        "$ 1.599.900 · Envío gratis\n"
        f"[WhatsApp](https://samsung-webform.sprinklr.com/?token={token})\n"
        f"código {token}"
    )
    limpio = sanear(crudo)
    assert "data:" not in limpio and "%3C" not in limpio and token not in limpio
    assert "?scale" not in limpio and "?sid" not in limpio and "?token" not in limpio
    assert "[Cmr logo](https://www.falabella.com.co/cmr)" in limpio  # la imagen deja su texto
    assert "Galaxy A57\n" in limpio and "$ 1.599.900 · Envío gratis" in limpio
    assert "Samsung-Galaxy-A57-256GB-8GB-RAM-Camara-posterior-50MP/73262421)" in limpio
    assert recortar(crudo, [], saneado=False)[0] == crudo


def test_saneamiento_no_toca_el_bloque_schema_org():
    bloque = '{"@type":"Offer","price":"1599900","gtin13":"8806095426280","url":"https://x.co/p/1"}'
    assert sanear(bloque) == bloque


def test_lector_lee_el_pdf_del_visitante_sin_red():
    pdf = Fuente(
        id="U1",
        nombre="Lista",
        tipo_fuente="pdf",
        herramienta="leer_documento",
        url="pdf://abc",
        origen="usuario",
    )

    async def leer():
        lector = Lector(RegistroFuentes(fuentes=[pdf]), documentos={"pdf://abc": "Monitor $1"})
        async with lector:
            return await lector.leer_documento("pdf://abc")

    assert asyncio.run(leer()).texto == "Monitor $1"


def test_tiendas_en_vivo_por_defecto():
    assert [f.nombre for f in TIENDAS_EN_VIVO] == [
        "Alkosto",
        "Ktronix",
        "Falabella",
        "Samsung Colombia",
        "Panamericana",
    ]
    assert all(f.abierta and f.prefijo.startswith("https://") for f in TIENDAS_EN_VIVO)
    registro = RegistroFuentes(fuentes=TIENDAS_EN_VIVO)
    assert registro.por_url("https://www.alkosto.com/portatiles/c/BI_104").id == "V1"
    assert registro.por_url("https://www.samsung.com/co/monitors/").id == "V4"
    assert registro.por_url("https://www.samsung.com/mx/") is None  # otro país, otro sitio


# --------------------------------------------------------------------------------------------------
# Comparación abierta


def _oferta(titulo: str, precio: float, fuente: Fuente = TIENDAS_EN_VIVO[0], **kw):
    from comercio_agentico.agente.extraccion import a_ofertas
    from comercio_agentico.agente.lectura import Documento

    extraida = OfertaExtraida(
        titulo=titulo,
        precio=precio,
        costo_envio=kw.pop("envio", 0),
        disponibilidad=kw.pop("disponibilidad", "en_stock"),
        plazo_entrega_dias=kw.pop("plazo", 3),
        **kw,
    )
    documento = Documento(fuente=fuente, consulta=fuente.url, texto="t")
    return a_ofertas(documento, ListaOfertas(ofertas=[extraida]), "doble")[0]


def test_pistas_agrupan_por_gtin_y_por_titulo_casi_igual():
    ofertas = [
        _oferta("PORTATIL ASUS VIVOBOOK 15 16GB 512GB", 2_500_000),
        _oferta("Portatil ASUS Vivobook 15 16GB 512GB", 2_400_000, TIENDAS_EN_VIVO[1]),
        _oferta("Celular Samsung A56", 1_500_000, gtin="8806095467139"),
        _oferta("Galaxy A56 5G 256", 1_450_000, TIENDAS_EN_VIVO[2], gtin="8806095467139"),
        _oferta("Audífonos Sony WH-1000XM6", 1_200_000),
    ]
    g = pistas(ofertas, codificador_trigramas)
    assert g[0] == g[1] and g[2] == g[3] and len({g[0], g[2], g[4]}) == 3


def test_comparar_usa_el_juicio_del_llm_y_las_reglas_deterministas():
    ofertas = [
        _oferta("Monitor LG 27 4K", 1_200_000),
        _oferta("Monitor LG 27 4K", 1_100_000, TIENDAS_EN_VIVO[1], plazo=12),
        _oferta("Soporte de pared para monitor", 90_000),
        _oferta("Monitor Samsung 27 4K", 4_000_000, TIENDAS_EN_VIVO[2]),
    ]
    juez = Doble(
        Juicios(
            juicios=[
                Juicio(oferta=0, grupo=1, cumple=True, motivo=None),
                Juicio(oferta=1, grupo=1, cumple=True, motivo=None),
                Juicio(oferta=2, grupo=2, cumple=False, motivo="es un accesorio"),
                # la oferta 3 no recibe juicio: se descarta, no se adivina
            ]
        )
    )
    n = Necesidad(tipo_producto="monitor", presupuesto_max=3_000_000, plazo_max_dias=5)
    salida = asyncio.run(comparar(ofertas, n, PERFIL, juez, codificador_trigramas))
    assert [o.descarte for o in salida] == [
        None,
        "supera el plazo",
        "es un accesorio",
        "sin juicio de pertinencia",
    ]
    assert salida[0].grupo == salida[1].grupo == 1
    # Los títulos llegan como datos, con la advertencia de ignorar instrucciones
    sistema = juez.vistos[0][0].content
    assert "datos de terceros" in sistema


def test_disponibilidad_desconocida_compite_con_aviso_y_agotado_no():
    from comercio_agentico.agente.comparacion_abierta import descarte_determinista

    n = Necesidad()
    desconocida = _oferta("Galaxy A57 256GB", 1_500_000, disponibilidad="desconocida")
    agotado = _oferta("Galaxy A57 256GB", 1_400_000, disponibilidad="agotado")
    assert descarte_determinista(desconocida, n, PERFIL) is None
    assert descarte_determinista(agotado, n, PERFIL) is not None
    p = proponer_abierto("a57", n, [desconocida], PERFIL, None, [], "doble", 0.01)
    assert any("disponibilidad" in a.mensaje for a in p.alertas)


def test_proponer_abierto_elige_el_menor_costo_total_y_se_abstiene_con_motivo():
    a = _oferta("Monitor LG 27 4K", 1_200_000, envio=0).model_copy(update={"grupo": 1})
    b = _oferta("Monitor LG 27 4K", 1_150_000, TIENDAS_EN_VIVO[1], envio=80_000)
    b = b.model_copy(update={"grupo": 1})
    p = proponer_abierto("monitor", Necesidad(), [a, b], PERFIL, None, [], "doble", 0.01)
    assert not p.abstencion and p.ofertas[p.recomendada].proveedor == "V1"
    assert "entre 2 ofertas del mismo producto" in p.justificacion

    malas = [a.model_copy(update={"descarte": "supera el presupuesto"})]
    p = proponer_abierto("monitor", Necesidad(), malas, PERFIL, None, [], "doble", 0.01)
    assert p.abstencion and "supera el presupuesto" in p.motivo_abstencion


# --------------------------------------------------------------------------------------------------
# Lista blanca por visitante (API)


def _pdf(texto: str) -> bytes:
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("helvetica", size=12)
    pdf.multi_cell(0, 10, texto)
    return bytes(pdf.output())


def test_texto_pdf_valida_tamano_formato_y_contenido():
    assert "Monitor" in texto_pdf(_pdf("Monitor LG 27 pulgadas 4K $1.200.000"))
    with pytest.raises(FuenteInvalida, match="no es un PDF"):
        texto_pdf(b"hola")
    with pytest.raises(FuenteInvalida, match="5 MB"):
        texto_pdf(b"%PDF" + b"0" * (5 * 1024 * 1024))
    with pytest.raises(FuenteInvalida, match="texto"):
        texto_pdf(_pdf(" "))


def test_lista_blanca_por_visitante_de_punta_a_punta(lista_modelos):  # noqa: F811
    agente = AgenteSimulado()
    c, servicio = cliente(lista_modelos, agente)
    servicio.fuentes.robots = lambda url: "bloqueada" not in url
    otro = {"X-Visitante": "00000000-0000-4000-8000-000000000000"}
    with c:
        grupos = {g["id"]: g for g in c.get("/api/fuentes", headers=CABECERAS).json()["grupos"]}
        assert list(grupos) == ["vivo", "a", "b"]
        assert [f["id"] for f in grupos["vivo"]["fuentes"]] == ["V1", "V2", "V3", "V4", "V5"]
        assert all(
            f["activa"] and not f["eliminable"] for g in grupos.values() for f in g["fuentes"]
        )

        # Desactivar una fuente por defecto solo afecta a este visitante
        r = c.patch("/api/fuentes/V3", json={"activa": False}, headers=CABECERAS)
        assert (
            next(f for f in r.json()["grupos"][0]["fuentes"] if f["id"] == "V3")["activa"] is False
        )
        assert all(
            f["activa"] for f in c.get("/api/fuentes", headers=otro).json()["grupos"][0]["fuentes"]
        )

        # URL propia: interna → rechazada; robots.txt la prohíbe → rechazada; pública → agregada
        assert (
            c.post(
                "/api/fuentes/url", json={"url": "http://127.0.0.1:8800/"}, headers=CABECERAS
            ).status_code
            == 422
        )
        r = c.post("/api/fuentes/url", json={"url": "https://8.8.8.8/bloqueada"}, headers=CABECERAS)
        assert r.status_code == 422 and "robots.txt" in r.json()["detail"]
        r = c.post("/api/fuentes/url", json={"url": "https://8.8.8.8/tienda"}, headers=CABECERAS)
        assert r.status_code == 201

        # PDF propio: se guarda su texto y su SHA-256; un archivo que no es PDF se rechaza
        archivo = {"archivo": ("lista.pdf", _pdf("Monitor LG 27 4K $1.200.000"), "application/pdf")}
        assert c.post("/api/fuentes/pdf", files=archivo, headers=CABECERAS).status_code == 201
        malo = {"archivo": ("x.pdf", b"no soy un pdf", "application/pdf")}
        assert c.post("/api/fuentes/pdf", files=malo, headers=CABECERAS).status_code == 422
        vivo = c.get("/api/fuentes", headers=CABECERAS).json()["grupos"][0]["fuentes"]
        propias = [f for f in vivo if f["eliminable"]]
        assert [f["tipo_fuente"] for f in propias] == ["web_plana", "pdf"]
        assert propias[1]["url"].startswith("PDF · SHA-256 ")

        registro, documentos = servicio.fuentes.registro(VISITANTE, "vivo")
        assert "V3" not in {f.id for f in registro.fuentes}
        assert len(documentos) == 1 and "Monitor" in next(iter(documentos.values()))

        # La consulta en vivo llega al agente con la comparación abierta y esas fuentes
        r = c.post(
            "/api/consultas", json={"consulta": "monitor 4K", "corpus": "vivo"}, headers=CABECERAS
        )
        assert r.status_code == 202
        for _ in range(100):
            if agente.llamadas:
                break
            time.sleep(0.02)
        kw = agente.llamadas[0]
        assert kw["abierta"] is True and kw["documentos"] == documentos
        assert {f.id for f in kw["registro"].fuentes} == {f.id for f in registro.fuentes}

        # Eliminar una propia; las por defecto no se eliminan; restablecer vuelve a todo
        assert c.delete(f"/api/fuentes/{propias[0]['id']}", headers=CABECERAS).status_code == 200
        assert c.delete("/api/fuentes/V1", headers=CABECERAS).status_code == 404
        r = c.post("/api/fuentes/restablecer", headers=CABECERAS).json()
        assert (
            all(f["activa"] for f in r["grupos"][0]["fuentes"])
            and len(r["grupos"][0]["fuentes"]) == 5
        )

        # Sin fuentes activas en el grupo no se crea la consulta
        for i in range(1, 6):
            c.patch(f"/api/fuentes/V{i}", json={"activa": False}, headers=CABECERAS)
        r = c.post(
            "/api/consultas", json={"consulta": "monitor 4K", "corpus": "vivo"}, headers=CABECERAS
        )
        assert r.status_code == 422
