#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Mede SOBREPOSIÇÃO REAL da Area1 e imagens regionais com as suas geometrias.

Não transfere pontos árvore/grama para outras cidades. Retorna interseção
entre o polígono Area1 (AOI_new.shp) e o retângulo dos pixels RGB regionais,
além de quantos dos 510 pontos pertencem a cada footprint. Não comprova
identidade pixel-a-pixel nem torna os 510 pontos um teste independente.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import geopandas as gpd
import rasterio
from shapely.geometry import Polygon


def raster_footprint(src):
    t=src.transform
    coords=[t*(0,0),t*(src.width,0),t*(src.width,src.height),
            t*(0,src.height)]
    return Polygon(coords)


def inspect(area1_aoi:Path, trees:Path, grass:Path, regional_rgb:Path,
            region:str, dest:Path, buffer_m:float=25):
    dest.mkdir(parents=True,exist_ok=True)
    with rasterio.open(regional_rgb) as ds:
        if ds.crs is None or not ds.crs.is_projected:
            raise ValueError("Imagem regional precisa de CRS projetado.")
        if ds.crs.linear_units not in {"metre","meter","metres","meters","m"}:
            raise ValueError("Área e exclusão espacial exigem unidades em metros.")
        roi=gpd.read_file(area1_aoi)
        if roi.empty or roi.crs is None:
            raise ValueError("Polígono da Area1 vazio ou sem CRS.")
        roi=roi.to_crs(ds.crs)
        mask=roi.geometry.union_all()
        if mask.is_empty or not mask.is_valid:
            raise ValueError("Polígono Area1 inválido.")
        image=raster_footprint(ds)
        intersection=mask.intersection(image)
        inside=float(intersection.area)
        aoi_area=float(mask.area)
        pct=inside/aoi_area if aoi_area>0 else 0.
        polygon_buffer=mask.buffer(buffer_m)
        study_data={
            "regiao":region,
            "aoi_area1_m2":aoi_area,
            "intersecao_area1_com_regiao_m2":inside,
            "frac_area1_coberta_por_regiao":pct,
            "area_regiao_rgb_m2":float(image.area),
            "regiao_rgb_bbox":list(ds.bounds),
            "area1_aoi_bbox":list(mask.bounds),
            "distancia_exclusao_m":buffer_m,
            "aoi_inteira_contida":bool(image.covers(mask)),
            "intersecao_nao_vazia":not intersection.is_empty,
            "referencias":{},
            "alerta":"Sobreposição não prova identidade dos pixels; pontos dentro da Area1 ou a menos de 25m dela são inelegíveis como teste independente."
        }
        for path,name in [(trees,"arvore"),(grass,"grama")]:
            refs=gpd.read_file(path)
            if refs.empty or refs.crs is None:
                raise ValueError("Referências precisam ter CRS válido.")
            if not refs.geometry.geom_type.eq("Point").all():
                raise ValueError("Esperados pontos, não polígonos ou linhas.")
            refs=refs.to_crs(ds.crs)
            num=len(refs)
            in_roi=int(refs.geometry.apply(mask.covers).sum())
            in_reg=int(refs.geometry.apply(image.covers).sum())
            candidate=int(refs.geometry.apply(
                lambda point:image.covers(point) and not polygon_buffer.covers(point)).sum())
            study_data["referencias"][name]={
                "original":num,
                "dentro_da_area1":in_roi,
                "dentro_da_imagem_regional":in_reg,
                "fora_do_buffer_area1_dentro_regiao":candidate,
                "observacao":"Candidatos geométricos não substituem coleta independente de novos rótulos."
            }
        file=dest/(region+"_sobreposicao_area1.json")
        file.write_text(json.dumps(study_data,ensure_ascii=False,indent=2),encoding="utf-8")
        print(json.dumps({
            "regiao":region,"percentual_area1_coberta":round(pct*100,3),
            "area1_inteira_contida":study_data["aoi_inteira_contida"],
            "referencias":study_data["referencias"]
        },ensure_ascii=False),flush=True)
        return study_data


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--area1-aoi",required=True,type=Path)
    p.add_argument("--arvores",required=True,type=Path)
    p.add_argument("--grama",required=True,type=Path)
    p.add_argument("--rgb-regional",required=True,type=Path)
    p.add_argument("--regiao",required=True)
    p.add_argument("--exclusao-m",type=float,default=25)
    p.add_argument("--out",required=True,type=Path)
    a=p.parse_args()
    inspect(a.area1_aoi,a.arvores,a.grama,a.rgb_regional,a.regiao,a.out,a.exclusao_m)


if __name__=="__main__":
    main()
