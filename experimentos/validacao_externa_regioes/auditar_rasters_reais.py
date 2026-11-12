#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Verificação real de GeoTIFFs das novas regiões, sem rótulos e sem treino.

Amostra algumas janelas 256×256, testa os mesmos atributos e segmentação
Quickshift do protocolo Area1. Não mede F1 nem faz classificação treinada.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import rasterio
from rasterio.windows import Window
from skimage.segmentation import quickshift

from aplicar_regiao import features_originales


def details(ds):
    return {
       "width":ds.width,"height":ds.height,"count":ds.count,
       "crs":str(ds.crs),"res":list(ds.res),"bounds":list(ds.bounds),
       "transform":list(tuple(ds.transform)[:6]),
       "dtypes":list(ds.dtypes),"descriptions":list(ds.descriptions),
       "colorinterp":[str(v.name) for v in ds.colorinterp],
       "nodata":ds.nodata,"tags":{k:str(v)[:160] for k,v in ds.tags().items()},
       "band_tags":[{k:str(v)[:180] for k,v in ds.tags(i).items()}
                    for i in range(1,ds.count+1)]
    }


def inspect(region: str, rgb_path:Path, multi_path:Path, dest:Path):
    dest.mkdir(parents=True,exist_ok=True)
    with rasterio.open(rgb_path) as rgb, rasterio.open(multi_path) as multi:
        meta={"region":region,"rgb":details(rgb),"multi":details(multi)}
        aligned=(
           rgb.crs == multi.crs and rgb.width==multi.width and
           rgb.height==multi.height and rgb.transform.almost_equals(multi.transform))
        same_extent=rgb.width==multi.width and rgb.height==multi.height and rgb.crs==multi.crs
        meta["aligned"]=aligned
        meta["same_grid_dimensions_and_crs"]=same_extent
        meta["bands_possible"]=rgb.count>=3 and multi.count>=4
        meta["nir_confirmed_by_metadata"]=bool(any(
          "nir" in (str(x).lower()) or "near infrared" in str(x).lower()
          for x in [*multi.descriptions,*(str(multi.tags(i)) for i in range(1,multi.count+1))]))
        meta["require_manual_band_order_confirmation"]=not meta["nir_confirmed_by_metadata"]
        meta["rasters_amostrados"]=[]
        if not meta["bands_possible"]:
            meta["status"]="bandas_insuficientes"
        elif not same_extent:
            meta["status"]="grades_ou_crs_diferentes_a_verificar"
        else:
            anchors=[
              (int(rgb.height*.2),int(rgb.width*.2)),
              (int(rgb.height*.5),int(rgb.width*.5)),
              (int(rgb.height*.8),int(rgb.width*.8))
            ]
            for index,(row,col) in enumerate(anchors):
                row=max(0,min(row,rgb.height-256))
                col=max(0,min(col,rgb.width-256))
                win=Window(col,row,min(256,rgb.width-col),min(256,rgb.height-row))
                if win.height<3 or win.width<3:
                    continue
                rgb_arr=np.moveaxis(rgb.read([1,2,3],window=win),0,-1)
                multi_arr=multi.read([1,2,3,4],window=win)
                valid=(rgb.read_masks(1,window=win)>0)&(multi.read_masks(4,window=win)>0)
                if not valid.any():
                    continue
                try:
                    segmentation=quickshift(rgb_arr,kernel_size=3,max_dist=5,ratio=.04,rng=42)
                    counts,features=features_originales(multi_arr,segmentation,valid)
                    good=(counts>0)&np.isfinite(features).all(axis=1)
                    feat=features[good]
                    segment_count=int(np.sum(counts>0))
                    correlation=[]
                    for band in range(3):
                        a=rgb_arr[...,band][valid].ravel().astype(float)
                        b=multi_arr[band][valid].ravel().astype(float)
                        if len(a)>1 and np.std(a)>0 and np.std(b)>0:
                            correlation.append(float(np.corrcoef(a,b)[0,1]))
                        else:
                            correlation.append(None)
                    meta["rasters_amostrados"].append({
                      "janela":index,"row":row,"col":col,"segmentos":segment_count,
                      "segmentos_com_atributos_finitos":len(feat),
                      "media_hsv":float(feat[:,0].mean()) if len(feat) else None,
                      "media_canny":float(feat[:,1].mean()) if len(feat) else None,
                      "media_ndvi":float(feat[:,2].mean()) if len(feat) else None,
                      "correlacao_rgb_multi_bandas_1a3":correlation,
                      "n_pixels_validos":int(valid.sum())
                    })
                except Exception as exc:
                    meta["rasters_amostrados"].append({
                      "janela":index,"erro":type(exc).__name__+": "+str(exc)[:220]})
            meta["status"]="amostra_quickshift_executada" if any(
                "segmentos" in x for x in meta["rasters_amostrados"]) else "amostra_sem_segmentos_validos"
        meta["nota"]=(
           "Quickshift e atributos em janelas amostrais com dados reais. "
           "Nenhum modelo foi treinado; nenhum F1 foi medido. "
           "Se não há confirmação de banda NIR, não chamar o quarto canal de NIR "
           "sem verificar sua origem e ordem.")
    result=dest/(region+"_metadados_quickshift_real.json")
    result.write_text(json.dumps(meta,indent=2,ensure_ascii=False),encoding="utf-8")
    print(json.dumps({"regiao":region,"status":meta["status"],
          "shape_rgb":[meta["rgb"]["height"],meta["rgb"]["width"]],
          "res_rgb":meta["rgb"]["res"],"bandas_rgb":meta["rgb"]["count"],
          "bandas_multi":meta["multi"]["count"],"crs":meta["rgb"]["crs"],
          "aligned":meta["aligned"],"tem_descritor_nir":meta["nir_confirmed_by_metadata"],
          "quickshift_amostras":meta["rasters_amostrados"]},ensure_ascii=False),flush=True)
    return meta


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--regiao",required=True)
    p.add_argument("--rgb",type=Path,required=True)
    p.add_argument("--multi",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    inspect(a.regiao,a.rgb,a.multi,a.out)


if __name__=="__main__":
    main()
