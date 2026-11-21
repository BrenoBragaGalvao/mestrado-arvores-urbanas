#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Testes de orquestração da Area1 com dados de controle, sem alegar F1 real."""
import hashlib
import json
import sys
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import pytest
import rasterio
from rasterio.transform import from_origin
from shapely.geometry import Point,box

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import executar_treinamento_real_area1 as api


def make_originals(path:Path):
    path.mkdir()
    profile={
        "driver":"GTiff", "width":40, "height":40, "count":3,
        "dtype":"uint8", "crs":"EPSG:31982",
        "transform":from_origin(1000,2000,.5,.5)
    }
    with rasterio.open(path/"AOI_RGB_NEW.tif","w",**profile) as f:
        f.write(np.ones((3,40,40),dtype="uint8"))
    profile["count"]=4
    with rasterio.open(path/"AOI_NEW_MULTI.tif","w",**profile) as f:
        f.write(np.ones((4,40,40),dtype="uint8"))
    gpd.GeoDataFrame(geometry=[box(990,1970,1050,2020)],
                     crs="EPSG:31982").to_file(path/"AOI_new.shp")
    for name,num in [("Arvores.gpkg",257),("Grama.gpkg",253)]:
        gpd.GeoDataFrame(geometry=[Point(1010,1990)]*num,
                        crs="EPSG:31982").to_file(path/name,driver="GPKG")


def test_auditoria_confere_510_referencias_reais_sinteticas(tmp_path):
    area=tmp_path/"area1"
    make_originals(area)
    result=api.audit_source(area)
    assert result["total_pontos_referencia"]==510
    assert result["quantidades_referencia"]=={"arvore":257,"grama":253}
    assert result["raster"]["rgb_bandas"]==3
    assert result["raster"]["multiespectral_bandas"]==4


def test_treinamento_bloqueia_pasta_de_entrada_ausente(tmp_path):
    with pytest.raises(FileNotFoundError):
        api.run_pipeline(tmp_path/"area1_inexistente",tmp_path/"saida")


def test_conferencia_segmentos_bloqueia_metricas_falsas(tmp_path,monkeypatch):
    area=tmp_path/"area1"
    make_originals(area)

    def reconstruct_fake(a,o,expect,resume):
        o.mkdir(parents=True)
        frame=pd.DataFrame({"id":range(503),"classe":["arvore"]*251+["grama"]*252,
                            "x":range(503),"y":range(503),
                            "mean_intensity":[0.3]*503,
                            "mean_edges":[0.1]*503,
                            "mean_ndvi":[0.2]*503})
        frame.to_csv(o/"rotulos_sem_duplicacao.csv",index=False)
        (o/"E3c_geometrias_rotuladas_812.gpkg").write_text("placeholder")
    monkeypatch.setattr(api,"reconstruct",reconstruct_fake)
    with pytest.raises(ValueError,match="505 segmentos"):
        api.run_pipeline(area,tmp_path/"saidas")
    assert not (tmp_path/"saidas/resumo_execucao_treinamento.json").exists()


def test_pipeline_reusa_modelos_apenas_se_sha_identico(tmp_path,monkeypatch):
    area=tmp_path/"area1"
    make_originals(area)
    out=tmp_path/"saida"
    frame=pd.DataFrame({"id":range(505),"classe":["arvore"]*257+["grama"]*248,
                        "x":np.arange(505)*3., "y":np.arange(505)*3.,
                        "mean_intensity":np.linspace(.1,.8,505),
                        "mean_edges":np.linspace(.01,.1,505),
                        "mean_ndvi":np.linspace(.2,.6,505)})
    monkeypatch.setattr(api,"read_training_data",lambda path:frame.copy())
    monkeypatch.setattr(api,"read_geometry",lambda path,frame:np.empty(len(frame),dtype=object))
    events={"reconstruct":0,"train":0,"evaluate":0}
    def reconstruct_fake(a,o,expect,resume):
        events["reconstruct"]+=1
        o.mkdir(parents=True)
        (o/"rotulos_sem_duplicacao.csv").write_text("id,classe,x,y\n")
        (o/"E3c_geometrias_rotuladas_812.gpkg").write_text("placeholder")
    def train_fake(csv,models,geo_path,allow_centroid):
        events["train"]+=1
        assert allow_centroid is False
        models.mkdir(parents=True,exist_ok=True)
        for filename in api.CLASSIFIER_FILES:
            (models/filename).write_bytes(b"model_only_for_synthetic_testing")
        (models/"manifesto_modelos.json").write_text(json.dumps({
            "base_area1_sha256":api.sha256_file(csv),
            "modelos":{f"m{i}":{"arquivo":filename,"receita":"moderada",
                                "f1_validacao_interna":.5}
                       for i,filename in enumerate(api.CLASSIFIER_FILES)},
            "validacao":{"tipo_embargo":"geometrias"}
        }),encoding="utf-8")
    def evaluate_fake(csv,output,geometry,centroid_embargo,outer,inner):
        events["evaluate"]+=1
        assert outer==5 and inner==3 and centroid_embargo is False
        output.mkdir(parents=True,exist_ok=True)
        (output/"metodologia_area1_aninhada.json").write_text(json.dumps({
            "base_sha256":api.sha256_file(csv),
            "embargo":"geometrico","particoes_externas_por_escala":5
        }),encoding="utf-8")
        pd.DataFrame([{"bloco_m":s,"modelo":f"m{i}","folds":5}
                      for s in (250,500) for i in range(8)]).to_csv(
                          output/"area1_resumo_oito_modelos.csv",index=False)
    monkeypatch.setattr(api,"reconstruct",reconstruct_fake)
    monkeypatch.setattr(api,"train",train_fake)
    monkeypatch.setattr(api,"evaluate",evaluate_fake)
    report=api.run_pipeline(area,out)
    assert report["estado"]=="AREA1_TREINADA_E_AUDITADA"
    assert report["area1_segmentos_rotulados_unicos"]==505
    assert report["nova_validacao_aninhada_concluida"]
    assert events=={"reconstruct":1,"train":1,"evaluate":1}
    report2=api.run_pipeline(area,out)
    assert report2["estado"]=="AREA1_TREINADA_E_AUDITADA"
    assert events=={"reconstruct":1,"train":1,"evaluate":1}
