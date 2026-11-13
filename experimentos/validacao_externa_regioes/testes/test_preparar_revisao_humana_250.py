"""Testes apenas SINTÉTICOS dos pacotes cegos para revisão independente."""
import json
from pathlib import Path
import sys
from zipfile import ZipFile

import geopandas as gpd
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from preparar_revisao_humana_250 import prepare_one, check_review


def make_zip(tmp_path, bad_id=False):
    source = tmp_path / "02_sagrada_familia_caxias_250_por_classe.zip"
    ids = list(range(1, 501))
    if bad_id:
        ids[-1] = 1
    frame = pd.DataFrame({
        "segmento_id": ids,
        "x": [500000.0 + i for i in range(500)],
        "y": [6770000.0 + i for i in range(500)],
        "classe": ["arvore"] * 250 + ["grama"] * 250,
        "classe_verificada": [""] * 500,
    })
    with ZipFile(source, "w") as z:
        z.writestr("pasta/Amostras_treino.csv", frame.to_csv(index=False))
        z.writestr("pasta/Manifesto_amostragem.json", json.dumps({"origem": "sintetica"}))
    return source


def test_prepara_pacote_cegamente_sem_reutilizar_rotulo_ia(tmp_path):
    source = make_zip(tmp_path)
    result = prepare_one(source, tmp_path / "outputs")
    assert result["confirmadas"] == 0
    dest = Path(result["pasta"])
    points = gpd.read_file(dest / "amostras_treino_REVISAO_CEGA.gpkg")
    assert len(points) == 500
    assert points.crs.to_epsg() == 31982
    assert "classe_sugerida_IA_NAO_VERIFICADA" not in points
    assert "classe" not in points
    assert points["classe_verificada"].fillna("").eq("").all()
    key = pd.read_csv(dest / "chave_sugestoes_IA_NAO_MOSTRAR_AO_REVISOR.csv")
    assert key["classe_sugerida_IA_NAO_VERIFICADA"].value_counts().to_dict() == {
        "arvore": 250, "grama": 250
    }
    points["classe_verificada"] = ["arvore"] * 200 + ["grama"] * 200 + ["outro"] * 100
    points["revisor"] = "Revisor humano ficticio (teste)"
    edited = tmp_path / "revisado.gpkg"
    points.to_file(edited, driver="GPKG")
    report = check_review(edited, dest / "chave_sugestoes_IA_NAO_MOSTRAR_AO_REVISOR.csv",
                          tmp_path / "revisao.json")
    assert report["status"] == "ANOTACOES_COMPLETAS_AGUARDA_AUDITORIA_DE_QUALIDADE"
    assert report["contagens"]["outro"] == 100
    assert not (dest / "f1_externo.csv").exists()


def test_recusa_segmentos_duplicados(tmp_path):
    source = make_zip(tmp_path, bad_id=True)
    with pytest.raises(ValueError, match="repetidos"):
        prepare_one(source, tmp_path / "outputs")


def test_nao_sobrescreve_revisao_gerada(tmp_path):
    source = make_zip(tmp_path)
    prepare_one(source, tmp_path / "outputs")
    with pytest.raises(FileExistsError, match="existente"):
        prepare_one(source, tmp_path / "outputs")
