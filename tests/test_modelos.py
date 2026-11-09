import pytest
from langchain_core.messages import AIMessage
from langchain_core.outputs import ChatGeneration, LLMResult

from comercio_agentico.modelos import (
    MODELOS,
    CostoExcedido,
    RegistroCosto,
    costo_estimado,
    nombre_por_id,
    obtener_modelo,
)


def resultado(meta, entrada=1000, salida=500):
    mensaje = AIMessage(
        content="ok",
        response_metadata=meta,
        usage_metadata={
            "input_tokens": entrada,
            "output_tokens": salida,
            "total_tokens": entrada + salida,
        },
    )
    return LLMResult(generations=[[ChatGeneration(message=mensaje)]])


def test_seis_modelos_y_proveedor_fijado_en_openrouter():
    assert len(MODELOS) == 6
    for cfg in MODELOS.values():
        assert (cfg.proveedor is not None) == (cfg.plataforma == "openrouter")


def test_fabrica_construye_sin_red(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "clave-ficticia")
    monkeypatch.setenv("OPENROUTER_API_KEY", "clave-ficticia")
    assert type(obtener_modelo("haiku")).__name__ == "ChatAnthropic"
    modelo = obtener_modelo("kimi")
    assert type(modelo).__name__ == "ChatOpenRouter"
    assert modelo.openrouter_provider["allow_fallbacks"] is False
    with pytest.raises(KeyError):
        obtener_modelo("gpt")


def test_nombre_por_id_tolera_version():
    assert nombre_por_id("deepseek/deepseek-v4.1-flash-20260910") == "deepseek-flash"
    assert nombre_por_id("claude-opus-5-5") == "opus"
    assert nombre_por_id("otro") is None


def test_registro_usa_costo_de_la_api_o_la_tabla():
    registro = RegistroCosto(tope_usd=1.0)
    registro.on_llm_end(resultado({"model_name": "moonshotai/kimi-k3.1-pro", "cost": 0.0123}))
    registro.on_llm_end(resultado({"model_name": "claude-haiku-5-5"}))
    api, tabla = registro.llamadas
    assert (api.costo_fuente, api.costo_usd, api.proveedor) == ("api", 0.0123, "deepinfra/bf16")
    assert tabla.costo_fuente == "tabla"
    assert tabla.costo_usd == pytest.approx(costo_estimado("haiku", 1000, 500))
    assert registro.tokens_totales == (2000, 1000)


def test_registro_corta_al_superar_el_tope():
    registro = RegistroCosto(tope_usd=0.01)
    with pytest.raises(CostoExcedido):
        registro.on_llm_end(resultado({"model_name": "opus", "cost": 0.02}))
