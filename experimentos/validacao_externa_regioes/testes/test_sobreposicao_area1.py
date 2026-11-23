#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
from pathlib import Path
import geopandas as gpd
import rasterio
import numpy as np
from shapely.geometry import box,Point
from rasterio.transform import from_origin

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from auditar_sobreposicao_area1 import inspect


def test_aoi_parcialmente_abrangida_nunca_considera_pontos_iguais_teste(tmp_path):
    area=tmp_path/"aoi.gpkg"
    trees=tmp_path/"arvores.gpkg"
    grass=tmp_path/"grama.gpkg"
    rgb=tmp_path/"rgb.tif"
    gpd.GeoDataFrame(geometry=[box(100,100,200,200)],crs="EPSG:31982").to_file(area,driver="GPKG")
    gpd.GeoDataFrame(geometry=[Point(150,150),Point(200,200)],crs="EPSG:31982").to_file(trees,driver="GPKG")
    gpd.GeoDataFrame(geometry=[Point(180,180),Point(240,240)],crs="EPSG:31982").to_file(grass,driver="GPKG")
    with rasterio.open(rgb,"w",driver="GTiff",count=3,width=100,height=100,
                       dtype="uint8",crs="EPSG:31982",transform=from_origin(150,250,1,1)) as ds:
        ds.write(np.zeros((3,100,100),dtype="uint8"))
    report=inspect(area,trees,grass,rgb,"sagrada_exemplo",tmp_path/"out",buffer_m=25)
    assert abs(report["frac_area1_coberta_por_regiao"]-.25)<1e-10
    assert report["aoi_inteira_contida"] is False
    assert report["referencias"]["arvore"]["dentro_da_area1"]==2
    assert report["referencias"]["arvore"]["fora_do_buffer_area1_dentro_regiao"]==0
    assert report["referencias"]["grama"]["fora_do_buffer_area1_dentro_regiao"]==1
