# coding: utf-8
"""E10: oito classificadores sobre o Quickshift GLOBAL original e referências comuns à V2.
Execute em uma sessão Colab na qual df e gdf_arvore_seg_filter já foram gerados
pelo pipeline original. Dados: somente arquivos e checkpoints derivados de Area1.
"""
from pathlib import Path
from datetime import datetime, timezone
import json, warnings, platform
import numpy as np
import pandas as pd
import geopandas as gpd
import rasterio
from scipy.spatial import cKDTree
from sklearn.ensemble import RandomForestClassifier, ExtraTreesClassifier, HistGradientBoostingClassifier
from sklearn.model_selection import train_test_split, GroupShuffleSplit
from sklearn.svm import SVC
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.neighbors import KNeighborsClassifier
from sklearn.naive_bayes import GaussianNB
from sklearn.dummy import DummyClassifier
from sklearn.metrics import (accuracy_score, balanced_accuracy_score, f1_score,
    precision_score, recall_score, matthews_corrcoef)
import sklearn, skimage

AREA=Path(globals().get("AREA_E10","/content/drive/MyDrive/Projetos/Segmentacao_Breno/Area1"))
OUT=Path(globals().get("OUT_E10","/content/drive/MyDrive/Projetos/Segmentacao_Breno/outputs/e10_original_vs_v2"))
TILES=Path(globals().get("TILES_E10","/content/drive/MyDrive/Projetos/Segmentacao_Breno/outputs/v2_progressivo_256/tiles"))
COLS=["mean_intensity","mean_edges","mean_ndvi"]
OUT.mkdir(parents=True,exist_ok=True)
for name in ["AOI_RGB_NEW.tif","Arvores.gpkg","Grama.gpkg"]:
    if not (AREA/name).exists(): raise FileNotFoundError(AREA/name)
if "df" not in globals() or "gdf_arvore_seg_filter" not in globals():
    raise RuntimeError("Execute primeiro Quickshift GLOBAL, K-Means K=6, cluster 3 e extração de atributos do notebook original.")
raw_df=globals()["df"]
geo=globals()["gdf_arvore_seg_filter"]
if not isinstance(raw_df,pd.DataFrame) or not isinstance(geo,gpd.GeoDataFrame):
    raise TypeError("df ou gdf_arvore_seg_filter com tipo incorreto.")
if len(raw_df)!=len(geo): raise ValueError("Linhas de df e da junção espacial não correspondem.")
if not set(COLS+["classe"]).issubset(raw_df.columns): raise ValueError("Tabela df não é a tabela final original.")
if not {"Classe","index_right"}.issubset(geo.columns): raise ValueError("Junção espacial original sem identificador da referência.")
if geo.crs is None: raise ValueError("CRS de segmentos ausente.")
labels_df=raw_df.classe.astype(str).str.strip().str.lower().to_numpy()
labels_geo=geo.Classe.astype(str).str.strip().str.lower().to_numpy()
if not np.array_equal(labels_df,labels_geo): raise ValueError("Ordem de rótulos entre df e sjoin divergente.")
if set(labels_df)!={"arvore","grama"}: raise ValueError("Classes inesperadas no método original.")

reference=[]
for filename,cls in (("Arvores.gpkg","arvore"),("Grama.gpkg","grama")):
    g=gpd.read_file(AREA/filename).to_crs(geo.crs)
    if not g.geometry.geom_type.eq("Point").all(): raise ValueError("Referências não são pontos.")
    for i,p in g.geometry.items():
        reference.append({"ref_id":f"{cls}:{i}","classe":cls,"x":float(p.x),"y":float(p.y)})
refs=pd.DataFrame(reference)
if refs.ref_id.duplicated().any(): raise ValueError("Referências com IDs repetidos.")
pairs=raw_df[COLS].reset_index(drop=True).copy()
pairs["classe"]=labels_df
pairs["segmento_id"]=geo.index.astype(str).to_numpy()
if geo.index_right.isna().any(): raise ValueError("index_right sem referência.")
pairs["ref_id"]=[f"{c}:{int(i)}" for c,i in zip(pairs.classe,geo.index_right)]
pairs=pairs.merge(refs[["ref_id","x","y"]],on="ref_id",validate="many_to_one")
for col in COLS: pairs[col]=pd.to_numeric(pairs[col],errors="coerce")
pairs=pairs.replace([np.inf,-np.inf],np.nan).dropna(subset=COLS)
pairs.to_csv(OUT/"pares_originais.csv",index=False)

