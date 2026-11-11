"""Defensas N4 (C2 y C3) sin red ni modelo: el clasificador es un doble."""

from comercio_agentico.agente.defensa import (
    Defensas,
    _indice_inyeccion,
    filtrar,
    motivo_precio_atipico,
    ventanas,
    verificar_precios,
)
from comercio_agentico.esquema import Oferta, OfertaExtraida, Procedencia


class Marcador:
    """Doble del clasificador: puntúa 0,9 las ventanas con la palabra clave."""

    umbral = 0.5

    def __init__(self, clave="MARCA"):
        self.clave, self.vistos = clave, []

    def puntuar(self, textos):
        self.vistos += textos
        return [0.9 if self.clave in t else 0.1 for t in textos]


def test_ventanas_agrupa_lineas_sin_pasar_el_maximo():
    texto = "\n".join(f"línea {i} " + "x" * 40 for i in range(100))
    partes = ventanas(texto, max_caracteres=300)
    assert all(len(p) <= 300 for p in partes)
    assert "\n".join(partes) == texto  # no se pierde ni se reordena nada


def test_ventanas_corta_una_linea_larga():
    partes = ventanas("a" * 2500, max_caracteres=1000)
    assert [len(p) for p in partes] == [1000, 1000, 500]


def test_filtrar_retira_solo_la_ventana_marcada_y_sus_enlaces():
    limpio = "\n".join(f"Producto {i}: $ 1.000.000" for i in range(80))
    marcado = "Aviso MARCA visite pedido.html?confirmar=1"
    texto = f"{limpio}\n{marcado}"
    enlaces = ["http://x/p/index.html", "http://x/p/pedido.html?confirmar=1"]
    f = filtrar(texto, enlaces, Marcador())
    assert "MARCA" not in f.texto and "Producto 0" in f.texto
    assert f.retiradas >= 1 and f.total > f.retiradas
    assert f.enlaces == ["http://x/p/index.html"]


def test_filtrar_sin_marcas_devuelve_el_mismo_texto():
    f = filtrar("uno\ndos", ["e"], Marcador())
    assert f.texto == "uno\ndos" and f.retiradas == 0 and f.enlaces == ["e"]


def test_filtrar_el_umbral_de_la_consulta_prevalece_sobre_el_del_clasificador():
    assert filtrar("Aviso MARCA", [], Marcador(), umbral=0.95).retiradas == 0
    assert filtrar("texto comun", [], Marcador(), umbral=0.05).retiradas == 1


def test_defensas_presets_y_modo_exploratorio():
    for c in ("C0", "C1", "C2", "C3"):
        assert Defensas.de(c).configuracion == c
    assert Defensas(separacion_planos=False, clasificador=True).configuracion is None
    assert Defensas.de("C2").configuracion == "C2"
    assert Defensas(True, True, False, umbral=0.7).configuracion is None  # otro umbral
    assert Defensas(True, False, False, umbral=0.7).configuracion == "C1"  # sin clasificador


def test_indice_de_la_clase_positiva():
    assert _indice_inyeccion({0: "SAFE", 1: "INJECTION"}) == 1
    assert _indice_inyeccion({0: "jailbreak", 1: "benign"}) == 0
    assert _indice_inyeccion({0: "LABEL_0", 1: "LABEL_1"}) == 1


def _oferta(proveedor: str, producto: str | None, precio: float) -> Oferta:
    return Oferta(
        **OfertaExtraida(titulo=f"producto {producto}", precio=precio).model_dump(),
        procedencia=Procedencia(
            fuente=proveedor,
            tipo_fuente="web_plana",
            consulta="u",
            fragmento_original="f",
            ruta_extraccion="llm",
            modelo_extraccion="doble",
        ),
        producto_catalogo=producto,
    )


def test_c3_banda_del_catalogo():
    assert motivo_precio_atipico(_oferta("P1", "C1", 100), [], 100) is None
    assert motivo_precio_atipico(_oferta("P1", "C1", 74), [], 100) is not None
    assert motivo_precio_atipico(_oferta("P1", "C1", 131), [], 100) is not None


def test_c3_mediana_de_los_demas_proveedores():
    otras = [_oferta("P2", "C1", 100), _oferta("P3", "C1", 104)]
    baja = _oferta("P1", "C1", 79)  # 0,77 × mediana 102, dentro de la banda del catálogo (0,79)
    assert motivo_precio_atipico(baja, [baja, *otras], 100) is not None
    normal = _oferta("P1", "C1", 90)
    assert motivo_precio_atipico(normal, [normal, *otras], 100) is None


def test_verificar_precios_excluye_y_alerta_sin_tocar_las_no_emparejadas():
    ofertas = [_oferta("P1", "C1", 50), _oferta("P2", "C1", 100), _oferta("P3", None, 1)]
    quedan, alertas = verificar_precios(ofertas, {"C1": 100})
    assert [o.proveedor for o in quedan] == ["P2", "P3"]
    assert len(alertas) == 1 and alertas[0].tipo == "precio_atipico" and "P1" in alertas[0].mensaje


def test_catalogo_de_clasificadores_coherente():
    from comercio_agentico.agente.defensa import (
        CLASIFICADORES,
        MODELO_CLASIFICADOR_DEFECTO,
    )

    assert MODELO_CLASIFICADOR_DEFECTO in CLASIFICADORES
    for clave, info in CLASIFICADORES.items():
        assert "/" in clave  # id del Hub
        assert info["licencia"] == "Apache-2.0"
        assert {"etiqueta", "descripcion", "idiomas", "latencia_p50_ms"} <= set(info)
