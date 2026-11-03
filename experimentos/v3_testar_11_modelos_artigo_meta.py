#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""V3: as 11 familias de regressao do artigo, ADAPTADAS a altura H=f(D_eq).

Articulo Chatziathanasiou et al. Land 2024, 13, 1579; correcao 2026,15,473.
O artigo ORIGINAL regressa CW = f(H) com largura de copa REAL.
Esta bateria inverte o PROBLEMA EMPIRICO, nao as equacoes originais:
ajusta H_Meta = g(D_eq) com as mesmas 11 FAMILIAS DE CURVAS.
D_eq = 2 sqrt(A_superpixel/pi) e SOMENTE largura circular equivalente de
SUPERPIXEL QUICKSHIFT; NAO eh diametro de copa medido.
Coeficientes obtidos a partir dos pontos Area1, nao copiados do artigo.
NENHUMA altura Meta eh verdade de campo. Resultados expressam concordancia
com um mapa de altura MODELADA e nao validacao de altura de arvores.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from collections import Counter
import numpy as np
import pandas as pd
from scipy.optimize import least_squares
from scipy.spatial import cKDTree
from pyproj import Transformer
from sklearn.model_selection import GroupKFold

# 10 m eh a escala numerica fixa para ajuste estavel; x = D_eq/10.
# No modelo logistico, u=40 m eh uma suposicao FIXA, nao parametro do artigo.
MODEL_NAMES=[
 "Linear", "Logaritmico", "Inverso", "Quadratico", "Cubico", "Potencial",
 "Composto", "Curva_S", "Logistico", "Crescimento", "Exponencial",
]
ARTICLE="https://doi.org/10.3390/land13101579"
CORRECTION="https://doi.org/10.3390/land15030473"
TARGETS={"pixel":"altura_meta_pixel_m","raio5":"altura_meta_max_5m_m"}
U=40.0

def predict(name,x,p):
    # Clipping numerico na escala 0..40m, dentro de todos os fits e
    # forecasts para nao criar alturas negativas. NAO equivale a campo.
    x=np.asarray(x,float);p=np.asarray(p,float)
    if name=="Linear":v=p[0]+p[1]*x
    elif name=="Logaritmico":v=p[0]+p[1]*np.log(x)
    elif name=="Inverso":v=p[0]-p[1]/x
    elif name=="Quadratico":v=p[0]+p[1]*x+p[2]*x*x
    elif name=="Cubico":v=p[0]+p[1]*x+p[2]*x*x+p[3]*x*x*x
    elif name=="Potencial":v=p[0]*x**p[1]
    elif name=="Composto":v=p[0]*np.exp(np.log(p[1])*x)
    elif name=="Curva_S":v=np.exp(np.clip(p[0]-p[1]/x,-20,5))
    elif name=="Logistico":v=1/(1/U+p[0]*np.exp(np.log(p[1])*x))
    elif name=="Crescimento":v=np.exp(np.clip(p[0]+p[1]*x,-20,5))
    elif name=="Exponencial":v=p[0]*np.exp(np.clip(p[1]*x,-20,5))
    else:raise ValueError(name)
    return np.clip(v,0,U)

def setup(name,mean_h):
    # Restricoes monotonicas nao decrescentes; excluem modelos
    # matematicamente possiveis mas com altura decrescente com a copa.
    h=max(0.1,float(mean_h))
    if name=="Linear":return [h/2,1.], [0,0], [40,30]
    if name=="Logaritmico":return [h,1.], [0,0], [40,30]
    if name=="Inverso":return [h,1.], [0,0], [40,30]
    if name=="Quadratico":return [h/2,1.,.1], [0,0,0], [40,30,30]
    if name=="Cubico":return [h/2,1.,.1,.01],[0,0,0,0],[40,30,30,30]
    if name=="Potencial":return [h,.2],[0,0],[40,2.5]
    if name=="Composto":return [h,1.02],[0,1],[40,4]
    if name=="Curva_S":return [float(np.log(h)),.2],[-9,0],[4,20]
    if name=="Logistico":return [.1,.8],[0,0.05],[100,1]
    if name=="Crescimento":return [float(np.log(h)),.05],[-9,0],[4,3]
    if name=="Exponencial":return [h,.05],[0,0],[40,3]
    raise ValueError(name)

def fit(name,x,y):
    if name=="Controle_constante":
        return np.array([float(np.median(y))])
    p0,lo,hi=setup(name,np.median(y))
    p0=np.clip(np.asarray(p0,float),np.asarray(lo)+1e-7,np.asarray(hi)-1e-7)
    try:
        opt=least_squares(lambda p:predict(name,x,p)-y,p0,bounds=(lo,hi),
            loss="soft_l1",f_scale=3,max_nfev=150)
    except (ValueError,FloatingPointError) as ex:
        raise RuntimeError(f"Falha na familia {name}: {ex}") from ex
    if not np.isfinite(opt.x).all():raise RuntimeError(name+" params nao finitos")
    return opt.x

