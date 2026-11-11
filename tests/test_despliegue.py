from pathlib import Path

from comercio_agentico.agente.defensa import CLASIFICADORES
from comercio_agentico.emparejamiento import MODELO_EMBEDDINGS

DOCKERFILE = (Path(__file__).resolve().parents[1] / "Dockerfile").read_text(encoding="utf-8")


def test_la_imagen_descarga_los_modelos_que_usa_el_agente():
    """La imagen corre sin acceso al Hub (HF_HUB_OFFLINE): cada modelo debe venir horneado."""
    for modelo in [MODELO_EMBEDDINGS, *CLASIFICADORES]:
        assert f"'{modelo}'" in DOCKERFILE, modelo
    assert "HF_HUB_OFFLINE=1" in DOCKERFILE
