#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Amostragem ESPACIAL CEGA para validação geográfica externa de árvores/grama.

Sem rótulos nas novas regiões, cria amostras georreferenciadas SEM revelar
a previsão dos classificadores ao anotador. A interpretação visual humana
é independente do modelo, e os pontos nunca são usados para retreinamento.

Uso:
 python preparar_rotulacao.py gerar --segmentos pred/segmento_id.tif \
        --out rotulacao --n 200 --bloco-m 250
 # Anote classe_verificada em rotulacao/amostras_para_anotar.gpkg
 python preparar_rotulacao.py exportar --anotadas amostras_para_anotar.gpkg \
        --out rotulacao/rotulos_verificados
"""
from __future__ import annotations
import argparse
import json
from collections import defaultdict
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
from rasterio.windows import Window
from shapely.geometry import Point


def generate_segments(ids: Path, target: int, block: float, seed: int, out: Path,
                      exclude_aoi: Path | None=None, exclusion_m:float=25):
    if target<20:
        raise ValueError("Amostragem de avaliação recomenda no mínimo 20 pontos.")
    out.mkdir(parents=True,exist_ok=True)
    annotation_path=out/"amostras_para_anotar.gpkg"
    if annotation_path.exists():
        raise FileExistsError(f"Já existe saída de rotulação: {annotation_path}")
    candidates=defaultdict(list)
    rng=np.random.default_rng(seed)
    with rasterio.open(ids) as ds:
        if not ds.crs or not ds.crs.is_projected:
            raise ValueError("Exige-se raster em CRS projetado em metros.")
        if ds.crs.linear_units not in {"metre", "meter", "metres", "meters", "m"}:
            # Pyproj/GDAL retornam usualmente 'metre' ou 'meter'.
            raise ValueError(f"CRS projetado não possui unidades métricas: {ds.crs.linear_units}")
        excluded_area=None
        if exclude_aoi is not None:
            if exclusion_m<0:
                raise ValueError("Exclusão espacial negativa")
            excluded=gpd.read_file(exclude_aoi)
            if excluded.empty or excluded.crs is None:
                raise ValueError("AOI de exclusão vazia ou sem CRS")
            excluded_area=excluded.to_crs(ds.crs).geometry.union_all().buffer(exclusion_m)
        for r0 in range(0,ds.height,256):
            for c0 in range(0,ds.width,256):
                win=Window(c0,r0,min(256,ds.width-c0),min(256,ds.height-r0))
                v=ds.read(1,window=win)
                valid=np.flatnonzero(v.ravel()>0)
                if not valid.size:
                    continue
                # Amostra aleatória independente da classe prevista.
                choice=rng.choice(valid,size=min(4,valid.size),replace=False)
                for pix in choice:
                    dr,dc=np.unravel_index(pix,v.shape)
                    row,col=r0+int(dr),c0+int(dc)
                    x,y=ds.xy(row,col,offset="center")
                    if excluded_area is not None and excluded_area.covers(Point(x,y)):
                        continue
                    key=(int(np.floor(x/block)),int(np.floor(y/block)))
                    candidates[key].append((int(v[int(dr),int(dc)]),float(x),float(y)))
        groups=list(candidates.keys())
        rng.shuffle(groups)
        points=[]
        used_segments=set()
        for key in groups:
            if len(points)>=target:
                break
            items=candidates[key]
            rng.shuffle(items)
            for sid,x,y in items:
                if sid not in used_segments:
                    points.append((sid,x,y,key))
                    used_segments.add(sid)
                    break
        if not points:
            raise RuntimeError("Raster não contém regiões válidas para amostragem.")
        gdf=gpd.GeoDataFrame({
            "amostra_id":[f"V{n+1:04d}" for n in range(len(points))],
            "classe_verificada":[""]*len(points),
            "observacoes":[""]*len(points),
            "bloco_m":[block]*len(points),
        },geometry=[Point(x,y) for _,x,y,_ in points],crs=ds.crs)
        gdf.to_file(annotation_path,driver="GPKG")
        gdf.drop(columns="geometry").assign(x=[x for _,x,_,_ in points],
                                           y=[y for _,_,y,_ in points]).to_csv(
            out/"amostras_para_anotar.csv",index=False)
        # Registro confidencial da associação a IDs, que o anotador não precisa ver.
        pd.DataFrame({
            "amostra_id":gdf.amostra_id,
            "segmento_id":[s for s,_,_,_ in points],
            "bloco_espacial":[f"{a}_{b}" for _,_,_,(a,b) in points]
        }).to_csv(out/"protocolo_amostragem.csv",index=False)
        manifest={
            "tipo":"amostragem espacial cega para anotação independente",
            "n_pretendido":target,"n_gerado":len(points),"bloco_m":block,"semente":seed,
            "regiao_crs":str(ds.crs),
            "area1_excluida":bool(exclude_aoi is not None),
            "buffer_exclusao_m":exclusion_m if exclude_aoi is not None else None,
            "classes_aceitas":["arvore","grama","incerto"],
            "regra":"Previsões dos classificadores não foram usadas para escolher nem rotular as amostras.",
            "advertencia":"Amostragem com um candidato por bloco: cobertura espacial, não amostra aleatória uniforme de pixels; não garante proporção real de classes."
        }
    (out/"metodologia_amostragem.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding="utf-8")
    print("Anote as classes em",annotation_path,"| pontos:",len(points))


def export_labels(source: Path, out: Path):
    if not source.is_file():
        raise FileNotFoundError(source)
    gdf=gpd.read_file(source)
    if gdf.crs is None:
        raise ValueError("O GeoPackage rotulado não possui CRS")
    if not gdf.geometry.geom_type.eq("Point").all():
        raise ValueError("Todas as amostras precisam ser pontos")
    expected={"arvore","grama","incerto"}
    if "classe_verificada" not in gdf or "amostra_id" not in gdf:
        raise ValueError("Faltam amostra_id ou classe_verificada")
    classes=gdf.classe_verificada.fillna("").astype(str).str.strip().str.lower()
    values=set(classes)
    if not values.issubset(expected|{""}):
        raise ValueError(f"Classes inválidas: {sorted(values-expected-{''})}")
    if gdf.amostra_id.duplicated().any():
        raise ValueError("IDs de amostra duplicados")
    out.mkdir(parents=True,exist_ok=True)
    labels={}
    for cls,filename in (("arvore","Arvores.gpkg"),("grama","Grama.gpkg")):
        valid=gdf.loc[classes.eq(cls)].copy()
        if len(valid)<5:
            raise ValueError(f"Apenas {len(valid)} exemplos da classe {cls}: mínimo técnico 5.")
        valid.to_file(out/filename,driver="GPKG")
        labels[cls]=len(valid)
    state={"registros_total":len(gdf),"validados":labels,
           "incertos":int(classes.eq("incerto").sum()),
           "sem_rotulo":int(classes.eq("").sum()),
           "protocolo":"Os rótulos foram produzidos externamente; revisar qualidade, cegamento e independência."}
    (out/"manifesto_rotulacao.json").write_text(json.dumps(state,ensure_ascii=False,indent=2),encoding="utf-8")
    print("Rótulos independentes exportados em",out,"| classes:",labels)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    sub=p.add_subparsers(dest="cmd",required=True)
    g=sub.add_parser("gerar")
    g.add_argument("--segmentos",required=True,type=Path)
    g.add_argument("--out",required=True,type=Path)
    g.add_argument("--n",type=int,default=200)
    g.add_argument("--bloco-m",type=float,default=250)
    g.add_argument("--semente",type=int,default=20261112)
    g.add_argument("--excluir-aoi",type=Path,
                   help="Sagrada Família: polígono Area1 a excluir da amostragem cega")
    g.add_argument("--buffer-exclusao-m",type=float,default=25)
    x=sub.add_parser("exportar")
    x.add_argument("--anotadas",required=True,type=Path)
    x.add_argument("--out",required=True,type=Path)
    a=p.parse_args()
    if a.cmd=="gerar":
        generate_segments(a.segmentos,a.n,a.bloco_m,a.semente,a.out,
                          a.excluir_aoi,a.buffer_exclusao_m)
    else:
        export_labels(a.anotadas,a.out)


if __name__=="__main__":
    main()
