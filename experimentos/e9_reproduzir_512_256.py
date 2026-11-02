#!/usr/bin/env python3
# coding: utf-8
"""Reexecução E9 em Area1: mesmos 119 recortes 512 px e dois modos Quickshift.

Uso no Colab, apos montar o Drive:
  python experimentos/e9_reproduzir_512_256.py --mode continuo_512 --area PATH --out PATH
  python experimentos/e9_reproduzir_512_256.py --mode quadrantes_256 --area PATH --out PATH
  python experimentos/e9_reproduzir_512_256.py --mode comparar --area PATH --out PATH

Cada modo deve ser executado num PROCESSO SEPARADO para permitir medir
ru_maxrss. Não modifica os rasters. Esta é nova implementação reexecutável;
só declarar reprodução numérica depois de confrontar CSVs de evidências E9.
"""
import argparse, json, math, os, platform, resource, time, gc
from pathlib import Path
import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
from rasterio.windows import Window
from skimage.segmentation import quickshift
from skimage.color import rgb2hsv
from skimage.feature import canny

MODOS=("continuo_512","quadrantes_256")
FEATURES=("mean_intensity","mean_edges","mean_ndvi")
def entradas(area):
    rgb=area/"AOI_RGB_NEW.tif"
    multi=area/"AOI_NEW_MULTI.tif"
    for p in (rgb,multi,area/"Arvores.gpkg",area/"Grama.gpkg"):
        if not p.is_file(): raise FileNotFoundError(str(p))
    return rgb,multi

