#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Somente testes sintéticos da NOVA ablação; não publicar F1 destas fixtures."""
from pathlib import Path
import sys

import geopandas as gpd
import numpy as np
import pandas as pd
import pytest
from shapely.geometry import Point
from sklearn.metrics import f1_score

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from ablacao_hsv_canny_ndvi_quatro_regioes import (
    FEATURES, REGIONS, model, load_area1, load_external, run, summary,
)


@pytest.fixture
def synthetic(tmp_path):
    rng = np.random.default_rng(20261120)
    n = 505
    xx = np.tile(np.arange(25), 21)[:n] * 120.0 + 480000
    yy = np.repeat(np.arange(21), 25)[:n] * 120.0 + 6700000
    labels = np.array(["arvore"] * 257 + ["grama"] * 248)
    rng.shuffle(labels)
    area = pd.DataFrame({
        "id": np.arange(1,n+1).astype(str),
        "classe": labels,
        "x": xx,
        "y": yy,
        "mean_intensity": (labels == "arvore") * .55 + .16 + rng.normal(0,.10,n),
        "mean_edges": (labels == "arvore") * .10 + .10 + rng.normal(0,.04,n),
        "mean_ndvi": (labels == "arvore") * .45 + .15 + rng.normal(0,.08,n),
    })
    area_csv = tmp_path / "area1.csv"
    area.to_csv(area_csv, index=False)
    geometry = gpd.GeoDataFrame({
        "segmento_id": area.id,
        "geometry": [Point(x,y).buffer(1) for x,y in zip(xx,yy)],
    }, crs="EPSG:31982")
    gpkg = tmp_path / "area1.gpkg"
    geometry.to_file(gpkg, driver="GPKG")
    full_cols = FEATURES["HSV + Canny + NDVI"]
    full_model = model().fit(area[full_cols].to_numpy(),labels)
    external_paths = []
    frozen = []
    for region,(title,eligible) in REGIONS.items():
        m=200
        pseudolabel = np.array(["arvore"]*85+["grama"]*(eligible-85)+
                               ["incerto"]*(200-eligible))
        rng.shuffle(pseudolabel)
        random_labels = np.where(pseudolabel == "arvore", "arvore", "grama")
        z = pd.DataFrame({
            "regiao":region,
            "amostra_id":[f"V{i+1:04d}" for i in range(m)],
            "segmento_id":[f"{region}_{i+1}" for i in range(m)],
            "bloco_500m":[f"{i%70}_{i//70}" for i in range(m)],
            "B":pseudolabel,
            "mean_intensity": (random_labels == "arvore")*.50+.18+rng.normal(0,.14,m),
            "mean_edges": (random_labels == "arvore")*.12+.1+rng.normal(0,.055,m),
            "mean_ndvi": (random_labels == "arvore")*.38+.2+rng.normal(0,.09,m),
        })
        z["predicao_modelo"] = full_model.predict(z[full_cols].to_numpy())
        p=tmp_path / f"{region}.csv"
        z.to_csv(p,index=False)
        external_paths.append((region,p))
        frozen.append(z[["regiao","amostra_id","segmento_id","bloco_500m","B",
                         "predicao_modelo"]])
    frozen_csv=tmp_path/"600_pontos_congelados.csv"
    pd.concat(frozen,ignore_index=True).to_csv(frozen_csv,index=False)
    return area_csv,gpkg,external_paths,frozen_csv


def test_new_paired_ablation_produces_exactly_240_f1_synthetic(tmp_path,synthetic):
    area,geo,external,frozen=synthetic
    tab=run(area,geo,external,frozen,tmp_path/"results")
    assert len(tab)==8
    assert tab.avaliacoes.eq(30).all()
    assert tab.media.between(0,1).all()
    evaluations=pd.read_csv(tmp_path/"results/ablacao_f1_pareado_240_avaliacoes.csv")
    assert len(evaluations)==240
    assert len(set(evaluations.configuracao))==2
    assert evaluations.groupby(["regiao","configuracao"]).size().eq(30).all()
    assert (tmp_path/"results/tabela_readme_ablacao_hsv_canny_ndvi.csv").is_file()


def test_frozen_predicoes_must_match(tmp_path,synthetic):
    area,geo,external,frozen=synthetic
    f=pd.read_csv(frozen)
    f.loc[0,"predicao_modelo"]="arvore" if f.loc[0,"predicao_modelo"]=="grama" else "grama"
    f.to_csv(frozen,index=False)
    with pytest.raises(ValueError,match="divergiu"):
        run(area,geo,external,frozen,tmp_path/"out")


def test_pseudo_label_counts_must_remain_frozen(synthetic):
    area,geo,external,frozen=synthetic
    p=external[0][1]
    f=pd.read_csv(p)
    f.loc[f.B=="incerto","B"]="grama"
    f.to_csv(p,index=False)
    with pytest.raises(ValueError,match="pseudo-rótulos válidos mudou"):
        load_external(external,frozen)


def test_area1_original_required(synthetic):
    area,geo,external,frozen=synthetic
    f=pd.read_csv(area).iloc[:-1]
    f.to_csv(area,index=False)
    with pytest.raises(ValueError,match="505 segmentos"):
        load_area1(area,geo)


def test_invalid_metric_table_rejected():
    bad=pd.DataFrame([{"configuracao":"HSV + Canny","regiao":"Area1",
                       "f1_macro":.8,"divisao":1}])
    with pytest.raises(AssertionError,match="duas configurações"):
        summary(bad)
