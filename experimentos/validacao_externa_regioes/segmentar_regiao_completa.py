#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Executa Quickshift REAL na imagem RGB inteira, sem modelos supervisionados.

Propósito: verificar a escala integral da segmentação nas quatro imagens
regionais. NÃO é classificação árvore/grama e NÃO gera F1-macro.

Trabalha com quadrantes até 256 x 256 px, o mesmo Quickshift da Area1.
Salva contagem por quadrante, manifesto e uma pré-visualização das bordas,
sem publicar os TIFFs originais nem os segmentos completos no GitHub.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import time
from pathlib import Path

import numpy as np
import rasterio
from rasterio.enums import Resampling
from rasterio.windows import Window
from skimage.segmentation import quickshift


PARAMS = dict(kernel_size=3,max_dist=5,ratio=.04,rng=42)


def process(region: str, rgb_path: Path, out: Path, max_tiles=None, preview_dim=1000):
    out.mkdir(parents=True,exist_ok=True)
    chunks=out/"quadrantes"
    chunks.mkdir(exist_ok=True)
    started=time.monotonic()
    with rasterio.open(rgb_path) as ds:
        if ds.count<3 or ds.crs is None:
            raise ValueError("RGB exige no mínimo três bandas com CRS válido.")
        ny=math.ceil(ds.height/256)
        nx=math.ceil(ds.width/256)
        total=ny*nx
        k=min(1.,preview_dim/max(ds.height,ds.width))
        ph=max(1,int(round(ds.height*k)))
        pw=max(1,int(round(ds.width*k)))
        preview=np.moveaxis(ds.read([1,2,3],out_shape=(3,ph,pw),
                resampling=Resampling.bilinear),0,-1).astype("float32")
        lo,hi=np.percentile(preview[np.isfinite(preview)],[2,98])
        preview=np.clip((preview-lo)/max(hi-lo,1e-8),0.,1.)
        boundaries=np.zeros((ph,pw),dtype=bool)
        already=0
        for yy in range(ny):
            for xx in range(nx):
                i=yy*nx+xx
                info_file=chunks/f"bloco_{i:06d}.json"
                if info_file.exists():
                    already+=1
                    continue
                if max_tiles is not None and already>=max_tiles:
                    break
                c=xx*256
                r=yy*256
                h=min(256,ds.height-r)
                w=min(256,ds.width-c)
                window=Window(c,r,w,h)
                raw=np.moveaxis(ds.read([1,2,3],window=window),0,-1)
                valid=ds.read_masks(1,window=window)>0
                records={"quadrante":i,"raster_row":r,"raster_col":c,
                    "largura":w,"altura":h,
                    "pixels_validos":int(valid.sum()),"segmentos":0}
                if valid.any() and h>=3 and w>=3:
                    if not np.isfinite(raw).all():
                        raise ValueError(f"NaN/inf no quadrante {i}")
                    segmentation=quickshift(raw,**PARAMS)
                    ids=np.unique(segmentation[valid])
                    records["segmentos"]=len(ids)
                    # Marcamos APENAS fronteiras internas do quadrante e pixels
                    # validos; linhas artificiais entre quadrantes não são bordas.
                    edges=np.zeros(valid.shape,dtype=bool)
                    edges[:,1:] = (segmentation[:,1:]!=segmentation[:,:-1])&valid[:,1:]&valid[:,:-1]
                    edges[1:,:] |= (segmentation[1:,:]!=segmentation[:-1,:])&valid[1:,:]&valid[:-1,:]
                    by,bx=np.where(edges)
                    if len(bx):
                        py=np.floor((r+by+.5)*ph/ds.height).astype(int)
                        px=np.floor((c+bx+.5)*pw/ds.width).astype(int)
                        boundaries[np.clip(py,0,ph-1),np.clip(px,0,pw-1)]=True
                info_file.write_text(json.dumps(records,ensure_ascii=False),encoding="utf-8")
                already+=1
                if already%100==0:
                    print(json.dumps({"regiao":region,"quadrantes_prontos":already,
                        "quadrantes_previstos":total}),flush=True)
            if max_tiles is not None and already>=max_tiles:
                break
        files=sorted(chunks.glob("bloco_*.json"))
        rows=[json.loads(f.read_text(encoding="utf-8")) for f in files]
        if len({x["quadrante"] for x in rows})!=len(rows):
            raise ValueError("IDs de quadrantes duplicados")
        complete=len(rows)==total
        csv_path=out/"quickshift_por_quadrante.csv"
        with csv_path.open("w",newline="",encoding="utf-8") as fp:
            writer=csv.DictWriter(fp,fieldnames=[
                "quadrante","raster_row","raster_col","largura","altura",
                "pixels_validos","segmentos"])
            writer.writeheader()
            writer.writerows(sorted(rows,key=lambda x:x["quadrante"]))
        summary={
            "regiao":region,
            "tipo":"segmentacao_nao_supervisionada_quickshift",
            "estado":"concluido" if complete else "parcial",
            "raster_RGB":str(rgb_path.name),
            "altura":ds.height,"largura":ds.width,
            "crs":str(ds.crs),"resolucao_m":list(ds.res),
            "quadrantes_previstos":total,
            "quadrantes_concluidos":len(rows),
            "segmentos_nao_rotulados":sum(x["segmentos"] for x in rows),
            "pixels_validos":sum(x["pixels_validos"] for x in rows),
            "parametros_quickshift":PARAMS,
            "f1_macro":None,
            "aplicou_modelos_supervisionados":False,
            "nota":"Segmentos Quickshift nao sao classes arvore/grama nem amostras validadas.",
            "segundos_execucao":round(time.monotonic()-started,2)
        }
        (out/"resultado_quickshift.json").write_text(json.dumps(
            summary,ensure_ascii=False,indent=2),encoding="utf-8")
        if complete:
            from matplotlib import pyplot as plt
            overlay=preview.copy()
            overlay[boundaries] = [0.0,0.95,1.]
            plt.imsave(out/"preview_quickshift.png",overlay)
        print(json.dumps({k:summary[k] for k in (
            "regiao","estado","quadrantes_concluidos",
            "quadrantes_previstos","segmentos_nao_rotulados",
            "pixels_validos","segundos_execucao")},ensure_ascii=False),flush=True)
        return summary


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--regiao",required=True)
    p.add_argument("--rgb",required=True,type=Path)
    p.add_argument("--out",required=True,type=Path)
    p.add_argument("--limite-quadrantes",type=int)
    p.add_argument("--preview-dim",type=int,default=1000)
    a=p.parse_args()
    process(a.regiao,a.rgb,a.out,a.limite_quadrantes,a.preview_dim)


if __name__=="__main__":
    main()
