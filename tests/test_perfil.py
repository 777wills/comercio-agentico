from pathlib import Path

import pytest
from pydantic import ValidationError

from comercio_agentico.esquema import (
    AtributoComparable,
    PerfilCategoria,
    RestriccionDura,
    cargar_perfil,
)

RUTA = Path(__file__).parents[1] / "perfiles" / "electronica.yaml"


@pytest.fixture(scope="module")
def perfil():
    return cargar_perfil(RUTA)


def test_perfil_carga_y_declara_emparejamiento(perfil):
    assert perfil.nombre == "electronica"
    assert perfil.identificador_emparejamiento[0] == "gtin"


@pytest.mark.parametrize(
    ("atributo", "valor", "unidad", "esperado"),
    [
        ("tamano_pantalla", 139.7, "cm", 55.0),
        ("pantalla", 55, '"', 55.0),
        ("almacenamiento", 1, "TB", 1024.0),
        ("ram", 16, "GB", 16.0),
        ("garantía", 2, "años", 24.0),
        ("peso", 1800, "g", 1.8),
    ],
)
def test_normaliza_unidades(perfil, atributo, valor, unidad, esperado):
    assert perfil.atributo(atributo).normalizar(valor, unidad) == pytest.approx(esperado, abs=0.01)


@pytest.mark.parametrize(
    ("texto", "esperado"), [("Ultra HD", "4K"), ("1080p", "FHD"), ("super amoled", "OLED")]
)
def test_normaliza_categorias(perfil, texto, esperado):
    nombre = "tipo_panel" if "amoled" in texto else "resolucion"
    assert perfil.atributo(nombre).normalizar(texto) == esperado


def test_unidad_o_valor_desconocido_falla(perfil):
    with pytest.raises(ValueError):
        perfil.atributo("peso").normalizar(3, "arrobas")
    with pytest.raises(ValueError):
        perfil.atributo("resolucion").normalizar("retina")
    with pytest.raises(KeyError):
        perfil.atributo("sabor")


def test_restricciones_duras_del_perfil(perfil):
    por_atributo = {r.atributo: r for r in perfil.restricciones_duras}
    assert por_atributo["moneda"].cumple("COP")
    assert not por_atributo["moneda"].cumple("USD")
    assert por_atributo["disponibilidad"].cumple("en_stock")
    assert not por_atributo["disponibilidad"].cumple("agotado")
    assert not por_atributo["disponibilidad"].cumple(None)


def test_restriccion_numerica():
    assert RestriccionDura(atributo="precio", operador="<=", valor=2_500_000).cumple(2_199_900)
    assert not RestriccionDura(atributo="precio", operador=">=", valor=3_000_000).cumple(2_199_900)


def test_perfil_invalido_se_rechaza():
    with pytest.raises(ValidationError):
        AtributoComparable(nombre="peso", tipo="numero")  # sin unidad canónica
    with pytest.raises(ValidationError):
        PerfilCategoria(
            nombre="x",
            identificador_emparejamiento=["gtin"],
            atributos=[AtributoComparable(nombre="color", tipo="texto")],
            restricciones_duras=[RestriccionDura(atributo="inexistente", operador="==", valor=1)],
        )
