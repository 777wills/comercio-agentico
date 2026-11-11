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


def test_clave_del_visitante_por_consulta(monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.setattr("comercio_agentico.modelos.load_dotenv", lambda: None)
    modelo = obtener_modelo("haiku-or", clave_openrouter="sk-or-visitante")
    assert modelo.openrouter_api_key.get_secret_value() == "sk-or-visitante"
    assert "sk-or-visitante" not in repr(modelo)
    assert "order" not in modelo.openrouter_provider  # sin proveedor fijado
    assert modelo.temperature is None  # Claude 5.5 rechaza la temperatura (D60)
    with pytest.raises(ValueError):
        obtener_modelo("haiku", clave_openrouter="sk-or-visitante")  # Anthropic directo
    with pytest.raises(KeyError):
        obtener_modelo("gpt")


def test_la_clave_del_visitante_no_llega_a_las_trazas(monkeypatch):
    """Lo que vería LangSmith (D117): serialización, parámetros y metadatos de la llamada."""
    from langchain_core.messages import HumanMessage
    from langchain_core.outputs import ChatResult
    from langchain_core.tracers.context import collect_runs

    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.setattr("comercio_agentico.modelos.load_dotenv", lambda: None)
    clave = "sk-or-v1-visitante-secreta-0123456789"
    modelo = obtener_modelo("deepseek-flash", clave_openrouter=clave)
    respuesta = ChatResult(generations=[ChatGeneration(message=AIMessage(content="ok"))])
    monkeypatch.setattr(type(modelo), "_generate", lambda *a, **k: respuesta)
    with collect_runs() as recolector:
        modelo.invoke([HumanMessage(content="Precio del Galaxy A57")])
    (traza,) = recolector.traced_runs
    volcado = traza.model_dump_json() + repr(traza.serialized) + repr(traza.extra)
    assert "Galaxy A57" in volcado  # la traza sí registra la consulta
    assert clave not in volcado


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
