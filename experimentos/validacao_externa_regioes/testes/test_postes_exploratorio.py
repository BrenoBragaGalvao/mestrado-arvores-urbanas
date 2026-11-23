#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Teste ilustrativo de distância 2D a postes, não é risco elétrico."""
import json
import sys
from pathlib import Path

import geopandas as gpd
import numpy as np
import rasterio
from rasterio.transform import from_origin
from shapely.geometry import Point

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from proximidade_postes_opcional import run


def test_postes_e_arvores_previstas_sinteticos(tmp_path):
    folder=tmp_path/"predicoes"
    folder.mkdir()
    map_=np.zeros((32,32),dtype=np.uint8)
    map_[8,8]=1
    maps={}
    for i in range(8):
        name=f"modelo_{i}"
        file=folder/f"classificacao_{name}.tif"
        with rasterio.open(file,"w",driver="GTiff",height=32,width=32,
                           count=1,dtype="uint8",nodata=0,crs="EPSG:3857",
                           transform=from_origin(0,32,1,1)) as ds:
            ds.write(map_,1)
        maps[name]=str(file)
    (folder/"manifesto_execucao.json").write_text(
        json.dumps({"estado":"concluido","mapas":maps}),encoding="utf-8")
    poles=tmp_path/"postes.gpkg"
    gpd.GeoDataFrame({"nome":["p1","p2"]},geometry=[
        Point(8.5,32-8-.5),Point(30,2)],crs="EPSG:3857").to_file(poles,driver="GPKG")
    out=tmp_path/"resultados"
    summary=run(folder,poles,out)
    assert len(summary)==8
    assert summary.postes_analisados.eq(2).all()
    assert summary.postes_ate_1m.eq(1).all()
    assert summary.postes_ate_5m.eq(1).all()
    assert (out/"metodologia.json").exists()
