#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Reconstrói SOMENTE a base rotulada Area1 com a segmentação Quickshift de 256 px.

Reproduz o processamento por quadrantes do notebook V2, sem os recortes de
512 px, sem K-Means e sem usar dados geográficos de teste. Os quadrantes sem
pontos conhecidos não precisam ser lidos para formar a base de treinamento:
o Quickshift é independente entre quadrantes.

As grades RGB e RGB+NIR da Area1 têm leve deslocamento. Para preservar a
aproximação do protocolo V2, usa a MESMA janela de pixels sem warp. Essa
aproximação fica registrada e não é automaticamente transferida a outros AOIs.

É uma NOVA execução, não substitui os CSVs históricos; confrontar registros.
"""
from __future__ import annotations

import argparse
import json
import math
import time
from collections import defaultdict
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
from rasterio.features import geometry_mask
from rasterio.windows import Window, transform as window_transform
from shapely.geometry import mapping
from skimage.color import rgb2hsv
from skimage.feature import canny
from skimage.segmentation import quickshift

TILE=256
FEATURES=("mean_intensity","mean_edges","mean_ndvi")
NAMES=("id","tile","sid","n_pixels","x","y",*FEATURES,"classe")
PACKAGES=("AOI_RGB_NEW.tif","AOI_NEW_MULTI.tif","AOI_new.shp","Arvores.gpkg","Grama.gpkg")


def build_references(folder: Path, rgb_ds) -> tuple[dict,list[dict]]:
    m=defaultdict(list)
    meta=[]
    for file_name,cl in (("Arvores.gpkg","arvore"),("Grama.gpkg","grama")):
        gdf=gpd.read_file(folder/file_name)
        if gdf.crs is None:
            raise ValueError(f"Referência {file_name} não possui CRS")
        if not gdf.geometry.geom_type.eq("Point").all():
            raise ValueError(f"Geometrias não pontuais em {file_name}")
        gdf=gdf.to_crs(rgb_ds.crs)
        for i,p in enumerate(gdf.geometry):
            row,col=map(int,rasterio.transform.rowcol(rgb_ds.transform,p.x,p.y))
            ok=0<=row<rgb_ds.height and 0<=col<rgb_ds.width
            record={"ref_id":f"{cl}_{i}","classe":cl,"r":row,"c":col,
                    "dentro_grade":ok,"x":float(p.x),"y":float(p.y)}
            meta.append(record)
            if ok:
                m[(row//TILE*TILE,col//TILE*TILE)].append(record)
    return dict(m),meta


def aggregate(seg,channel,mask):
    ids=seg.ravel().astype("int32")
    valid=mask.ravel()
    counts=np.bincount(ids[valid],minlength=int(seg.max())+1)
    sums=np.bincount(ids[valid],weights=np.asarray(channel,dtype=np.float64).ravel()[valid],minlength=len(counts))
    mean=np.divide(sums,counts,out=np.full(len(counts),np.nan),where=counts>0)
    return counts,mean


def process_tile(index:int,rc:tuple[int,int],refs:list[dict],rgb,multi,aois,
                 geometry_store=None):
    r0,c0=rc
    h=min(TILE,rgb.height-r0);w=min(TILE,rgb.width-c0)
    win=Window(c0,r0,w,h)
    trans=window_transform(win,rgb.transform)
    mask=geometry_mask(aois,out_shape=(h,w),transform=trans,invert=True)
    if not mask.any():
        return [],{"tile":index,"pontos":len(refs),"fora_aoi":len(refs),"segmentos":0}
    rgb_arr=np.moveaxis(rgb.read([1,2,3],window=win),0,-1)
    bands=multi.read([1,2,3,4],window=win)
    seg=quickshift(rgb_arr,kernel_size=3,max_dist=5,ratio=.04,rng=42).astype(np.int32)
    nir,red=bands[3].astype("float32"),bands[0].astype("float32")
    ndvi=(nir-red)/(nir+red+1e-8)
    brilho=rgb2hsv(np.moveaxis(bands[:3],0,-1))[...,2].astype("float32")
    bordas=canny(nir/10000,sigma=1).astype("float32")
    counts,b=aggregate(seg,brilho,mask)
    _,c=aggregate(seg,bordas,mask)
    _,d=aggregate(seg,ndvi,mask)
    row,col=np.indices((h,w),dtype="float32")
    _,rcenter=aggregate(seg,row,mask)
    _,ccenter=aggregate(seg,col,mask)
    rr=rcenter+r0+.5
    cc=ccenter+c0+.5
    xx=rgb.transform.c+rgb.transform.a*cc+rgb.transform.b*rr
    yy=rgb.transform.f+rgb.transform.d*cc+rgb.transform.e*rr
    if int(seg.max())>=65536:
        raise ValueError("Mais de 65.535 segmentos em quadrante; IDs não seguros")
    points=[]
    outside=0
    for p in refs:
        r,c0p=p["r"]-r0,p["c"]-c0
        if not mask[r,c0p]:
            outside+=1
            continue
        sid=int(seg[r,c0p])
        vec=(float(b[sid]),float(c[sid]),float(d[sid]))
        if not np.isfinite(vec).all() or counts[sid]<=0:
            outside+=1
            continue
        points.append(dict(id=int(index*65536+sid),tile=index,sid=sid,
                           n_pixels=int(counts[sid]),x=float(xx[sid]),
                           y=float(yy[sid]),mean_intensity=vec[0],mean_edges=vec[1],
                           mean_ndvi=vec[2],classe=p["classe"],ref_id=p["ref_id"]))
    if geometry_store is not None and points:
        # Gerar geometrias dos MESMOS segmentos rotulados, para embargo
        # geométrico exato de 25 m em vez de aproximação por centróides.
        from rasterio.features import shapes
        from shapely.geometry import shape, mapping
        from shapely.ops import unary_union
        from collections import defaultdict
        wanted={int(p["sid"]) for p in points}
        polygon_mask=mask & np.isin(seg,list(wanted))
        polygons=defaultdict(list)
        for polygon,sid in shapes(seg.astype("int32"),mask=polygon_mask,
                                  transform=trans):
            if int(sid) in wanted:
                polygons[int(sid)].append(shape(polygon))
        for sid in wanted:
            if not polygons[sid]:
                raise ValueError(f"Segmento {sid} sem polígono georreferenciado")
            merged=unary_union(polygons[sid])
            if not merged.is_valid or merged.is_empty:
                raise ValueError(f"Geometria inválida para o segmento {sid}")
            geometry_store.append({
                "segmento_id":str(index*65536+sid),
                "geometry":mapping(merged)
            })
    return points,{"tile":index,"pontos":len(refs),"fora_aoi":outside,
                   "segmentos":int(seg.max()+1),"validos":len(points)}


def run(area:Path,out:Path,expect:int=505,limit:int|None=None,resume:bool=False):
    out.mkdir(parents=True,exist_ok=True)
    missing=[s for s in PACKAGES if not (area/s).is_file()]
    if missing:
        raise FileNotFoundError(f"Ausentes arquivos da Area1: {missing}")
    signature={
        "area1":str(area.resolve()),
        "arquivos":{name:{"bytes":(area/name).stat().st_size,
                          "modificado_ns":(area/name).stat().st_mtime_ns}
                    for name in PACKAGES},
        "tamanho_quadrante_px":TILE,
        "esperado":expect,
        "quickshift":{"kernel_size":3,"max_dist":5,"ratio":.04,"rng":42},
        "features":list(FEATURES)
    }
    signature_path=out/"assinatura_reconstrucao.json"
    if signature_path.exists():
        if not resume or json.loads(signature_path.read_text(encoding="utf-8"))!=signature:
            raise ValueError("Checkpoint preexistente com entradas diferentes ou sem --retomar")
    else:
        if resume:
            raise FileNotFoundError("Sem checkpoint para retomar")
        signature_path.write_text(json.dumps(signature,ensure_ascii=False,indent=2),encoding="utf-8")
    tiles_out=out/"quadrantes_com_referencias"
    tiles_out.mkdir(exist_ok=True)
    started=time.monotonic()
    with rasterio.open(area/"AOI_RGB_NEW.tif") as rgb,rasterio.open(area/"AOI_NEW_MULTI.tif") as multi:
        if rgb.count<3 or multi.count<4 or rgb.crs is None or rgb.crs!=multi.crs or rgb.shape!=multi.shape:
            raise ValueError("Rasters RGB e RGB+NIR não possuem bandas/grade/CRS compatíveis.")
        grid_aligned=rgb.transform.almost_equals(multi.transform)
        aoi=gpd.read_file(area/"AOI_new.shp")
        if aoi.empty or aoi.crs is None:
            raise ValueError("AOI_new.shp vazio ou sem CRS")
        aois=[mapping(g) for g in aoi.to_crs(rgb.crs).geometry if g is not None and not g.is_empty]
        refs,inventory=build_references(area,rgb)
        nrows=math.ceil(rgb.height/TILE);ncols=math.ceil(rgb.width/TILE)
        if len(inventory)!=510:
            raise ValueError(f"Expected original 510 point records; found {len(inventory)}. Check inputs.")
        selected=sorted(refs.items(),key=lambda pair:(pair[0][0],pair[0][1]))
        completed=0
        for (r0,c0),points in selected:
            index=(r0//TILE)*ncols+(c0//TILE)
            dest=tiles_out/f"tile_{index:04d}.csv"
            check=tiles_out/f"tile_{index:04d}.meta.json"
            geo_path=tiles_out/f"tile_{index:04d}.geometrias.json"
            if dest.is_file() and check.is_file() and geo_path.is_file():
                if not resume:
                    raise FileExistsError(f"Quadrante já processado: {dest}. Use --retomar.")
                continue
            if limit is not None and completed>=limit:
                break
            geometries=[]
            records,stat=process_tile(index,(r0,c0),points,rgb,multi,aois,
                                      geometry_store=geometries)
            if len(geometries)!=len({p["id"] for p in records}):
                raise ValueError("Quantidade de polígonos distinta dos segmentos rotulados")
            pd.DataFrame(records,columns=(*NAMES,"ref_id")).to_csv(dest,index=False)
            geo_path.write_text(json.dumps(geometries),encoding="utf-8")
            check.write_text(json.dumps(stat,ensure_ascii=False,indent=2),encoding="utf-8")
            completed+=1
            if completed%20==0:
                print(f"Novos quadrantes com pontos: {completed}/{len(selected)}",flush=True)
        files=list(tiles_out.glob("tile_*.csv"))
        total_ready=sum(all((tiles_out/f"tile_{(r//TILE)*ncols+(c//TILE):04d}.{suffix}").is_file()
                            for suffix in ("csv","meta.json","geometrias.json"))
                        for (r,c) in refs)
        full=total_ready==len(refs)
        if not full:
            partial={"estado":"parcial","tiles_com_referencia":len(refs),
                     "quadrantes_prontos":total_ready,
                     "progresso_pct":round(100*total_ready/max(len(refs),1),2)}
            (out/"estado_parcial.json").write_text(json.dumps(partial,indent=2),encoding="utf-8")
            print("BASE PARCIAL, NÃO TREINAR:",partial)
            return
        data=pd.concat([pd.read_csv(p) for p in sorted(files)],ignore_index=True)
        if data.empty:
            raise RuntimeError("Nenhum ponto foi associado a segmentos Quickshift.")
        nclass=data.groupby("id").classe.nunique()
        conflicts=set(nclass.index[nclass>1])
        valid=(data.loc[~data.id.isin(conflicts)]
               .drop_duplicates(subset="id")
               .sort_values("id").drop(columns="ref_id").reset_index(drop=True))
        # Agregar polígonos salvos junto com cada quadrante, sem reprocessar
        # o Quickshift no fechamento da reconstrução.
        from shapely.geometry import shape
        geometry_entries=[]
        for file in sorted(tiles_out.glob("tile_*.geometrias.json")):
            geometry_entries.extend(json.loads(file.read_text(encoding="utf-8")))
        unique_geometries={}
        for entry in geometry_entries:
            identifier=str(entry["segmento_id"])
            if identifier in unique_geometries:
                raise ValueError(f"Polígono duplicado do segmento {identifier}")
            unique_geometries[identifier]=shape(entry["geometry"])
        expected_ids=set(valid.id.astype(str))
        if not expected_ids.issubset(set(unique_geometries)):
            raise ValueError("Não existem polígonos para todos os segmentos da base")
        geometry_gdf=gpd.GeoDataFrame({
            "segmento_id":sorted(expected_ids),
        },geometry=[unique_geometries[i] for i in sorted(expected_ids)],crs=rgb.crs)
        if geometry_gdf.geometry.isna().any() or not geometry_gdf.is_valid.all():
            raise ValueError("Geometrias não válidas ou ausentes")
        diagnostics={
            "estado":"dados_reconstruidos_e_nao_publicados_historicamente",
            "quadrantes_total_raster":nrows*ncols,
            "quadrantes_com_pontos":len(refs),
            "quadrantes_processados_efetivamente":total_ready,
            "pontos_referencia_original":len(inventory),
            "pontos_na_grade":sum(1 for x in inventory if x["dentro_grade"]),
            "pontos_associados_a_segmentos":len(data),
            "ids_distintos_antes_conflito":int(data.id.nunique()),
            "segmentos_classes_conflitantes":len(conflicts),
            "segmentos_rotulados_unicos_validos":len(valid),
            "poligonos_segmentos_rotulados":len(geometry_gdf),
            "permite_embargo_geometrico_exato":True,
            "quantidade_esperada":expect,
            "compatibilidade_com_registro_historico":len(valid)==expect,
            "crs":str(rgb.crs),
            "rgb_multi_mesma_transformacao":grid_aligned,
            "alinhamento":("grades iguais" if grid_aligned else
                           "deslocamento de origem; mesma aproximação por índices de pixels do notebook V2"),
            "quickshift":{"kernel_size":3,"max_dist":5,"ratio":.04,"rng":42},
            "features":list(FEATURES),"janela_px":TILE,
            "reproducao":("quadrantes sem pontos conhecidos ignorados porque são independentes "
                          "para a formação da base supervisionada; para mapas completos "
                          "é necessário executar Quickshift em todos os quadrantes"),
            "segundos":time.monotonic()-started}
        (out/"auditoria_reproducao_area1.json").write_text(
            json.dumps(diagnostics,ensure_ascii=False,indent=2),encoding="utf-8")
        if len(valid)!=expect:
            valid.to_csv(out/"base_reconstruida_nao_confirmada.csv",index=False)
            raise RuntimeError(f"RESULTADO NÃO CONFERIDO: {len(valid)} segmentos vs {expect} esperados. "
                               "Verifique auditoria_reproducao_area1.json; não treine.")
        valid.to_csv(out/"rotulos_sem_duplicacao.csv",index=False)
        geometry_gdf.to_file(out/"E3c_geometrias_rotuladas_812.gpkg",driver="GPKG")
        print("Geometrias exatas dos segmentos:",out/"E3c_geometrias_rotuladas_812.gpkg")
        print(f"Base Area1 OK: {len(valid)} segmentos | {len(refs)} quadrantes com referências | "
              f"{nrows*ncols} quadrantes totais. Arquivo: {out/'rotulos_sem_duplicacao.csv'}")


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--area1",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--esperado",type=int,default=505)
    p.add_argument("--limite-quadrantes",type=int)
    p.add_argument("--retomar",action="store_true")
    a=p.parse_args()
    run(a.area1,a.out,a.esperado,a.limite_quadrantes,a.retomar)


if __name__=="__main__":
    main()
