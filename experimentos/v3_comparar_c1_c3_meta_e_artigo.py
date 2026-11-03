#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""V3: C1-C3 original (potencial/linear) + modelos CW(H) invertidos do artigo.
META/WRI eh altura MODELADA, nao altura de campo. Coeficientes C1-C3 nao
foram publicados por Chatziathanasiou et al. (2024).
"""
import argparse
import json
import numpy as np
import pandas as pd
from pathlib import Path

CONFIG={"C1":(0.5,0.7),"C2":(0.6,0.8),"C3":(2.5,0.4)}
# Inversoes algebricas de equacoes publicadas. As referencias sao largura
# de copa CW=f(altura H), e NAO fornecem modelos transferiveis de altura.
# Limites por especie da Tabela 3 de Chatziathanasiou et al. (2024).
PAPER=[
  ("Magnolia_Kavala_log","Magnolia grandiflora","Kavala",
   "CW=-1.906+3.691ln(H)","H=exp((CW+1.906)/3.691)",.35,8.14,1.8,13.4,
   lambda w:np.exp((w+1.906)/3.691)),
  ("Magnolia_Orestiada_log","Magnolia grandiflora","Orestiada",
   "CW=-1.440+3.375ln(H)","H=exp((CW+1.440)/3.375)",.35,8.14,1.8,13.4,
   lambda w:np.exp((w+1.440)/3.375)),
  ("Magnolia_Xanthi_inverse","Magnolia grandiflora","Xanthi",
   "CW=7.280-16.672/H","H=16.672/(7.280-CW)",.35,8.14,1.8,13.4,
   lambda w:16.672/np.where(w<7.280,7.280-w,np.nan)),
  ("Magnolia_Komotini_inverse","Magnolia grandiflora","Komotini",
   "CW=7.394-14.882/H","H=14.882/(7.394-CW)",.35,8.14,1.8,13.4,
   lambda w:14.882/np.where(w<7.394,7.394-w,np.nan)),
  ("Acer_total_compound","Acer negundo","4 cidades",
   "CW=0.676*(1.123**H)","H=ln(CW/0.676)/ln(1.123)",.79,17.30,1.6,15.6,
   lambda w:np.log(w/.676)/np.log(1.123))
]

def metrics(p,y):
    m=np.isfinite(p)&np.isfinite(y)
    x=p[m]
    z=y[m]
    if len(x)==0:return dict(n=0,delta_medio=None,delta_mediano=None,r=None)
    cor=float(pd.Series(x).corr(pd.Series(z))) if len(x)>2 and len(np.unique(x))>1 and len(np.unique(z))>1 else None
    return dict(n=int(len(x)),delta_medio=float(np.mean(abs(x-z))),
                delta_mediano=float(np.median(abs(x-z))),r=cor)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--input",required=True,type=Path)
    ap.add_argument("--out",required=True,type=Path)
    args=ap.parse_args()
    args.out.mkdir(exist_ok=True,parents=True)
    df=pd.read_csv(args.input,encoding="utf-8-sig")
    req={"ponto_id","area_superpixel_m2","altura_meta_pixel_m","altura_meta_max_5m_m"}
    if not req.issubset(df.columns) or len(df)!=257 or df.ponto_id.nunique()!=257:
        raise ValueError("Arquivo de 257 pontos Meta incorreto.")
    A=pd.to_numeric(df.area_superpixel_m2,errors="coerce").to_numpy(float)
    y=pd.to_numeric(df.altura_meta_pixel_m,errors="coerce").to_numpy(float)
    y5=pd.to_numeric(df.altura_meta_max_5m_m,errors="coerce").to_numpy(float)
    if np.isnan(A).any() or (A<=0).any(): raise ValueError("Area superpixel invalida")
    rows=[]
    def append(name,classe,forma,eq,p,especie="",cidade=""):
        d={"modelo":name,"grupo":classe,"forma":forma,"equacao":eq,
           "especie_artigo":especie,"cidade_artigo":cidade,
           "n_alturas_hipoteticas":int(np.isfinite(p).sum())}
        for label,ref in [("pixel_todos",y),("pixel_positivo",np.where(y>0,y,np.nan)),
                          ("raio5_todos",y5),("raio5_positivo",np.where(y5>0,y5,np.nan))]:
            for k,v in metrics(p,ref).items():d[f"{k}_{label}"]=v
        rows.append(d)
    for cfg,(a,b) in CONFIG.items():
        for f,p,expr in [("potencial",a*A**b,f"{a}*A**{b}"),
                         ("linear",a+b*A,f"{a}+{b}*A")]:
            df[f"{cfg}_{f}"]=p
            append(f"{cfg}_{f}","Original C1-C3",f,expr,p)
    # Apenas HIPOTESE de copa circular equivalente: superpixel nao e copa.
    CW=np.sqrt(4*A/np.pi)
    df["largura_equivalente_superpixel_m"]=CW
    entries=[]
    for name,esp,city,forward,back,wmin,wmax,hmin,hmax,fn in PAPER:
        with np.errstate(all="ignore"): h=fn(CW)
        ok=(np.isfinite(h)&(CW>=wmin)&(CW<=wmax)&(h>=hmin)&(h<=hmax))
        h=np.where(ok,h,np.nan)
        df[f"artigo_{name}_H_hipotetica_m"]=h
        append(name,"Artigo 2024 invertido",back,back,h,esp,city)
        entries.append({"modelo":name,"especie":esp,"cidade":city,
          "CW_original_em_funcao_de_H":forward,"H_inversa":back,
          "n_sem_extrapolacao":int(ok.sum()),"CW_min":wmin,"CW_max":wmax,
          "H_min":hmin,"H_max":hmax,
          "referencia":"Chatziathanasiou et al. (2024) Land 13 1579"})
    summary=pd.DataFrame(rows)
    summary.to_csv(args.out/"v3_c1_c3_meta_resumo_comparativo.csv",index=False,encoding="utf-8-sig")
    df.to_csv(args.out/"v3_c1_c3_meta_257_pontos.csv",index=False,encoding="utf-8-sig")
    pd.DataFrame(entries).to_csv(args.out/"v3_modelos_artigo_testados.csv",index=False,encoding="utf-8-sig")
    ordered=summary[summary.grupo=="Original C1-C3"].sort_values("delta_medio_raio5_positivo")
    art=summary[summary.grupo=="Artigo 2024 invertido"].sort_values("delta_medio_raio5_positivo")
    fmt=lambda v: "-" if pd.isna(v) else f"{v:.3f}"
    lines=[
      "# V3 — Comparacao exploratoria de C1-C3 e modelos de Chatziathanasiou et al. (2024)",
      "",
      "**Atencao:** o artigo apresenta CW=f(H) por especie em cidades gregas.",
      "**Os coeficientes C1-C3 do codigo original NAO sao desse artigo.**",
      "As estimativas Meta/WRI sao alturas MODELADAS de dossel, nao alturas de campo.",
      "As diferencas numericas abaixo nao comprovam precisao real de altura.",
      "Nao foi feito ajuste de coeficientes com a Meta.",
      "",
      "## 1. Configuracoes empiricas originais (A = area do SUPERPIXEL)",
      "",
      "| Config. | a | b | Potencial | Linear |",
      "|---|---:|---:|---|---|",
    ]
    for cfg,(a,b) in CONFIG.items():
        lines.append(f"| {cfg} | {a} | {b} | {a} x A^{b} | {a} + {b} x A |")
    lines += ["","## 2. Proximidade numerica da Meta nos mesmos 257 pontos","",
              "Comparacao principal: valor do pixel da Meta, incluindo zeros.",
              "Sensibilidade: maximo Meta em raio de 5 m, excluindo valores zero.",
              "Os indices originais NAO estao calibrados em metros: diferencas",
              "devem ser descritas apenas como divergencia numerica, nao MAE",
              "de altura real. O raio de 5 m pode incluir outra copa.","",
              "| Modelo | n pixel | Divergencia media pixel | n Meta raio 5m >0 | Divergencia media raio 5m >0 | Pearson raio 5m >0 |",
              "|---|---:|---:|---:|---:|---:|"]
    for r in ordered.itertuples(index=False):
        lines.append(f"| {r.modelo} | {r.n_pixel_todos} | {fmt(r.delta_medio_pixel_todos)} | {r.n_raio5_positivo} | {fmt(r.delta_medio_raio5_positivo)} | {fmt(r.r_raio5_positivo)} |")
    lines += ["","## 3. Equacoes publicadas testadas por inversao algebrica","",
              "O artigo mede CW (largura real de copa) e H (altura real)",
              "em Magnolia grandiflora e Acer negundo. Como a Area1 nao mede",
              "CW, foi testada somente a hipotese de largura circular equivalente",
              "CW=sqrt(4A/pi) a partir de area de SUPERPIXEL. Essa suposicao",
              "nao demonstra largura real; especie de cada individuo e desconhecida.",
              "Apenas alturas hipoteticas dentro do intervalo observado da especie",
              "no artigo foram registradas; demais pontos sao ausentes.",
              "",
              "| Modelo/especie | Equacao H invertida | n/257 validos sem extrapolacao | Diverg. pixel | Diverg. raio5 >0 |",
              "|---|---|---:|---:|---:|"]
    for r in art.itertuples(index=False):
        lines.append(f"| {r.modelo} / {r.especie_artigo} | {r.equacao} | {r.n_alturas_hipoteticas} | {fmt(r.delta_medio_pixel_todos)} | {fmt(r.delta_medio_raio5_positivo)} |")
    lines += ["",
              "A menor divergencia contra a Meta NAO indica o modelo",
              "mais correto biologicamente; a Meta nao e verdade de campo.",
              "A comparacao com o artigo e somente ensaio matematico de",
              "transferibilidade e nao validacao ou calibracao regional.",
              "",
              "## 4. Fonte e dados reprodutiveis",
              "",
              "- Artigo: https://doi.org/10.3390/land13101579 (Tabelas 1, 3, 4, 5, 6, 8 e 9).",
              "- Meta/WRI CHMv2: https://registry.opendata.aws/dataforgood-fb-forestsv2/",
              "- CSV origem: v3_comparacao_c3_meta_257.csv (257 pontos).",
              "- Saidas: v3_c1_c3_meta_257_pontos.csv; v3_c1_c3_meta_resumo_comparativo.csv;",
              "  v3_modelos_artigo_testados.csv; v3_c1_c3_meta_comparacao.png.",
              "- Necessario para validacao de altura: copa realmente delimitada,",
              "  especie e medicao independente de altura dos mesmos individuos.",
              ""]
    (args.out/"v3_c1_c3_meta_relatorio.md").write_text("\n".join(lines),encoding="utf-8")
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig,ax=plt.subplots(figsize=(9,5))
    lab=ordered.modelo.to_list()
    values=ordered.delta_medio_raio5_positivo.to_list()
    ax.barh(lab[::-1],values[::-1])
    ax.set(xlabel="Divergencia numerica media para Meta (raio 5m, >0)",
           title="C1-C3: proximidade numerica nao e acuracia real")
    fig.tight_layout()
    fig.savefig(args.out/"v3_c1_c3_meta_comparacao.png",dpi=150)
    plt.close(fig)
    print(json.dumps({"pontos":len(df),"n_configuracoes":len(ordered),
      "n_artigo":len(art),"ordem_numerica":lab,
      "aviso":"Nao ha validacao contra alturas de campo"},ensure_ascii=False,indent=2))

if __name__=="__main__":
    main()