def forecast(name,x,p):
    if name=="Controle_constante":return np.full(x.shape,p[0],float)
    return predict(name,x,p)

def metric(y,p):
    d=np.asarray(p)-np.asarray(y)
    return {"n":int(len(y)),"mae_vs_meta_m":float(np.mean(abs(d))),
       "rmse_vs_meta_m":float(np.sqrt(np.mean(d*d))),
       "vies_m":float(np.mean(d)),
       "mediana_erro_abs_m":float(np.median(abs(d))),
       "ate_2m_pct":float(np.mean(abs(d)<=2)*100),
       "ate_5m_pct":float(np.mean(abs(d)<=5)*100)}

def splits(ids,gr,xy,k=5,embargo=25):
    ng=len(np.unique(gr[ids]))
    if ng<k:raise RuntimeError(f"Grupos espaciais insuficientes: {ng}")
    out=[]
    for itr,ite in GroupKFold(n_splits=k).split(ids,groups=gr[ids]):
        tr,te=ids[itr],ids[ite]
        dis,_=cKDTree(xy[te]).query(xy[tr])
        tr=tr[dis>=embargo]
        if len(tr)<15 or len(te)<3:raise RuntimeError("Fold invalido apos embargo")
        out.append((tr,te))
    return out

def choose_inside(train,gr,xy,x,y):
    inner=splits(train,gr,xy,k=3,embargo=25)
    scores={}
    for n in MODEL_NAMES+["Controle_constante"]:
        ys=[];preds=[]
        for t,v in inner:
            par=fit(n,x[t],y[t])
            ys.extend(y[v]);preds.extend(forecast(n,x[v],par))
        scores[n]=float(np.mean(abs(np.array(ys)-np.array(preds))))
    # Do not pick a curve unless its MAE improves >=5% over constant.
    constant=scores["Controle_constante"]
    winners=sorted(MODEL_NAMES,key=lambda z:(scores[z],MODEL_NAMES.index(z)))
    pick=winners[0] if scores[winners[0]] < .95*constant else "Controle_constante"
    return pick,scores

def evaluation(df,block,target):
    A=df.area_superpixel_m2.to_numpy(float)
    D=2*np.sqrt(A/np.pi)
    x=D/10.0
    y=df[target].to_numpy(float)
    xx,yy=Transformer.from_crs("EPSG:4326","EPSG:31982",always_xy=True).transform(
        df.longitude.to_numpy(float),df.latitude.to_numpy(float))
    xy=np.column_stack((xx,yy))
    gr=np.array([f"{int(np.floor(a/block))}_{int(np.floor(b/block))}" for a,b in xy])
    ids=np.arange(len(df))
    outer=splits(ids,gr,xy,k=5,embargo=25)
    names=MODEL_NAMES+["Controle_constante","Selecao_aninhada"]
    pred={n:np.full(len(df),np.nan) for n in names}
    rows=[]
    for fi,(tr,te) in enumerate(outer,1):
        selected,cv=choose_inside(tr,gr,xy,x,y)
        vals={}
        for n in MODEL_NAMES+["Controle_constante"]:
            prm=fit(n,x[tr],y[tr])
            pred[n][te]=forecast(n,x[te],prm)
        pred["Selecao_aninhada"][te]=pred[selected][te]
        rows.append({"alvo":target,"bloco_m":block,"fold":fi,
            "treino_n":len(tr),"teste_n":len(te),"modelo_escolhido_interno":selected,
            "resultados_internos":json.dumps(cv,ensure_ascii=False)})
        print("fold",block,target,fi,"inner selected",selected,flush=True)
    summary=[]
    for n in names:
        valid=np.isfinite(pred[n])
        if valid.sum()!=len(df):raise RuntimeError(f"{n}: previsoes OOF faltantes")
        record=dict(modelo=n,alvo=target,bloco_m=block,
            n_grupos=int(len(np.unique(gr))),n_folds=5,
            validacao="grupos espaciais GroupKFold, embargo 25m; cada ponto fora do treino")
        record.update(metric(y,pred[n]))
        m=y>0
        pm=metric(y[m],pred[n][m])
        record["mae_positivos_meta_m"]=pm["mae_vs_meta_m"]
        record["n_positivos_meta"]=pm["n"]
        summary.append(record)
    return summary,rows,pred,D

