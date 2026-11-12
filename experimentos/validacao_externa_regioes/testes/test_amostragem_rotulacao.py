#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Amostragem cega e exportação de rótulos com mosaico sintético."""
import sys
from pathlib import Path

import geopandas as gpd
import numpy as np
import rasterio
import pytest
from rasterio.transform import from_origin

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from preparar_rotulacao import generate_segments, export_labels


def test_amostras_geoespaciais_cegas_e_rotulos_exportados(tmp_path):
    mosaic=tmp_path/"ids.tif"
    data=np.arange(1024*1024,dtype=np.uint32).reshape((1024,1024))+1
    with rasterio.open(mosaic,"w",driver="GTiff",height=1024,width=1024,
                       count=1,dtype="uint32",crs="EPSG:3857",
                       transform=from_origin(0,1024,1,1)) as dst:
        dst.write(data,1)
    target=tmp_path/"rotulacao"
    generate_segments(mosaic,40,50,20261112,target)
    file=target/"amostras_para_anotar.gpkg"
    assert file.is_file()
    g=gpd.read_file(file)
    assert len(g)>=20
    assert g.classe_verificada.fillna("").eq("").all()
    assert g.amostra_id.is_unique
    assert g.crs.to_epsg()==3857
    g["classe_verificada"]=np.where(np.arange(len(g))%2==0,"arvore","grama")
    g.to_file(file,driver="GPKG")
    export_labels(file,target/"verificados")
    assert len(gpd.read_file(target/"verificados/Arvores.gpkg"))>=5
    assert len(gpd.read_file(target/"verificados/Grama.gpkg"))>=5
    assert (target/"protocolo_amostragem.csv").exists()


def test_sem_crs_nao_permite_criar_arquivo(tmp_path):
    # O teste usa sistema projetado pois a política exige metros.
    mosaic=tmp_path/"invalid.tif"
    with rasterio.open(mosaic,"w",driver="GTiff",height=32,width=32,
                       count=1,dtype="uint32",transform=from_origin(0,32,1,1)) as dst:
        dst.write(np.ones((32,32),dtype="uint32"),1)
    with pytest.raises(ValueError):
        generate_segments(mosaic,20,250,1,tmp_path/"out")
