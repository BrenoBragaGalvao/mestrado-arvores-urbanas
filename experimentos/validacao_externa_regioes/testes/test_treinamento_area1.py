#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Teste sintético de seleção interna + treinamento dos oito modelos."""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from treinar_area1 import run


def test_treina_modelos_somente_com_dados_area1_sinteticos(tmp_path):
    xx, yy=np.meshgrid(np.arange(20)*100.,np.arange(20)*100.)
    n=xx.size
    label=np.where(np.arange(n)%2==0,"arvore","grama")
    r=np.random.default_rng(19)
    frame=pd.DataFrame({
        "id":[f"segmento-{j}" for j in range(n)], "classe":label,
        "x":xx.ravel(),"y":yy.ravel(),
        "mean_intensity":np.where(label=="arvore",.6,.3)+r.normal(0,.01,n),
        "mean_edges":r.uniform(.01,.13,n),
        "mean_ndvi":np.where(label=="arvore",.7,.15)+r.normal(0,.01,n)
    })
    csv=tmp_path/"area1_sintetica.csv"
    frame.to_csv(csv,index=False)
    models=tmp_path/"models"
    run(csv,models,geo_path=None,allow_centroid=True)
    m=json.loads((models/"manifesto_modelos.json").read_text())
    assert m["amostras_rotuladas"]==n
    assert m["validacao"]["tipo_embargo"]=="centroides"
    assert len(m["modelos"])==8
    assert len(list(models.glob("*.joblib")))==8
    chosen=pd.read_csv(models/"modelos_escolhidos_area1.csv")
    assert len(chosen)==8
    assert set(chosen.receita)=={"forte","moderada"} or set(chosen.receita).issubset({"forte","moderada"})
    assert pd.read_csv(models/"validacoes_internas_area1.csv").shape[0]>=64