def write_report(out,df,metrics,folds,full):
    scores=pd.DataFrame(metrics)
    lines=[
      "# V3 — Onze familias do artigo de CW–H adaptadas para H=f(D_eq), comparadas com a Meta/WRI",
      "",
      "## ADVERTENCIA DE INTERPRETACAO",
      "",
      "**As 11 familias de curvas foram testadas, mas NAO sao as 11 equacoes",
      "originais com os coeficientes publicados.** O artigo de",
      "[Chatziathanasiou et al. (2024)](https://doi.org/10.3390/land13101579)",
      "ajusta **largura de copa medida CW=f(H) a partir de altura real medida**",
      "em especies e cidades gregas. **Aqui adaptamos a mesma familia de curvas**",
      "para **H_modelada_Meta=f(D_eq)**. A variavel D_eq=2sqrt(A_superpixel/pi)",
      "e o **diametro circular equivalente de um SUPERPIXEL QUICKSHIFT**,",
      "**nao a largura da copa individual observada no artigo**.",
      "",
      "A [correcao de 2026](https://doi.org/10.3390/land15030473)",
      "retificou formas de equacoes no artigo; este ensaio registra a correcao",
      "e nao reutiliza coeficientes de especies da Grecia.",
      "Os valores Meta/WRI CHMv2 sao **altura de dossel MODELADA**,",
      "nao medidas de campo. O MAE avalia exclusivamente concordancia",
      "com Meta/WRI, nunca precisao de altura real.",
      "",
      "## Parametrizacao ensaiada",
      "",
      "Definimos x=D_eq/10 m para estabilizar numericamente os ajustes",
      "(sem mudar a familia funcional). Restricao de crescimento",
      "nao decrescente e valores previstos entre 0 e 40 m. No modelo",
      "logistico, u=40 m e fixo como hipotese de trabalho.",
      "",
      "| Modelo artigo (familia) | Equacao ADAPTADA, H_modelada=f(x) |",
      "|---|---|",
      "| 1. Linear | H=b0+b1 x |",
      "| 2. Logaritmico | H=b0+b1 ln(x) |",
      "| 3. Inverso | H=b0-b1/x |",
      "| 4. Quadratico | H=b0+b1 x+b2 x² |",
      "| 5. Cubico | H=b0+b1 x+b2 x²+b3 x³ |",
      "| 6. Potencial | H=b0 x^b1 |",
      "| 7. Composto | H=b0 b1^x |",
      "| 8. Curva-S | H=exp(b0-b1/x) |",
      "| 9. Logistico | H=1/(1/40+b0 b1^x) |",
      "| 10. Crescimento | H=exp(b0+b1 x) |",
      "| 11. Exponencial | H=b0 exp(b1 x) |",
      "",
      "**Atenção: modelos 7, 10 e 11 sao reparametrizacoes da MESMA",
      "familia exponencial de dois parametros**, nao tres classes",
      "funcionais independentes. A ordem entre elas nao deve ser",
      "interpretada como superioridade de uma tecnica distinta.",
      "",
      "## Resultados com validacao espacial de 5 divisões e embargo de 25 m",
      "",
      "Todos os 257 pontos aparecem em teste fora do respectivo",
      "ajuste em cada uma das escalas 250 m e 500 m.",
      "A selecao da familia e feita somente em tres folds",
      "internos, sem usar os alvos de teste externos.",
      "",
    ]
    for kind,col in [("Pixel exato","altura_meta_pixel_m"),
                     ("Maximo 5 m","altura_meta_max_5m_m")]:
        for block in (250,500):
            part=scores[(scores.alvo==col)&(scores.bloco_m==block)].sort_values(
                ["mae_vs_meta_m","modelo"])
            lines.extend([
              f"### {kind} — blocos de {block} m",
              "",
              "| Modelo | MAE vs. Meta (m) | RMSE vs. Meta (m) | MAE no subset Meta >0 (m) |",
              "|---|---:|---:|---:|"])
            for it in part.itertuples():
                lines.append(f"| {it.modelo} | {it.mae_vs_meta_m:.3f} | {it.rmse_vs_meta_m:.3f} | {it.mae_positivos_meta_m:.3f} |")
            base=part.loc[part.modelo=="Controle_constante","mae_vs_meta_m"].iloc[0]
            best=part[part.modelo.isin(MODEL_NAMES)].iloc[0]
            nested=part[part.modelo=="Selecao_aninhada"].iloc[0]
            selections=Counter(pd.DataFrame(folds).query("alvo==@col and bloco_m==@block").modelo_escolhido_interno)
            lines.extend([
              "",
              f"**Melhor das 11 por MAE observado:** {best.modelo} ({best.mae_vs_meta_m:.3f} m).",
              f"**Controle constante:** {base:.3f} m.",
              f"**Seleção aninhada:** {nested.mae_vs_meta_m:.3f} m.",
              f"**Famílias selecionadas internamente nos cinco folds:** {dict(selections)}.",
              "A melhor família da tabela é uma escolha exploratória APÓS ver",
              "os resultados de teste; para alegar desempenho de seleção",
              "sem viés, usar a linha Seleção_aninhada e avaliação futura.",
              "",
            ])
    lines.extend([
      "## Reprodutibilidade",
      "",
      "- [257 pontos, referência Meta e previsões OOF de todas as famílias](v3_11_familias_meta_257_previsoes.csv).",
      "- [Resumo dos 11 modelos, controle e seleção aninhada](v3_11_familias_meta_resumo.csv).",
      "- [Folds espaciais, embargo e escolha interna](v3_11_familias_meta_folds.csv).",
      "- [Gráfico comparativo de MAE](v3_11_familias_meta_mae.png).",
      "- [Script do experimento](../../experimentos/v3_testar_11_modelos_artigo_meta.py).",
      "",
      "**Limitações:** D_eq calculado por área de SUPERPIXEL pode não",
      "representar nenhuma copa real. O máximo Meta em 5 m pode",
      "pertencer a outra árvore; zero no pixel Meta não implica",
      "ausência da árvore. Nenhum modelo foi validado com altura medida",
      "em campo. Estes resultados NÃO justificam substituir automaticamente",
      "os coeficientes históricos C1–C6 do notebook original.",
      "",
    ])
    (out/"v3_11_familias_meta_relatorio.md").write_text("\n".join(lines),encoding="utf-8")

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--csv",required=True,type=Path)
    ap.add_argument("--out",required=True,type=Path)
    args=ap.parse_args()
    df=pd.read_csv(args.csv,encoding="utf-8-sig").sort_values("ponto_id").reset_index(drop=True)
    needed={"ponto_id","longitude","latitude","area_superpixel_m2"}|set(TARGETS.values())
    if len(df)!=257 or df.ponto_id.nunique()!=257 or not needed.issubset(df):
        raise ValueError("Esperados 257 pontos originais com coords, area e Meta.")
    if not np.isfinite(df[list(needed-{"ponto_id"})].to_numpy(float)).all():
        raise ValueError("Valores ausentes ou infinitos")
    if not (df.area_superpixel_m2>0).all():raise ValueError("Area nao positiva")
    args.out.mkdir(parents=True,exist_ok=True)
    all_summary=[];all_folds=[]
    px=df[["ponto_id","area_superpixel_m2","longitude","latitude",
        "altura_meta_pixel_m","altura_meta_max_5m_m"]].copy()
    for targetname,col in TARGETS.items():
        for block in (250,500):
            summary,folds,preds,D=evaluation(df,block,col)
            all_summary.extend(summary);all_folds.extend(folds)
            for name,arr in preds.items():
                px[f"{targetname}_{block}m_{name}"]=arr
    px.insert(1,"largura_circular_superpixel_equiv_m",
              2*np.sqrt(df.area_superpixel_m2.to_numpy(float)/np.pi))
    pd.DataFrame(all_summary).to_csv(args.out/"v3_11_familias_meta_resumo.csv",
                                index=False,encoding="utf-8-sig")
    pd.DataFrame(all_folds).to_csv(args.out/"v3_11_familias_meta_folds.csv",
                                index=False,encoding="utf-8-sig")
    px.to_csv(args.out/"v3_11_familias_meta_257_previsoes.csv",
                                index=False,encoding="utf-8-sig")
    write_report(args.out,df,all_summary,all_folds,px)
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    summary=pd.DataFrame(all_summary)
    plt.figure(figsize=(11,6))
    bb=summary[(summary.bloco_m==250)&(summary.alvo==TARGETS["pixel"])]
    bb=bb.sort_values("mae_vs_meta_m")
    plt.barh(bb.modelo[::-1],bb.mae_vs_meta_m[::-1])
    plt.xlabel("MAE vs altura modelada Meta/WRI no pixel (m)")
    plt.title("11 familias adaptadas, controle e seleção aninhada — validação espacial 250 m")
    plt.tight_layout()
    plt.savefig(args.out/"v3_11_familias_meta_mae.png",dpi=160)
    plt.close()
    for (t,b),g in summary.groupby(["alvo","bloco_m"]):
        g1=g[g.modelo.isin(MODEL_NAMES)].sort_values("mae_vs_meta_m")
        const=g.loc[g.modelo=="Controle_constante","mae_vs_meta_m"].iloc[0]
        print(json.dumps({"target":t,"block":int(b),
            "melhor_entre_11":g1.iloc[0].modelo,
            "mae_melhor":round(float(g1.iloc[0].mae_vs_meta_m),4),
            "mae_constante":round(float(const),4),
            "mae_selecao_aninhada":float(g.loc[
              g.modelo=="Selecao_aninhada","mae_vs_meta_m"].iloc[0])},
            ensure_ascii=False),flush=True)
    print("SUCESSO - 11 familias x 2 referencias x 2 escalas espaciais; 257 pontos",flush=True)

if __name__=="__main__":
    main()
