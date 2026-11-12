#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Teste de ponta a ponta com pontos/rasters artificiais, sem dados científicos."""
import json
import sys
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
from rasterio.transform import from_origin
from shapely.geometry import Point

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pytest
from avaliar_regiao import run


def test_avaliacao_independente_de_pontos_sinteticos(tmp_path):
    region="regiao_sintetica"
    input_dir=tmp_path/"input"
    input_dir.mkdir()
    raster_ids=np.zeros((32,32),dtype="uint32")
    predict=np.zeros((32,32),dtype="uint8")
    trees=[]
    grass=[]
    for i in range(6):
        col=3+2*i
        raster_ids[4,col]=i+1
        raster_ids[7,col]=i+7
        predict[4,col]=1
        predict[7,col]=2
        trees.append(Point(col+.5,32-4-.5))
        grass.append(Point(col+.5,32-7-.5))
    tr=from_origin(0,32,1,1)
    with rasterio.open(input_dir/"segmento_id.tif","w",driver="GTiff",height=32,width=32,
                       count=1,dtype="uint32",crs="EPSG:3857",transform=tr,nodata=0) as dst:
        dst.write(raster_ids,1)
    pred_map={}
    for i in range(8):
        filename=input_dir/f"classificacao_modelo{i}.tif"
        with rasterio.open(filename,"w",driver="GTiff",height=32,width=32,
                           count=1,dtype="uint8",crs="EPSG:3857",transform=tr,nodata=0) as dst:
            dst.write(predict,1)
        pred_map[f"modelo_{i}"]=str(filename)
    gpd.GeoDataFrame({"tipo":["arvore"]*6},geometry=trees,crs="EPSG:3857").to_file(
        tmp_path/"arvores.gpkg",driver="GPKG")
    gpd.GeoDataFrame({"tipo":["grama"]*6},geometry=grass,crs="EPSG:3857").to_file(
        tmp_path/"grama.gpkg",driver="GPKG")
    (input_dir/"manifesto_execucao.json").write_text(
        json.dumps({"estado":"concluido","regiao":region,"mapas":pred_map}),encoding="utf-8")
    output=tmp_path/"scores"
    table=run(region,input_dir,tmp_path/"arvores.gpkg",tmp_path/"grama.gpkg",output)
    assert table.shape[0]==8
    assert np.allclose(table.f1_macro.to_numpy(),1.)
    assert np.allclose(table.acuracia_balanceada.to_numpy(),1.)
    assert (output/"matrizes_confusao.csv").exists()
    assert (output/"auditoria_referencias.csv").exists()
    assert pd.read_csv(output/"comparacao_por_segmento.csv").shape[0]==12

def test_sagrada_nao_permite_metricas_sem_excluir_area1(tmp_path):
    with pytest.raises(ValueError, match="area1-aoi"):
        run("sagrada_familia_caxias",tmp_path/"pred",
            tmp_path/"arvores.gpkg",tmp_path/"grama.gpkg",
            tmp_path/"resultados")