def models():
    return {
        "Random Forest":RandomForestClassifier(n_estimators=500,random_state=42,n_jobs=-1),
        "SVM RBF":make_pipeline(StandardScaler(),SVC(C=1,kernel="rbf",gamma="scale")),
        "Regressão logística":make_pipeline(StandardScaler(),LogisticRegression(max_iter=2000,random_state=42)),
        "KNN (7)":make_pipeline(StandardScaler(),KNeighborsClassifier(n_neighbors=7)),
        "Extra Trees":ExtraTreesClassifier(n_estimators=300,random_state=42,n_jobs=-1),
        "HistGradientBoosting":HistGradientBoostingClassifier(max_iter=100,learning_rate=0.1,l2_regularization=1.0,random_state=42),
        "Gaussian Naive Bayes":GaussianNB(),
        "Dummy":DummyClassifier(strategy="most_frequent")
    }

def metrics(y,p):
    return {"acuracia":accuracy_score(y,p),"acuracia_balanceada":balanced_accuracy_score(y,p),
            "f1_macro":f1_score(y,p,average="macro",zero_division=0),
            "f1_arvore":f1_score(y,p,pos_label="arvore",zero_division=0),
            "precisao_arvore":precision_score(y,p,pos_label="arvore",zero_division=0),
            "recall_arvore":recall_score(y,p,pos_label="arvore",zero_division=0),
            "mcc":matthews_corrcoef(y,p)}

def score(base,tr,te,pipeline,protocol,roundno,block=0,check=True):
    if len(tr)<15 or len(te)<7 or len(set(base.iloc[tr].classe))<2 or len(set(base.iloc[te].classe))<2:
        return []
    if check and set(base.iloc[tr].segmento_id)&set(base.iloc[te].segmento_id):
        raise AssertionError("Mesmo segmento no treino e no teste.")
    x=base[COLS].to_numpy(float); y=base.classe.to_numpy()
    records=[]
    for name,model in models().items():
        model.fit(x[tr],y[tr])
        predicted=model.predict(x[te])
        records.append({"pipeline":pipeline,"protocolo":protocol,"rodada":roundno,
                        "bloco_m":block,"embargo_pontos_m":25 if block else 0,
                        "modelo":name,"n_treino":len(tr),"n_teste":len(te),**metrics(y[te],predicted)})
    return records

# Benchmark histórico por PARES (não deduplicado), mesmo split e RF original.
tr,te=train_test_split(np.arange(len(pairs)),test_size=.2,random_state=42)
historico=score(pairs,tr,te,"original_pares","historico_80_20",1,check=False)
pd.DataFrame(historico).to_csv(OUT/"historico_oito_modelos.csv",index=False)
rf=[z for z in historico if z["modelo"]=="Random Forest"][0]
if abs(rf["acuracia"]-0.87)>0.015:
    warnings.warn("Acurácia reproduzida difere de 0,87 histórico: checar versões, rótulos, segmentos e parâmetros.")

def dedup(data):
    d=data.copy()
    conflicts=set(d.groupby("segmento_id").classe.nunique().loc[lambda x:x>1].index)
    d=(d.loc[~d.segmento_id.isin(conflicts)]
       .sort_values(["ref_id","segmento_id"]).drop_duplicates("ref_id")
       .sort_values(["segmento_id","ref_id"]).drop_duplicates("segmento_id")
       .sort_values("ref_id").reset_index(drop=True))
    return d,len(conflicts)

orig,n_conflict=dedup(pairs)
if len(orig)<20: raise ValueError("Poucos segmentos após deduplicação.")
with rasterio.open(AREA/"AOI_RGB_NEW.tif") as raster:
    width,height,transform,crs,bounds=raster.width,raster.height,raster.transform,raster.crs,raster.bounds

