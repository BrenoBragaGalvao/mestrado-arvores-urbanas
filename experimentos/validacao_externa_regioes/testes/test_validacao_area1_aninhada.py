#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Teste de separação estrita entre validação interna e teste externo."""
import sys
from pathlib import Path
import numpy as np
import pandas as pd
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from validar_area1_aninhada import evaluate


def test_valida_spatial_nested_sem_uso_teste_para_hiperparametros(tmp_path):
    xx,yy=np.meshgrid(np.arange(20)*100.,np.arange(20)*100.)
    n=len(xx.ravel())
    labels=np.where(np.arange(n)%2==0,"arvore","grama")
    data=pd.DataFrame({
        "id":np.arange(n),"classe":labels,"x":xx.ravel(),"y":yy.ravel(),
        "mean_intensity":np.where(labels=="arvore",.8,.1),
        "mean_edges":np.linspace(.02,.10,n),"mean_ndvi":np.linspace(.1,.9,n)
    })
    csv=tmp_path/"data.csv"
    data.to_csv(csv,index=False)
    scores=evaluate(csv,tmp_path/"results",centroid_embargo=True,outer=2,inner=2,
                    models=["Dummy"],scales=(250,500))
    assert len(scores)==2
    assert scores.folds.eq(2).all()
    test_data=pd.read_csv(tmp_path/"results/area1_aninhada_divisoes.csv")
    inner_data=pd.read_csv(tmp_path/"results/area1_validacao_interna.csv")
    assert len(test_data)==4
    assert len(inner_data)==16
    assert test_data.f1_teste_espacial.between(0,1).all()
    assert test_data.f1_treino.between(0,1).all()
    assert np.allclose(test_data.gap_f1_treino_menos_teste,
                       test_data.f1_treino-test_data.f1_teste_espacial)
    assert inner_data.f1_validacao_interna.between(0,1).all()
    assert (tmp_path/"results/metodologia_area1_aninhada.json").exists()


def test_recusa_embargo_negativo(tmp_path):
    import pytest
    with pytest.raises(ValueError, match="negativo"):
        evaluate(tmp_path/"inexistente.csv", tmp_path/"out",
                 centroid_embargo=True, embargo_m=-1)
