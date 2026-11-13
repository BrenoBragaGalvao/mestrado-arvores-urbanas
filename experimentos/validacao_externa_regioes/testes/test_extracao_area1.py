#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Testes sintéticos da reconstrução da base Area1; sem dados reais."""
import sys
from pathlib import Path

import numpy as np
import pytest
import rasterio
from rasterio.transform import from_origin
from shapely.geometry import box, mapping

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from extrair_base_area1 import aggregate, process_tile, run


def test_agregacao_apenas_pixels_mascarados():
    seg=np.array([[0,0],[1,1]],dtype="int32")
    a=np.array([[1.,3.],[5.,7.]])
    mask=np.array([[True,False],[True,True]])
    n,mu=aggregate(seg,a,mask)
    np.testing.assert_array_equal(n,[1,2])
    np.testing.assert_allclose(mu,[1,6])


def test_processamento_tile_com_referencias_sinteticas(tmp_path):
    rgb_file=tmp_path/"rgb.tif"
    multi_file=tmp_path/"multi.tif"
    rng=np.random.default_rng(8)
    rgb_data=rng.integers(1,255,size=(3,40,40),dtype=np.uint8)
    multi=np.zeros((4,40,40),dtype=np.uint16)
    multi[:3]=rgb_data.astype(np.uint16)
    multi[3]=np.full((40,40),4500,dtype="uint16")
    tr=from_origin(0,40,.5,.5)
    for path,arr in [(rgb_file,rgb_data),(multi_file,multi)]:
        with rasterio.open(path,"w",driver="GTiff",
            count=arr.shape[0],width=40,height=40,
            dtype=arr.dtype,transform=tr,crs="EPSG:31982") as dst:
            dst.write(arr)
    refs=[{"r":5,"c":5,"classe":"arvore","ref_id":"arvore_0"},
          {"r":25,"c":29,"classe":"grama","ref_id":"grama_0"}]
    geometry_store=[]
    with rasterio.open(rgb_file) as rgb,rasterio.open(multi_file) as ms:
        records,stats=process_tile(0,(0,0),refs,rgb,ms,
                                   [mapping(box(0,20,20,40))],
                                   geometry_store=geometry_store)
    assert len(geometry_store)==len({r["id"] for r in records})
    assert all("geometry" in x and x["geometry"]["type"] in ("Polygon","MultiPolygon")
               for x in geometry_store)
    assert stats["pontos"]==2
    assert len(records)==2
    assert set(rec["classe"] for rec in records)=={"arvore","grama"}
    assert np.isfinite([[rec["mean_intensity"],rec["mean_edges"],rec["mean_ndvi"]]
                       for rec in records]).all()
    assert all(rec["id"]>=0 for rec in records)


def test_ausencia_rasters_interrompe_sem_inventar_dados(tmp_path):
    with pytest.raises(FileNotFoundError):
        run(tmp_path,tmp_path/"out")