# A V2 já deve ter gravado checkpoints progressivos: ler os mesmos segmentos 256,
# sem alegar que equivalem ao Quickshift global.
v2_rows=[]; absent=0; missing=0
if TILES.exists():
    reg=refs.copy()
    ref_geo=gpd.GeoDataFrame(reg,geometry=gpd.points_from_xy(reg.x,reg.y),crs=geo.crs).to_crs(crs)
    if crs!=geo.crs:
        back=ref_geo.to_crs(geo.crs).geometry
    else: back=ref_geo.geometry
    buckets={}
    per_row=(width+255)//256
    for i,(row,p) in enumerate(zip(reg.itertuples(index=False),ref_geo.geometry)):
        rr,cc=rasterio.transform.rowcol(transform,p.x,p.y)
        if not(0<=rr<height and 0<=cc<width): continue
        tile=(rr//256)*per_row+cc//256
        buckets.setdefault(tile,[]).append((row.ref_id,row.classe,int(rr%256),int(cc%256)))
    for tile,items in buckets.items():
        path=TILES/f"tile_{tile:04d}.npz"
        if not path.exists():
            if not (TILES/f"tile_{tile:04d}.skip").exists():missing+=1
            continue
        with np.load(path) as item:
            seg=item["seg"]; inside=item["dentro"]; f3=item["f3"]
            for key,cls,r,c in items:
                if r>=seg.shape[0] or c>=seg.shape[1] or not inside[r,c]:continue
                sid=int(seg[r,c]); vector=f3[sid]
                if not np.isfinite(vector).all():continue
                v2_rows.append({"ref_id":key,"classe":cls,"segmento_id":f"t{tile}:{sid}",
                                "mean_intensity":float(vector[0]),"mean_edges":float(vector[1]),
                                "mean_ndvi":float(vector[2])})
else: absent=1
if v2_rows:
    v2_raw=pd.DataFrame(v2_rows).merge(refs[["ref_id","x","y"]],on="ref_id",validate="one_to_one")
    v2,n_v2_conflicts=dedup(v2_raw)
else:
    v2=pd.DataFrame(); n_v2_conflicts=0

audit={"date_utc":datetime.now(timezone.utc).isoformat(),"area1_refs":len(refs),
       "historic_pairs":len(pairs),"historic_random_forest_accuracy":rf["acuracia"],
       "historic_rf_n_test":rf["n_teste"],"original_unique_segments":len(orig),"original_references_with_candidates":int(pairs.ref_id.nunique()),
       "original_reference_coverage":float(pairs.ref_id.nunique()/len(refs)),
       "original_conflicting_segment_ids":n_conflict,"v2_checkpoint_status":"ausentes" if absent else
        ("parcial" if missing else "presente"),"v2_missing_reference_tiles":missing,
       "v2_unique_segments":len(v2),"v2_reference_count":len(v2_rows),"v2_conflicting_segment_ids":n_v2_conflicts,
       "global_quickshift_label_mode":globals().get("MODO_SEGMENTOS_E10","nao_registrado"),
       "python":platform.python_version(),"numpy":np.__version__,"sklearn":sklearn.__version__,
       "skimage":skimage.__version__,"rasterio":rasterio.__version__}
# Cobertura calculada antes da modelagem: nao confundir taxa de cobertura e F1.
coverage=[]
for cls in ("arvore","grama"):
    total=int((refs.classe==cls).sum())
    choices=[("original_pares",pairs),("original_unicos",orig),
             ("v2_checkpoints",pd.DataFrame(v2_rows) if v2_rows else pd.DataFrame()),
             ("v2_unicos",v2)]
    for stage,data in choices:
        count=int(data.loc[data.classe==cls,"ref_id"].nunique()) if not data.empty else 0
        coverage.append({"classe":cls,"pipeline":stage,"referencias_total":total,
                         "referencias_cobertas":count,"fracao_cobertura":count/total})
pd.DataFrame(coverage).to_csv(OUT/"cobertura_por_classe.csv",index=False)
results=[]
tr,te=train_test_split(np.arange(len(orig)),test_size=.2,random_state=42)
results+=score(orig,tr,te,"original_global_unico","aleatorio_80_20",1)
if not v2.empty:
    common=sorted(set(orig.ref_id)&set(v2.ref_id))
    a=orig.set_index("ref_id").loc[common].reset_index()
    b=v2.set_index("ref_id").loc[common].reset_index()
    audit["common_references_after_dedup"]=len(common)
    a.to_csv(OUT/"referencias_comuns_original.csv",index=False)
    b.to_csv(OUT/"referencias_comuns_v2.csv",index=False)
    if not np.array_equal(a.classe.to_numpy(),b.classe.to_numpy()):
        raise ValueError("Rótulo divergente entre pipelines.")
    if len(common)>=30 and a.classe.nunique()==2:
        partitions=[]
        tr,te=train_test_split(np.arange(len(common)),test_size=.2,random_state=42)
        partitions.append(("aleatorio_80_20",0,1,tr,te))
        xy=a[["x","y"]].to_numpy(float)
        for block in (250,500):
            groupx=np.floor((xy[:,0]-bounds.left)/block).astype(int)
            groupy=np.floor((xy[:,1]-bounds.bottom)/block).astype(int)
            groups=np.array([f"{x}:{y}" for x,y in zip(groupx,groupy)])
            if len(np.unique(groups))<5:continue
            for rep,(tr,te) in enumerate(GroupShuffleSplit(n_splits=5,test_size=.2,
                                          random_state=2026).split(xy,a.classe,groups),1):
                partitions.append(("espacial",block,rep,tr,te))
        kept=[]
        for protocol,block,rep,tr,te in partitions:
            if block:
                dists,_=cKDTree(xy[te]).query(xy[tr],k=1)
                tr=tr[dists>25]
            # Mesmos índices de treino e teste; remover potenciais segmentos
            # transversais às partições em AMBOS os pipelines.
            idsa=set(a.iloc[te].segmento_id);idsb=set(b.iloc[te].segmento_id)
            tr=np.array([i for i in tr if a.iloc[i].segmento_id not in idsa
                         and b.iloc[i].segmento_id not in idsb],dtype=int)
            if len(tr)<15 or len(te)<7 or a.iloc[tr].classe.nunique()!=2 or a.iloc[te].classe.nunique()!=2:
                continue
            kept.append({"protocolo":protocol,"bloco_m":block,"rodada":rep,
                         "n_treino":len(tr),"n_teste":len(te),
                         "treino_ids":";".join(a.iloc[tr].ref_id),
                         "teste_ids":";".join(a.iloc[te].ref_id)})
            results+=score(a,tr,te,"original_global_comum",protocol,rep,block)
            results+=score(b,tr,te,"v2_256_comum",protocol,rep,block)
        pd.DataFrame(kept).to_csv(OUT/"folds_comuns.csv",index=False)
    else:
        audit["common_comparison"]="insuficiente: menos de 30 referências ou classe única"

if results:
    table=pd.DataFrame(results)
    table.to_csv(OUT/"metricas.csv",index=False)
    summary=table.groupby(["pipeline","protocolo","bloco_m","modelo"],as_index=False).agg(
        n_rodadas=("f1_macro","count"),f1_macro_medio=("f1_macro","mean"),
        acuracia_media=("acuracia","mean"),acuracia_balanceada_media=("acuracia_balanceada","mean"))
    summary.to_csv(OUT/"resumo.csv",index=False)
    print(summary.round(4).to_string(index=False))
    if {"original_global_comum","v2_256_comum"}<=set(table.pipeline):
        pivot=table[table.pipeline.isin(["original_global_comum","v2_256_comum"])].pivot(
            index=["protocolo","bloco_m","rodada","modelo"],columns="pipeline",values="f1_macro")
        delta=pivot.dropna().assign(delta_v2_menos_original=lambda t:t.v2_256_comum-t.original_global_comum)
        delta.to_csv(OUT/"deltas_f1_pareados.csv")

(OUT/"manifesto.json").write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding="utf-8")
print("E10: arquivos efetivamente calculados em:",OUT)
print("ATENÇÃO: no experimento pareado, o embargo de 25 m é ENTRE PONTOS, não entre polígonos.")
print("O resultado histórico por pares NÃO equivale ao conjunto deduplicado ou ao E3c publicado.")
