#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""V3 -- calibracao dos coeficientes originais e novos modelos com Meta/WRI.

IMPORTANTE: alvos sao alturas MODELADAS por Meta/WRI, e NAO alturas de campo.
A variavel A e AREA DE SUPERPIXEL, nao area de copa individual comprovada.
Validacao espacial externa por blocos de 250/500m e embargo de 25m.
Selecao interna do modelo com blocos independentes, sem olhar os testes externos.
"""
import argparse
import json
import math
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.optimize import least_squares
from scipy.spatial import cKDTree
from sklearn.model_selection import GroupKFold
from pyproj import Transformer

MODELS=["constante","potencia","potencia_offset","raiz_offset","logaritmica",
        "linear","saturacao"]
TARGETS=["altura_meta_pixel_m","altura_meta_max_5m_m"]
OLD={"C1_potencial":(.5,.7),"C2_potencial":(.6,.8),"C3_potencial":(2.5,.4)}

def model(name,area,params):
    A=np.asarray(area,dtype=float)
    p=np.asarray(params,dtype=float)
    if name=="constante": out=np.full_like(A,p[0])
    elif name=="potencia": out=p[0]*np.power(A,p[1])
    elif name=="potencia_offset":out=p[0]+p[1]*np.power(A,p[2])
    elif name=="raiz_offset":out=p[0]+p[1]*np.sqrt(A)
    elif name=="logaritmica":out=p[0]+p[1]*np.log1p(A)
    elif name=="linear":out=p[0]+p[1]*A
    elif name=="saturacao":out=p[0]+p[1]*(1-np.exp(-A/p[2]))
    else:raise ValueError("modelo nao reconhecido: "+name)
    return np.clip(out,0,40)

def formula(name,p):
    z=lambda n:f"{float(n):.5g}"
    if name=="constante":return "H_modelada="+z(p[0])
    if name=="potencia":return "H_modelada="+z(p[0])+" * A^"+z(p[1])
    if name=="potencia_offset":return "H_modelada="+z(p[0])+" + "+z(p[1])+" * A^"+z(p[2])
    if name=="raiz_offset":return "H_modelada="+z(p[0])+" + "+z(p[1])+" * sqrt(A)"
    if name=="logaritmica":return "H_modelada="+z(p[0])+" + "+z(p[1])+" * ln(1+A)"
    if name=="linear":return "H_modelada="+z(p[0])+" + "+z(p[1])+" * A"
    if name=="saturacao":return "H_modelada="+z(p[0])+" + "+z(p[1])+" * (1-exp(-A/"+z(p[2])+"))"
    return "?"

def fit(name,A,y):
    A=np.asarray(A,float);y=np.asarray(y,float)
    ok=np.isfinite(A)&np.isfinite(y)&(A>0)
    A=A[ok];y=y[ok]
    if len(y)<12:raise ValueError("Menos de 12 observacoes para ajustar")
    if name=="constante":return np.array([max(0,float(np.median(y)))])
    med=float(np.median(y))
    if name=="potencia":
        attempts=[([min(40,med/np.median(A)**b),b],[0,0],[40,1.5])
                  for b in [.1,.35,.7,1.]]
    elif name=="potencia_offset":
        attempts=[([max(0,med*.4),min(40,med*.6/np.median(A)**b),b],
                   [0,0,0],[40,40,1.5]) for b in [.2,.5,1.]]
    elif name=="raiz_offset":attempts=[([max(0,med*.5),min(40,med*.5/np.sqrt(np.median(A)))],[0,0],[40,40])]
    elif name=="logaritmica":attempts=[([max(0,med*.5),min(40,med*.5/np.log1p(np.median(A)))],[0,0],[40,40])]
    elif name=="linear":attempts=[([max(0,med*.5),min(40,med*.5/np.median(A))],[0,0],[40,40])]
    elif name=="saturacao":attempts=[([max(0,med*.3),min(40,med*.7),v],[0,0,5],[40,40,2500]) for v in [50,150,500]]
    else:raise ValueError(name)
    best=None
    for init,lo,hi in attempts:
        try:
            r=least_squares(lambda p:model(name,A,p)-y,np.array(init),
              bounds=(lo,hi),loss="soft_l1",f_scale=3,
              max_nfev=350,ftol=1e-6,xtol=1e-6)
            err=float(np.mean(abs(model(name,A,r.x)-y)))
            if np.isfinite(err) and (best is None or err<best[0]):best=(err,r.x)
        except (ValueError,RuntimeError,FloatingPointError):
            pass
    if best is None:raise RuntimeError("Falha ajuste "+name)
    return best[1]

def group_ids(x,y,side):
    # Grades espaciais FIXAS para comparacoes entre recortes e folds;
    # nao sao recalculadas dentro de treino/teste.
    gx=np.floor(x/side).astype(int)
    gy=np.floor(y/side).astype(int)
    return np.array([f"{a}_{b}" for a,b in zip(gx,gy)])

def folds(ind,groups,coords,partitions=5,embargo=25):
    subg=groups[ind]
    n=min(partitions,len(np.unique(subg)))
    if n<3:return []
    it=GroupKFold(n_splits=n)
    out=[]
    for tr,te in it.split(ind,groups=subg):
        tra=ind[tr];tes=ind[te]
        dist,_=cKDTree(coords[tes]).query(coords[tra],k=1)
        tra=tra[dist>=embargo]
        if len(tra)<12 or len(tes)<2:continue
        out.append((tra,tes))
    return out

def metric(y,p):
    if len(y)==0:return {"n":0}
    residual=np.asarray(p)-np.asarray(y)
    return {"n":int(len(y)),"mae_m":float(np.mean(abs(residual))),
      "rmse_m":float(np.sqrt(np.mean(residual**2))),
      "vies_m":float(np.mean(residual)),
      "mediana_residual_abs_m":float(np.median(abs(residual)))}

def inner_choose(indices,groups,coords,A,y):
    inner=folds(indices,groups,coords,partitions=3,embargo=25)
    if len(inner)<2:return "constante",{"constante":float("nan")} # fallback
    scores={}
    for n in MODELS:
        ys=[];ps=[]
        for tr,te in inner:
            try:
                param=fit(n,A[tr],y[tr])
                pred=model(n,A[te],param)
                ys.extend(y[te]);ps.extend(pred)
            except (ValueError,RuntimeError):
                pass
        scores[n]=float(np.mean(abs(np.asarray(ys)-np.asarray(ps)))) if ys else float("inf")
    eligible=[n for n in MODELS if np.isfinite(scores[n])]
    if not eligible:return "constante",scores
    best=min(eligible,key=lambda n:(scores[n],MODELS.index(n)))
    # Requer melhoria >=5% em relacao ao modelo constante para preferir
    # uma formula dependente de area, reduzindo a escolha de ruido.
    if best!="constante" and scores[best]>0.95*scores["constante"]:
        best="constante"
    return best,scores

def experiment(data,block,target):
    A=data.area_superpixel_m2.to_numpy(float)
    y=data[target].to_numpy(float)
    # Para alvo principal, preservamos os zeros e nao filtramos com base
    # nas alturas do proprio conjunto de teste.
    wgs=Transformer.from_crs("EPSG:4326","EPSG:31982",always_xy=True)
    xx,yy=wgs.transform(data.longitude.to_numpy(float),data.latitude.to_numpy(float))
    xy=np.column_stack([xx,yy])
    groups=group_ids(xx,yy,block)
    idx=np.where(np.isfinite(y))[0]
    outer=folds(idx,groups,xy,partitions=5,embargo=25)
    if len(outer)<3:
        raise RuntimeError(f"Validacao espacial inviavel: block={block}, alvo={target}, folds={len(outer)}")
    all_predictions={name:np.full(len(data),np.nan) for name in MODELS+["selecao_aninhada"]}
    selected=[]
    details=[]
    for f,(train,test) in enumerate(outer,1):
        winner,inner_scores=inner_choose(train,groups,xy,A,y)
        selected.append(winner)
        for name in MODELS:
            p=fit(name,A[train],y[train])
            pred=model(name,A[test],p)
            all_predictions[name][test]=pred
        pred=all_predictions[winner][test]
        all_predictions["selecao_aninhada"][test]=pred
        details.append({"alvo":target,"bloco_m":block,"fold":f,"treino_n":len(train),
          "teste_n":len(test),"melhor_interno":winner,
          "mae_teste_selecao_m":metric(y[test],pred)["mae_m"],
          "pontuacoes_internas":json.dumps(inner_scores,allow_nan=True)})
    report=[]
    for name,pred in all_predictions.items():
        valid=np.isfinite(pred)&np.isfinite(y)
        m=metric(y[valid],pred[valid])
        m.update({"alvo_meta":target,"bloco_m":block,"modelo":name,"n_folds":len(outer),
          "pct_teste_efetivo":float(np.mean(valid))*100,
          "observacao":"Erro versus referencia MODELADA Meta/WRI; nao erro de campo."})
        report.append(m)
    return report,details,all_predictions,selected,groups,idx

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--csv",type=Path,required=True)
    ap.add_argument("--out",type=Path,required=True)
    args=ap.parse_args()
    df=pd.read_csv(args.csv,encoding="utf-8-sig").sort_values("ponto_id")
    required={"ponto_id","area_superpixel_m2","latitude","longitude"}|set(TARGETS)
    if len(df)!=257 or df.ponto_id.nunique()!=257 or not required.issubset(df.columns):
        raise ValueError("A entrada precisa dos 257 pontos originais e das colunas de meta e area.")
    args.out.mkdir(parents=True,exist_ok=True)
    A=df.area_superpixel_m2.to_numpy(float)
    cv=[];foldrecords=[]
    preds=df[["ponto_id","area_superpixel_m2","latitude","longitude"]].copy()
    info={}
    for target in TARGETS:
        y=df[target].to_numpy(float)
        if not np.isfinite(y).all():raise ValueError("Target incompleto: "+target)
        info[target]={}
        for block in [250,500]:
            rows,detail,oop,selected,groups,idx=experiment(df,block,target)
            cv.extend(rows);foldrecords.extend(detail)
            label=("pixel" if target==TARGETS[0] else "raio5")+"_"+str(block)
            for key,p in oop.items():preds[label+"_"+key]=p
            info[target][str(block)]={"folds":len(selected),
              "selecionados":selected,
              "n_grupos":int(len(np.unique(groups)))}
        # Ajuste FINAL em todos os 257 pontos (somente para aplicar
        # posteriormente). Sua estimativa de erro vem dos folds OOF,
        # NAO da proximidade medida nesses mesmos 257 dados usados no fit.
        info[target]["formula_final"]={}
        for name in MODELS:
            params=fit(name,A,y)
            info[target]["formula_final"][name]={"params":[float(z) for z in params],
                   "formula":formula(name,params)}
            preds[("pixel" if target==TARGETS[0] else "raio5")+"_ajuste_total_"+name]=model(name,A,params)
    dfcv=pd.DataFrame(cv)
    dfcv.to_csv(args.out/"v3_meta_calibracao_validacao_espacial.csv",index=False,encoding="utf-8-sig")
    pd.DataFrame(foldrecords).to_csv(args.out/"v3_meta_calibracao_folds.csv",index=False,encoding="utf-8-sig")
    preds.to_csv(args.out/"v3_meta_calibracao_257_pontos.csv",index=False,encoding="utf-8-sig")
    old=[]
    for key,(a,b) in OLD.items():
        for target in TARGETS:
            yy=df[target].to_numpy(float)
            p=a*np.power(A,b)
            m=metric(yy,p)
            m.update({"nome":key,"alvo":target,"coef_a":a,"coef_b":b,
                  "metodo":"Coeficientes originais fixos, SEM validacao de ajuste"})
            old.append(m)
    pd.DataFrame(old).to_csv(args.out/"v3_meta_calibracao_coeficientes_originais.csv",index=False,encoding="utf-8-sig")
    base={}
    for target in TARGETS:
        tmp=dfcv[(dfcv.alvo_meta==target)&(dfcv.bloco_m==250)]
        winner=tmp.sort_values("mae_m").iloc[0]
        base[target]={"menor_mae_exploratorio":winner.modelo,
          "menor_mae_exploratorio_m":float(winner.mae_m),
          "mae_constante":float(tmp.loc[tmp.modelo=="constante","mae_m"].iloc[0]),
          "mae_selecao_aninhada":float(tmp.loc[tmp.modelo=="selecao_aninhada","mae_m"].iloc[0])}
    info["resumo"]=base
    info["ressalva"]="Criterio mede concordancia com modelo Meta/WRI, NAO acuracia de altura medida."
    info["modelo_selecionado_em_novo_local"]="Requer teste externo independente antes de afirmar generalizacao"
    (args.out/"v3_meta_calibracao_parametros_e_limites.json").write_text(
        json.dumps(info,ensure_ascii=False,indent=2),encoding="utf-8")
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        fig,ax=plt.subplots(figsize=(9,5.2))
        comp=dfcv[(dfcv.bloco_m==250)&(dfcv.alvo_meta==TARGETS[1])].sort_values("mae_m")
        ax.barh(comp.modelo.iloc[::-1],comp.mae_m.iloc[::-1])
        ax.set(xlabel="MAE vs. altura MODELADA Meta (m), validacao espacial 250m",
          title="Area1 — modelos calibrados e referencia constante")
        fig.tight_layout();fig.savefig(args.out/"v3_meta_calibracao_mae_250m.png",dpi=160);plt.close(fig)
    except ImportError:
        pass
    print(json.dumps(info["resumo"],ensure_ascii=False,indent=2))
    print("Arquivos produzidos: validacao, folds, 257 pontos, parametros, originais, grafico.")

if __name__=="__main__":
    main()
