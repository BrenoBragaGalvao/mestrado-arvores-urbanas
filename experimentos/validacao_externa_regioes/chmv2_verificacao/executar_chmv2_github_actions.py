#!/usr/bin/env python3
"""Concordancia exploratoria entre a LR congelada da Area1 e alturas Meta/WRI CHMv2.
ATENCAO: F1 abaixo refere-se a pseudo-rotulos CHMv2, NAO verdade de campo.
Area1 tem F1 INTERNO ja calculado; nao comparar como protocolos identicos.
"""
import csv
import hashlib
import json
import math
import os
from pathlib import Path

import numpy as np
import pandas as pd
import rasterio
import requests
from pyproj import Transformer
from rasterio.windows import Window
from sklearn.metrics import confusion_matrix, f1_score, accuracy_score

BASE = Path(__file__).resolve().parent
INPUT = BASE / "600_pontos_predicao_congelada.csv"
OUT = Path(os.environ.get("CHM_OUTPUT", "chm_results"))
OUT.mkdir(exist_ok=True, parents=True)
DATA = OUT / "tiles"
DATA.mkdir(exist_ok=True)
TILES = {"2103121330", "2103123110"}
URLS = [
 "https://data.source.coop/tge-labs/meta-chm-v2/chm/{}.tif",
 "https://dataforgood-fb-data.s3.us-east-1.amazonaws.com/forests/v2/global/dinov3_global_chm_v2_ml3/chm/{}.tif",
]
TO_3857 = Transformer.from_crs(31982, 3857, always_xy=True)
TO_31982 = Transformer.from_crs(3857, 31982, always_xy=True)
TO_4326 = Transformer.from_crs(31982, 4326, always_xy=True)

def quadkey(x,y,level=10):
    lon,lat=TO_4326.transform(float(x),float(y))
    n=2**level
    tx=max(0,min(n-1,int((lon+180)/360*n)))
    ty=max(0,min(n-1,int((1-math.asinh(math.tan(math.radians(lat)))/math.pi)/2*n)))
    return "".join(str(((tx>>(level-i-1))&1)+2*((ty>>(level-i-1))&1)) for i in range(level))

def download(key):
    p=DATA / (key+".tif")
    if p.exists():
        with rasterio.open(p) as ds:
            if ds.count==1 and ds.crs.to_epsg()==3857:
                return p
        p.unlink()
    errors=[]
    for url_t in URLS:
        url=url_t.format(key)
        try:
            print("Download:",url,flush=True)
            with requests.get(url,stream=True,timeout=(30,160)) as resp:
                resp.raise_for_status()
                temp=p.with_suffix(".part")
                with temp.open("wb") as out:
                    for chunk in resp.iter_content(1024*1024):
                        if chunk:out.write(chunk)
            with rasterio.open(temp) as ds:
                assert ds.count==1 and ds.crs.to_epsg()==3857, "crs/nbands invalidos"
            temp.rename(p)
            print("Raster confirmado",key,p.stat().st_size,flush=True)
            return p
        except Exception as e:
            errors.append(str(e))
            p.with_suffix(".part").unlink(missing_ok=True)
    raise RuntimeError("Nao consegui obter CHMv2 "+key+": "+" | ".join(errors))

def chm_at(ds,x,y):
    x3857,y3857=TO_3857.transform(float(x),float(y))
    # 11m de margem no Mercator contem 5m no terreno (~lat30).
    rr,cc=ds.index(x3857,y3857)
    px=None
    if 0<=rr<ds.height and 0<=cc<ds.width:
        v=ds.read(1,window=Window(cc,rr,1,1),masked=True)[0,0]
        if not np.ma.is_masked(v) and np.isfinite(v) and int(v)!=255:
            px=float(v)
    # usar janela centrada por indice, evitando rasters de centenas de MB em memoria
    cw=max(12,int(math.ceil(12/max(ds.res[0],1e-5))))
    row0=max(0,rr-cw)
    row1=min(ds.height,rr+cw+1)
    col0=max(0,cc-cw)
    col1=min(ds.width,cc+cw+1)
    if row0>=row1 or col0>=col1:return (px,None,None,0,0)
    arr=ds.read(1,window=Window(col0,row0,col1-col0,row1-row0),masked=True)
    rows,cols=np.meshgrid(np.arange(row0,row1),np.arange(col0,col1),indexing="ij")
    xx,yy=rasterio.transform.xy(ds.transform,rows,cols,offset="center")
    ax,ay=TO_31982.transform(np.asarray(xx),np.asarray(yy))
    dist=(np.asarray(ax)-float(x))**2+(np.asarray(ay)-float(y))**2
    mask=(dist<=25+1e-7) & (~np.ma.getmaskarray(arr)) & (np.asarray(arr)!=255)
    z=np.asarray(arr)[mask].astype(float)
    if not len(z):return (px,None,None,0,0)
    return (px,float(z.max()),float(np.median(z)),len(z),int(np.sum(z==0)))

