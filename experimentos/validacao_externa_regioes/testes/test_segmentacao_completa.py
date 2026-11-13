#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Verificação Quickshift em cobertura RGB sintética com quadrantes reais."""
import json
import sys
from pathlib import Path
import numpy as np
import rasterio
from rasterio.transform import from_origin
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from segmentar_regiao_completa import process


def test_segmenta_todas_as_janelas_sem_modelo_nem_f1(tmp_path):
    rgb=tmp_path/"small_rgb.tif"
    rng=np.random.default_rng(61)
    pixel=rng.integers(10,230,size=(3,300,300),dtype=np.uint8)
    with rasterio.open(rgb,"w",driver="GTiff",height=300,width=300,count=3,
        dtype="uint8",crs="EPSG:31982",transform=from_origin(100,200,.5,.5)) as dst:
        dst.write(pixel)
    result=process("area_sintetica",rgb,tmp_path/"report",preview_dim=160)
    assert result["estado"]=="concluido"
    assert result["quadrantes_previstos"]==4
    assert result["quadrantes_concluidos"]==4
    assert result["segmentos_nao_rotulados"]>0
    assert result["aplicou_modelos_supervisionados"] is False
    assert result["f1_macro"] is None
    assert (tmp_path/"report/preview_quickshift.png").exists()
    assert (tmp_path/"report/quickshift_por_quadrante.csv").exists()
    png_before=(tmp_path/"report/preview_quickshift.png").read_bytes()
    repeat=process("area_sintetica",rgb,tmp_path/"report",preview_dim=160)
    assert repeat["segmentos_nao_rotulados"]==result["segmentos_nao_rotulados"]
    assert (tmp_path/"report/preview_quickshift.png").read_bytes()==png_before
    assert len(list((tmp_path/"report/quadrantes").glob("*.edges")))==4
