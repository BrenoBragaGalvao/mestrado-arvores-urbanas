#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Teste sintético do processamento raster e salvamento/retomada."""
import json
import sys
from pathlib import Path

import joblib
import numpy as np
import rasterio
from rasterio.transform import from_origin
from sklearn.dummy import DummyClassifier

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from aplicar_regiao import run


def write_tif(path, data):
    with rasterio.open(path,"w",driver="GTiff",width=data.shape[2],
                       height=data.shape[1],count=data.shape[0],
                       dtype=data.dtype,crs="EPSG:31982",
                       transform=from_origin(100,200,.5,.5)) as dst:
        dst.write(data)


def test_processa_retomada_e_oito_mapas(tmp_path):
    rgb=tmp_path/"rgb.tif"
    multi=tmp_path/"multi.tif"
    rng=np.random.default_rng(42)
    rgb_data=rng.integers(20,220,size=(3,32,32),dtype=np.uint8)
    mult=np.zeros((4,32,32),dtype=np.uint16)
    mult[:3]=rgb_data.astype("uint16")
    mult[3]=5000
    write_tif(rgb,rgb_data)
    write_tif(multi,mult)
    models_dir=tmp_path/"models"
    models_dir.mkdir()
    meta={"features":["mean_intensity","mean_edges","mean_ndvi"],
          "classes":["arvore","grama"],"modelos":{}}
    X=np.array([[.2,.04,.1],[.8,.10,.6]])
    y=np.array(["arvore","grama"])
    for i in range(8):
        model=DummyClassifier(strategy="constant",constant="arvore").fit(X,y)
        name=f"modelo_{i}"
        joblib.dump(model,models_dir/(name+".joblib"))
        meta["modelos"][name]={"arquivo":name+".joblib"}
    (models_dir/"manifesto_modelos.json").write_text(json.dumps(meta),encoding="utf-8")
    result=tmp_path/"pred"
    first=run("teste_regiao",rgb,multi,models_dir,result,
              resume=False,make_previews=False,limit_tiles=1)
    assert first["estado"]=="concluido"
    assert first["quadrantes_concluidos"]==1
    assert len(first["mapas"])==8
    with rasterio.open(result/"segmento_id.tif") as src:
        ids=src.read(1)
        assert ids.shape==(32,32)
        assert int(ids.max())>0
    for path in first["mapas"].values():
        with rasterio.open(path) as src:
            assert set(np.unique(src.read(1))).issubset({0,1,2})
            assert np.count_nonzero(src.read(1))>0
    second=run("teste_regiao",rgb,multi,models_dir,result,
               resume=True,make_previews=False,limit_tiles=1)
    assert second["estado"]=="concluido"
    assert second["quadrantes_concluidos"]==1
    assert (result/"segmentos.csv.gz").exists()