def label(h,rule):
    if h is None or not np.isfinite(h): return "sem_dado"
    if rule=="A0":return "grama" if h<=0 else "arvore"
    if rule=="A05":return "grama" if h<=0.5 else "arvore"
    if rule=="B":return "arvore" if h>=5 else ("grama" if h<=0.5 else "incerto")
    raise ValueError(rule)

def calc(g,rule):
    rows=g[g[rule].isin(["arvore","grama"])].copy()
    a=int(sum(rows[rule]=="arvore"));b=int(sum(rows[rule]=="grama"))
    res={"n_total":len(g),"n_usados":len(rows),"rotulos_arvore":a,"rotulos_grama":b,
         "n_incertos_sem_dados":len(g)-len(rows),"taxa_inclusao":round(len(rows)/len(g),6)}
    if not a or not b:
        res.update({"f1_macro_proxy":None,"acuracia_proxy":None,"matriz":[[0,0],[0,0]],"nota":"Nao ha ambas as classes CHMv2"})
        return res
    yt=rows[rule].to_numpy()
    yp=rows.predicao_modelo.to_numpy()
    res["f1_macro_proxy"]=round(float(f1_score(yt,yp,labels=["arvore","grama"],average="macro",zero_division=0)),6)
    res["acuracia_proxy"]=round(float(accuracy_score(yt,yp)),6)
    res["matriz"]=confusion_matrix(yt,yp,labels=["arvore","grama"]).tolist()
    return res

def main():
    data=pd.read_csv(INPUT)
    assert len(data)==600
    assert all(data.groupby("regiao").size()==200)
    data["quadkey"]=[quadkey(r.x,r.y) for r in data.itertuples()]
    assert set(data.quadkey)==TILES, data.quadkey.value_counts().to_dict()
    tiles={k:download(k) for k in sorted(TILES)}
    manifest={"produto":"CHMv2 (Meta/WRI), pseudo-rotulos, NAO validacao humana",
      "f1_area1_interno_250m":0.8375528327339948,
      "f1_area1_interno_500m":0.8567141723557405,
      "origem_predicao":"regressao_logistica.joblib treinada apenas na Area1",
      "rasters":{},"metricas":{}}
    for key,path in tiles.items():
        sha=hashlib.sha256()
        with path.open("rb") as f:
            for chunk in iter(lambda:f.read(1024*1024),b""):sha.update(chunk)
        with rasterio.open(path) as d:
            manifest["rasters"][key]={"sha256":sha.hexdigest(),"size":path.stat().st_size,
                                      "crs":str(d.crs),"res":list(d.res),"nodata":d.nodata,
                                      "type":d.dtypes[0]}
    dat=[]
    for key,part in data.groupby("quadkey"):
        with rasterio.open(tiles[key]) as d:
            for r in part.itertuples():
                h,m,med,n,nzero=chm_at(d,r.x,r.y)
                dat.append({"regiao":r.regiao,"amostra_id":r.amostra_id,"x":r.x,"y":r.y,
                            "bloco_500m":r.bloco_500m,"segmento_id":r.segmento_id,
                            "predicao_modelo":r.predicao_modelo,"quadkey":key,
                            "meta_pixel":h,"meta_max5":m,"meta_mediana5":med,
                            "n_pixels5":n,"n_zeros5":nzero,
                            "A0":label(m,"A0"),"A05":label(m,"A05"),"B":label(m,"B")})
    df=pd.DataFrame(dat).sort_values(["regiao","amostra_id"])
    assert len(df)==600
    df.to_csv(OUT/"600_pontos_mais_CHM.csv",index=False)
    for region,g in df.groupby("regiao"):
        manifest["metricas"][region]={
          "n_blocos_500m":int(g.bloco_500m.nunique()),
          "n_meta_max5_igual_zero":int((g.meta_max5==0).sum()),
          "n_meta_pixel_igual_zero":int((g.meta_pixel==0).sum()),
          "alturas_ausentes":int(g.meta_max5.isna().sum()),
          "estrategias":{rule:calc(g,rule) for rule in ["A0","A05","B"]}
        }
    manifest["advertencia"]="No CHMv2, valor 0 pode ser ausência de altura real OU NoData. F1 calculado com pseudo-rótulos CHMv2 não é desempenho validado por inspeção humana."
    (OUT/"resumo_f1_chmv2.json").write_text(json.dumps(manifest,indent=2,ensure_ascii=False),encoding="utf-8")
    print("CHM_SUMMARY_JSON="+json.dumps(manifest["metricas"],ensure_ascii=False),flush=True)
    print("CHM_OK: gerados 600_pontos_mais_CHM.csv e resumo_f1_chmv2.json")

if __name__=="__main__":
    main()
