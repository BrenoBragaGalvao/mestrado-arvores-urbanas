#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Proposta 2 opcional: distância horizontal aproximada a postes.

Mede distância 2D do PONTO de poste até o CENTRO do pixel mais próximo
classificado como árvore, em janela de raio configurável. Não é distância
até cabos, não usa alturas e NÃO comprova risco elétrico. Não comparável
diretamente ao método histórico por polígonos/cluster 3.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
from rasterio.windows import Window


def closest_tree_pixel(ds, point, radius_m:float):
    row,col=map(int,ds.index(point.x,point.y))
    px=max(1,math.ceil(radius_m / min(abs(ds.res[0]),abs(ds.res[1]))))
    r0=max(0,row-px);r1=min(ds.height,row+px+1)
    c0=max(0,col-px);c1=min(ds.width,col+px+1)
    if r0>=r1 or c0>=c1:
        return float("nan")
    win=Window(c0,r0,c1-c0,r1-r0)
    mask=ds.read(1,window=win)
    rows,cols=np.where(mask==1)
    if not rows.size:
        return float("nan")
    xs,ys=ds.xy(rows+r0,cols+c0,offset="center")
    dist=np.hypot(np.asarray(xs,dtype=float)-point.x,
                  np.asarray(ys,dtype=float)-point.y)
    nearby=dist[dist<=radius_m]
    return float(nearby.min()) if nearby.size else float("nan")


def run(predictions:Path,poles:Path,out:Path,max_m:float=10):
    if max_m<5:
        raise ValueError("Raio máximo deve ser >=5 m para cobrir 1/3/5 m.")
    manifest_path=predictions/"manifesto_execucao.json"
    if not manifest_path.is_file():
        raise FileNotFoundError(manifest_path)
    manifest=json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("estado")!="concluido":
        raise RuntimeError("Mapas não concluídos; não analisar postes.")
    models=manifest["mapas"]
    if len(models)!=8:
        raise ValueError("São esperados oito mapas completos.")
    g=gpd.read_file(poles)
    if g.crs is None or g.empty:
        raise ValueError("Camada de postes vazia ou sem CRS.")
    if not g.geometry.geom_type.eq("Point").all():
        raise ValueError("Postes precisam ser pontos geográficos.")
    out.mkdir(parents=True,exist_ok=True)
    records=[]
    for name,raw_path in models.items():
        raster_path=Path(raw_path)
        if not raster_path.exists():
            raster_path=predictions/Path(raw_path).name
        if not raster_path.exists():
            raise FileNotFoundError(raster_path)
        with rasterio.open(raster_path) as ds:
            if ds.crs is None or not ds.crs.is_projected:
                raise ValueError("CRS raster deve ser projetado em metros.")
            if ds.crs.linear_units not in {"metre","meter","metres","meters","m"}:
                raise ValueError("Unidade linear não métrica.")
            data=g.to_crs(ds.crs)
            for i,p in enumerate(data.geometry):
                dist=closest_tree_pixel(ds,p,max_m)
                records.append({
                    "modelo":name,"poste_idx":i,"x":p.x,"y":p.y,
                    "min_distancia_centro_pixel_arvore_m":dist,
                    "arvore_prevista_ate_1m":bool(np.isfinite(dist) and dist<=1),
                    "arvore_prevista_ate_3m":bool(np.isfinite(dist) and dist<=3),
                    "arvore_prevista_ate_5m":bool(np.isfinite(dist) and dist<=5)})
    rows=pd.DataFrame(records)
    rows.to_csv(out/"proximidade_postes_por_modelo.csv",index=False)
    agg=(rows.groupby("modelo",as_index=False)
         .agg(postes_analisados=("poste_idx","size"),
              postes_ate_1m=("arvore_prevista_ate_1m","sum"),
              postes_ate_3m=("arvore_prevista_ate_3m","sum"),
              postes_ate_5m=("arvore_prevista_ate_5m","sum")))
    agg.to_csv(out/"resumo_postes.csv",index=False)
    (out/"metodologia.json").write_text(json.dumps({
        "status":"analise_exploratoria_possivel_com_arquivo_de_postes",
        "distancia":"2D da posição do poste ao CENTRO do pixel mais próximo classificado como árvore",
        "raio_busca_m":max_m,"limiares_m":[1,3,5],
        "cuidado":"Proximidade a postes não é proximidade a fios, nem estimativa de risco elétrico.",
        "nao_comparavel":"Não representa exatamente os polígonos e índices de porte do método histórico.",
        "sem_uso_altura":True
    },ensure_ascii=False,indent=2),encoding="utf-8")
    print(agg.to_string(index=False))
    return agg


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--predicoes",type=Path,required=True)
    p.add_argument("--postes",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--raio-m",type=float,default=10)
    a=p.parse_args()
    run(a.predicoes,a.postes,a.out,a.raio_m)


if __name__=="__main__":
    main()
