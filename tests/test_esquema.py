import pytest
from pydantic import ValidationError

from comercio_agentico.esquema import (
    Alerta,
    ListaOfertas,
    Oferta,
    OfertaExtraida,
    Procedencia,
    PropuestaCompra,
    gtin_valido,
    suma_verificacion,
)

FRAGMENTO = "Televisor Samsung 55'' 4K UHD — $2.199.900 — EAN 4006381333931"


def procedencia(**cambios):
    datos = {
        "fuente": "proveedor-web-plana",
        "tipo_fuente": "web_plana",
        "consulta": "abrir_pagina(/tv-55)",
        "fragmento_original": FRAGMENTO,
        "ruta_extraccion": "llm",
        "modelo_extraccion": "deepseek-flash",
    }
    return Procedencia(**(datos | cambios))


def oferta(**cambios):
    datos = {"titulo": "Televisor Samsung 55 4K", "precio": 2_199_900, "procedencia": procedencia()}
    return Oferta(**(datos | cambios))


@pytest.mark.parametrize(
    ("codigo", "esperado"),
    [
        ("4006381333931", True),
        ("4006381333932", False),
        ("96385074", True),
        ("12345", False),
        ("abc", False),
    ],
)
def test_gtin_por_digito_de_control(codigo, esperado):
    assert gtin_valido(codigo) is esperado


def test_gtin_se_limpia_y_se_valida():
    assert OfertaExtraida(titulo="x", precio=1, gtin="400-6381 333931").gtin == "4006381333931"
    with pytest.raises(ValidationError):
        OfertaExtraida(titulo="x", precio=1, gtin="4006381333932")


def test_precio_debe_ser_positivo_y_moneda_iso():
    with pytest.raises(ValidationError):
        OfertaExtraida(titulo="x", precio=0)
    with pytest.raises(ValidationError):
        OfertaExtraida(titulo="x", precio=10, moneda="pesos")


def test_procedencia_sella_la_suma_de_verificacion():
    p = procedencia()
    assert p.suma_verificacion == suma_verificacion(FRAGMENTO)
    assert p.marca_tiempo.tzinfo is not None


def test_procedencia_rechaza_fragmento_alterado():
    with pytest.raises(ValidationError, match="suma de verificación"):
        procedencia(suma_verificacion=suma_verificacion("otro texto"))


def test_extraccion_con_llm_exige_modelo():
    with pytest.raises(ValidationError):
        procedencia(modelo_extraccion=None)
    assert procedencia(ruta_extraccion="determinista", modelo_extraccion=None)


def test_oferta_exige_procedencia_y_suma_envio():
    with pytest.raises(ValidationError):
        Oferta(titulo="x", precio=10)
    assert oferta(costo_envio=30_000).costo_total == 2_229_900


def test_esquema_de_extraccion_no_expone_procedencia():
    # El LLM nunca escribe la procedencia: no forma parte de su salida estructurada.
    esquema = ListaOfertas.model_json_schema()
    assert "procedencia" not in esquema["$defs"]["OfertaExtraida"]["properties"]
    assert "Procedencia" not in esquema["$defs"]


def test_propuesta_con_recomendacion():
    p = PropuestaCompra(consulta="tv 55", perfil="electronica", ofertas=[oferta()], recomendada=0)
    assert not p.abstencion


def test_propuesta_abstencion_coherente():
    p = PropuestaCompra(
        consulta="tv 55",
        perfil="electronica",
        abstencion=True,
        motivo_abstencion="Sin ofertas verificadas",
    )
    assert p.recomendada is None
    with pytest.raises(ValidationError):
        PropuestaCompra(consulta="tv", perfil="electronica", abstencion=True)
    with pytest.raises(ValidationError):
        PropuestaCompra(consulta="tv", perfil="electronica")


def test_propuesta_rechaza_indices_fuera_de_rango():
    with pytest.raises(ValidationError):
        PropuestaCompra(consulta="tv", perfil="electronica", ofertas=[oferta()], recomendada=1)
    with pytest.raises(ValidationError):
        PropuestaCompra(
            consulta="tv",
            perfil="electronica",
            ofertas=[oferta()],
            recomendada=0,
            alertas=[Alerta(tipo="precio_atipico", mensaje="?", oferta=3)],
        )