def referencias(area, ds):
    out=[]
    for arquivo,classe in (("Arvores.gpkg","arvore"),("Grama.gpkg","grama")):
        pts=gpd.read_file(area/arquivo).to_crs(ds.crs)
        if not pts.geometry.geom_type.eq("Point").all():
            raise ValueError("Este protocolo E9 pressupoe pontos de referencia.")
        for idx,p in pts.geometry.items():
            r,c=rasterio.transform.rowcol(ds.transform,p.x,p.y)
            if 0<=r<ds.height and 0<=c<ds.width:
                out.append(dict(point_id=f"{classe}_{idx}",classe=classe,
                                r=int(r),c=int(c),x=float(p.x),y=float(p.y)))
    ref=pd.DataFrame(out).sort_values("point_id").reset_index(drop=True)
    if len(ref)!=510 or ref.point_id.duplicated().any():
        raise ValueError(f"Esperados 510 pontos originais unicos, obtidos {len(ref)}.")
    ref["row0"]=(ref.r//512)*512
    ref["col0"]=(ref.c//512)*512
    return ref

def media_segmentos(seg,array):
    flat=seg.ravel()
    n=int(seg.max())+1
    counts=np.bincount(flat,minlength=n)
    sums=np.bincount(flat,weights=np.asarray(array,dtype=np.float32).ravel(),minlength=n)
    return np.divide(sums,counts,out=np.full(n,np.nan,dtype=np.float64),where=counts>0)

def segmentar(area,out,modo):
    import skimage
    start=time.monotonic()
    arquivo_rgb,arquivo_multi=entradas(area)
    with rasterio.open(arquivo_rgb) as rgb_ds,rasterio.open(arquivo_multi) as ms_ds:
        if rgb_ds.shape!=ms_ds.shape or not rgb_ds.crs==ms_ds.crs or rgb_ds.count!=3 or ms_ds.count<4:
            raise ValueError("Bandas/grades ou CRS inesperados.")
        if not rgb_ds.transform.almost_equals(ms_ds.transform):
            import warnings
            warnings.warn("Grades RGB e RGB+NIR possuem deslocamento de origem. Este E9 reproduz a extração histórica por índices de pixels; documentar a aproximação espacial.",RuntimeWarning)
        ref=referencias(area,rgb_ds)
        grupos=ref.groupby(["row0","col0"],sort=True)
        if len(grupos)!=119:raise ValueError(f"Esperados 119 recortes, encontrados {len(grupos)}.")
        baseline=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024
        records=[]; total_segmentos=0; total_pixels=0; windows=0
        for (r0,c0),part in grupos:
            h=min(512,rgb_ds.height-int(r0));w=min(512,rgb_ds.width-int(c0))
            win=Window(int(c0),int(r0),w,h)
            rgb=np.moveaxis(rgb_ds.read(window=win),0,-1)
            multis=ms_ds.read(window=win)
            nir=multis[3].astype(np.float32);red=multis[0].astype(np.float32)
            ndvi=(nir-red)/(nir+red+1e-8)
            valor=rgb2hsv(np.moveaxis(multis[:3],0,-1))[...,2]
            bordas=canny(nir/10000,sigma=1).astype(np.float32)
            sub=[(0,h,0,w)] if modo=="continuo_512" else [
                (rr,min(rr+256,h),cc,min(cc+256,w))
                for rr in (0,256) for cc in (0,256) if rr<h and cc<w]
            for subindice,(ra,rb,ca,cb) in enumerate(sub):
                sg=quickshift(rgb[ra:rb,ca:cb],kernel_size=3,max_dist=5,ratio=.04,rng=42)
                nseg=int(sg.max())+1
                total_segmentos+=nseg
                mapas=(valor[ra:rb,ca:cb],bordas[ra:rb,ca:cb],ndvi[ra:rb,ca:cb])
                feat=[media_segmentos(sg,a) for a in mapas]
                for point in part.itertuples(index=False):
                    lr=int(point.r-r0);lc=int(point.c-c0)
                    if not (ra<=lr<rb and ca<=lc<cb):continue
                    sid=int(sg[lr-ra,lc-ca])
                    vector=[float(arr[sid]) for arr in feat]
                    if not np.isfinite(vector).all():continue
                    records.append(dict(point_id=point.point_id,classe=point.classe,
                         x=point.x,y=point.y,segment_id=f"{r0}:{c0}:{subindice}:{sid}",
                         **dict(zip(FEATURES,vector))))
                del sg,feat
            windows+=1;total_pixels+=h*w
            del rgb,multis,nir,red,ndvi,valor,bordas
            gc.collect()
            if windows%20==0 or windows==119:
                print(f"{modo}: {windows}/119 recortes | segmentos={total_segmentos}",flush=True)
    res=pd.DataFrame(records).sort_values("point_id").reset_index(drop=True)
    if res.point_id.duplicated().any():raise AssertionError("Referência em mais de um subsegmento.")
    res.to_csv(out/f"{modo}_referencias.csv",index=False)
    peak=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024
    manifest=dict(modo=modo,janelas=windows,pontos_encontrados=len(res),
         segmentos=total_segmentos,pixels=total_pixels,pico_rss_mib=peak,
         pico_incremental_mib=max(0,peak-baseline),baseline_mib=baseline,
         segundos=time.monotonic()-start,
         quickshift=dict(kernel_size=3,max_dist=5,ratio=.04,rng=42),
         cpu_ram_metodo="ru_maxrss do processo Linux; 119 janelas em sequencia",
         versoes=dict(python=platform.python_version(),numpy=np.__version__,
                      rasterio=rasterio.__version__,skimage=skimage.__version__))
    (out/f"{modo}_perfil.json").write_text(json.dumps(manifest,indent=2,ensure_ascii=False))
    print("PERFIL",json.dumps(manifest,ensure_ascii=False))
    return res

def modelos():
    from sklearn.ensemble import RandomForestClassifier,ExtraTreesClassifier,HistGradientBoostingClassifier
    from sklearn.linear_model import LogisticRegression
    from sklearn.neighbors import KNeighborsClassifier
    from sklearn.naive_bayes import GaussianNB
    from sklearn.dummy import DummyClassifier
    from sklearn.svm import SVC
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler
    return {
      "Random Forest":RandomForestClassifier(n_estimators=500,random_state=42,n_jobs=-1),
      "SVM RBF":make_pipeline(StandardScaler(),SVC(kernel="rbf",C=1,gamma="scale")),
      "Regressão logística":make_pipeline(StandardScaler(),LogisticRegression(max_iter=2000,random_state=42)),
      "KNN (7)":make_pipeline(StandardScaler(),KNeighborsClassifier(n_neighbors=7)),
      "Extra Trees":ExtraTreesClassifier(n_estimators=300,random_state=42,n_jobs=-1),
      "HistGradientBoosting":HistGradientBoostingClassifier(max_iter=100,learning_rate=.1,l2_regularization=1.,random_state=42),
      "Gaussian Naive Bayes":GaussianNB(),
      "Dummy":DummyClassifier(strategy="most_frequent")
    }

def comparar(area,out):
    from sklearn.model_selection import GroupShuffleSplit
    from sklearn.metrics import (accuracy_score,balanced_accuracy_score,f1_score,
                                 precision_score,recall_score,matthews_corrcoef)
    from scipy.spatial import cKDTree
    d={}
    for modo in MODOS:
        p=out/f"{modo}_referencias.csv"
        if not p.exists():raise FileNotFoundError(f"Execute primeiro modo {modo}: {p}")
        d[modo]=pd.read_csv(p).set_index("point_id")
        if d[modo].index.duplicated().any():raise ValueError("point_id duplicado")
    ids=sorted(set(d[MODOS[0]].index)&set(d[MODOS[1]].index))
    shared=pd.DataFrame({"point_id":ids})
    for m in MODOS:
        shared[m+"_segmento"]=d[m].loc[ids,"segment_id"].to_numpy()
    base=d[MODOS[0]].loc[ids].copy()
    other=d[MODOS[1]].loc[ids].copy()
    if not np.array_equal(base.classe.to_numpy(),other.classe.to_numpy()):
        raise ValueError("Classes divergentes no mesmo ponto.")
    # Agrupar refs que coincidem com o MESMO segmento em qualquer braço.
    parent={p:p for p in ids}
    def find(a):
        while parent[a]!=a:
            parent[a]=parent[parent[a]]
            a=parent[a]
        return a
    def union(a,b):
        ra,rb=find(a),find(b)
        if ra!=rb:parent[rb]=ra
    for modo in MODOS:
        for _,names in d[modo].loc[ids].groupby("segment_id").groups.items():
            group=list(names)
            for item in group[1:]:union(group[0],item)
    groups={}
    for p in ids:groups.setdefault(find(p),[]).append(p)
    keep=[];conflicts=0
    for group in groups.values():
        labels=set(base.loc[group,"classe"])
        if len(labels)!=1:
            conflicts+=1
            continue
        keep.append(sorted(group)[0])
    keep=sorted(keep)
    a=base.loc[keep].copy()
    b=other.loc[keep].copy()
    if len(keep)<30 or set(a.classe)!={"arvore","grama"}:
        raise RuntimeError("Dados comuns insuficientes após auditoria.")
    a.to_csv(out/"amostras_comuns_512.csv")
    b.to_csv(out/"amostras_comuns_256.csv")
    shared_after=pd.DataFrame(dict(point_id=keep,classe=a.classe.to_numpy(),
                                   x=a.x.to_numpy(),y=a.y.to_numpy()))
    shared_after.to_csv(out/"amostras_comuns.csv",index=False)
    xy=a[["x","y"]].to_numpy(float); y=a.classe.to_numpy()
    data={m:d[m].loc[keep][list(FEATURES)].to_numpy(float) for m in MODOS}
    from sklearn.model_selection import GroupShuffleSplit
    runs=[];splits=[]
    for block in (250,500):
        # Grade determinada pelo mesmo ponto de origem nos dois braços.
        gx=np.floor((xy[:,0]-xy[:,0].min())/block).astype(int)
        gy=np.floor((xy[:,1]-xy[:,1].min())/block).astype(int)
        geogroups=np.array([f"{x}_{yy}" for x,yy in zip(gx,gy)])
        if len(set(geogroups))<5:raise RuntimeError("Blocos insuficientes")
        for rep,(train,test) in enumerate(GroupShuffleSplit(
            n_splits=5,test_size=.2,random_state=2026).split(xy,y,geogroups),1):
            for embargo in (0,25):
                tr=train.copy()
                if embargo:
                    distances,_=cKDTree(xy[test]).query(xy[tr],k=1)
                    tr=tr[distances>embargo]
                if len(tr)<15 or len(test)<7 or len(set(y[tr]))!=2 or len(set(y[test]))!=2:
                    raise RuntimeError(f"Protocolo invalido {block}/{rep}/{embargo}")
                splits.append(dict(bloco_m=block,rodada=rep,embargo_pontos_m=embargo,
                                   n_treino=len(tr),n_teste=len(test),
                                   ids_treino=";".join(a.index[tr]),ids_teste=";".join(a.index[test])))
                for modo in MODOS:
                    x=data[modo]
                    for name,model in modelos().items():
                        model.fit(x[tr],y[tr])
                        pred=model.predict(x[test])
                        runs.append(dict(bloco_m=block,rodada=rep,embargo_pontos_m=embargo,
                            estrategia_segmentacao=modo,modelo=name,
                            n_treino=len(tr),n_teste=len(test),
                            f1_macro=f1_score(y[test],pred,average="macro",zero_division=0),
                            acuracia=accuracy_score(y[test],pred),
                            acuracia_balanceada=balanced_accuracy_score(y[test],pred),
                            f1_arvore=f1_score(y[test],pred,pos_label="arvore",zero_division=0),
                            precisao_arvore=precision_score(y[test],pred,pos_label="arvore",zero_division=0),
                            recall_arvore=recall_score(y[test],pred,pos_label="arvore",zero_division=0),
                            mcc=matthews_corrcoef(y[test],pred)))
    table=pd.DataFrame(runs)
    if len(table)!=320 or len(splits)!=20:raise AssertionError("E9 exige 320 avaliações e 20 protocolos")
    table.to_csv(out/"metricas_mesmos_pontos.csv",index=False)
    pd.DataFrame(splits).to_csv(out/"particoes_identicas.csv",index=False)
    summary=(table.query("embargo_pontos_m==25")
             .groupby(["bloco_m","estrategia_segmentacao","modelo"])["f1_macro"]
             .agg(["count","mean","std"]).reset_index())
    summary.to_csv(out/"resumo_oito_modelos.csv",index=False)
    manifesto=dict(total_referencias_iniciais=len(ids),referencias_comuns=len(keep),
       grupos_conflitantes_descartados=conflicts,protocolos=len(splits),avaliacoes=len(table),
       interpretacao="E9 compara apenas recortes; nao refaz Quickshift global/K-Means cluster 3.",
       estado="resultados calculados por esta implementacao; cotejar contra evidencias originais E9")
    (out/"manifesto_reexecucao.json").write_text(json.dumps(manifesto,ensure_ascii=False,indent=2))
    print("E9 reproduzível: 119 recortes, 8 algoritmos, 2 modos e 20 protocolos.")
    print("Números desta nova execução (não alterar resultados históricos sem confrontação):")
    print(summary.round(4).to_string(index=False))

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--area",type=Path,required=True)
    parser.add_argument("--out",type=Path,required=True)
    parser.add_argument("--mode",choices=(*MODOS,"comparar"),required=True)
    args=parser.parse_args()
    args.out.mkdir(parents=True,exist_ok=True)
    if args.mode=="comparar":comparar(args.area,args.out)
    else:segmentar(args.area,args.out,args.mode)
