#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""V3: TABELA UNICA de 257 arvores, todas as formulas e as 11 familias.

As primeiras 3 colunas SEMPRE sao:
(1) Arvore (1..257), (2) Meta/WRI pixel, (3) Meta/WRI maximo em 5 m.

Inclui C1-C6 potenciais, logaritmica e potencia ajustada aos 257 pontos,
e as 11 familias adaptadas do artigo, com previsoes ESPACIAIS fora da
amostra (OOF) em blocos de 250 m, separadas por alvo Meta pixel ou raio 5 m.
Inclui controles e selecao aninhada; o CSV COMPLETO inclui ainda C1-C6
lineares, modelos calibrados em 5m e previsoes OOF em blocos de 500m.

ATENCAO: as familias publicadas no artigo foram ADAPTADAS e recalibradas
usando altura modelada Meta; NAO sao os coeficientes originalmente publicados.
C1-C6 sao indices nao calibrados em metros. A e area de superpixel, nao copa.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import numpy as np
import pandas as pd

FAMILIAS = [
    ("Linear","Linear"),("Logaritmico","Logarítmico"),
    ("Inverso","Inverso"),("Quadratico","Quadrático"),
    ("Cubico","Cúbico"),("Potencial","Potencial"),
    ("Composto","Composto"),("Curva_S","Curva-S"),
    ("Logistico","Logístico"),("Crescimento","Crescimento"),
    ("Exponencial","Exponencial")
]
CONTROLES = [("Controle_constante","Controle constante"),
             ("Selecao_aninhada","Seleção aninhada")]
FIRST = ["Árvore","Meta pixel (m)","Meta 5 m (m)"]
ALL = FAMILIAS + CONTROLES

def validate_table(frame, idcol, required, label):
    if len(frame)!=257 or frame[idcol].nunique()!=257:
        raise ValueError(f"{label}: esperados 257 IDs originais sem duplicatas")
    if not set(required).issubset(frame.columns):
        raise ValueError(f"{label}: colunas ausentes {set(required)-set(frame.columns)}")
    if set(frame[idcol].astype(int))!=set(range(257)):
        raise ValueError(f"{label}: IDs originais esperados 0..256")

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--formulas",type=Path,required=True)
    ap.add_argument("--modelos",type=Path,required=True)
    ap.add_argument("--out",type=Path,required=True)
    opt=ap.parse_args()
    formulas=pd.read_csv(opt.formulas,encoding="utf-8-sig")
    modelos=pd.read_csv(opt.modelos,encoding="utf-8-sig")
    validate_table(formulas,"Ponto_ID",["Arvore","Meta_WRI_pixel_m",
                  "Meta_WRI_maximo_5m_m","Area_superpixel_m2",
                  *[f"C{i}_potencial" for i in range(1,7)],
                  "Logaritmica_ajustada_pixel_m","Potencial_ajustada_pixel_m"],"formulas")
    names = [n for n,_ in ALL]
    oof_cols = [f"{target}_{block}m_{name}"
                for target in ["pixel","raio5"] for block in [250,500]
                for name in names]
    validate_table(modelos,"ponto_id",["altura_meta_pixel_m",
                 "altura_meta_max_5m_m", *oof_cols],"11 familias")
    formulas=formulas.sort_values("Ponto_ID").reset_index(drop=True)
    modelos=modelos.sort_values("ponto_id").reset_index(drop=True)
    merged=formulas.merge(modelos,on=None,left_on="Ponto_ID",right_on="ponto_id",
        how="left",validate="one_to_one")
    if len(merged)!=257 or not (merged.Arvore.to_numpy()==np.arange(1,258)).all():
        raise ValueError("Contagem de arvores incorreta")
    for orig,new in [
      ("Meta_WRI_pixel_m","altura_meta_pixel_m"),
      ("Meta_WRI_maximo_5m_m","altura_meta_max_5m_m")]:
        if not np.allclose(merged[orig],merged[new],equal_nan=True,rtol=0,atol=1e-8):
            raise ValueError("Meta pixel ou 5m difere entre experimentos")
    if not np.isfinite(merged[oof_cols].to_numpy(float)).all():
        raise ValueError("Alguma previsao OOF das 11 familias esta ausente")

    main=pd.DataFrame()
    main[FIRST[0]]=merged["Arvore"].astype(int)
    main[FIRST[1]]=merged["Meta_WRI_pixel_m"]
    main[FIRST[2]]=merged["Meta_WRI_maximo_5m_m"]
    for i in range(1,7):
        main[f"C{i} potencial (índice)"]=merged[f"C{i}_potencial"]
    main["Log ajustada ao pixel (m)"]=merged["Logaritmica_ajustada_pixel_m"]
    main["Potência ajustada ao pixel (m)"]=merged["Potencial_ajustada_pixel_m"]
    # Agrupar as duas predicoes da MESMA familia, deixando o alvo claro.
    for key,label in ALL:
        main[f"{label} — pixel OOF 250m (m)"]=merged[f"pixel_250m_{key}"]
        main[f"{label} — 5m OOF 250m (m)"]=merged[f"raio5_250m_{key}"]
    main["Ponto_ID original"]=merged["Ponto_ID"].astype(int)
    main["Área superpixel (m²)"]=merged["Area_superpixel_m2"]
    assert main.columns.tolist()[:3]==FIRST
    assert len(main)==257

    full=main.copy()
    for i in range(1,7):
        full[f"C{i} linear (índice)"]=merged[f"C{i}_linear"]
    for name in ["Logaritmica_ajustada_5m_m","Potencial_ajustada_5m_m"]:
        full[name]=merged[name]
    for key,label in ALL:
        full[f"{label} — pixel OOF 500m (m)"]=merged[f"pixel_500m_{key}"]
        full[f"{label} — 5m OOF 500m (m)"]=merged[f"raio5_500m_{key}"]
    full["Superpixel toca borda"]=merged["Superpixel_toca_borda"]

    opt.out.mkdir(exist_ok=True,parents=True)
    csv_main=opt.out/"v3_todos_modelos_meta_257.csv"
    csv_full=opt.out/"v3_todos_modelos_meta_257_completo.csv"
    main.to_csv(csv_main,index=False,encoding="utf-8-sig",float_format="%.6f")
    full.to_csv(csv_full,index=False,encoding="utf-8-sig",float_format="%.6f")

    lines=[
       "# V3 — Tabela das 257 árvores: Meta pixel, Meta 5 m e todos os modelos",
       "",
       "**Ordem obrigatória:** 1. **Árvore (1–257)**; 2. **Meta/WRI pixel exato**;",
       "3. **Meta/WRI máximo no raio de 5 m**; depois vêm **C1–C6 potenciais**,",
       "a **logarítmica** e a **potência recalibrada**, e as **11 famílias**",
       "do artigo (cada uma com duas colunas, porque foi testada contra",
       "Meta pixel e Meta em 5 m). Os controles constante e seleção aninhada",
       "também aparecem no final.",
       "",
       "**Leia as colunas corretamente:**",
       "- **Meta pixel e Meta 5 m**: são duas leituras do **mesmo produto**",
       "  Meta/WRI CHMv2; o máximo em 5 m pode representar outra árvore.",
       "- **C1–C6 potenciais**: são índices do notebook original, **não alturas",
       "  individualmente validadas em metros**.",
       "- **Log e potência ajustadas**: valores ajustados com os mesmos 257 pontos",
       "  para reproduzir alturas modeladas no pixel Meta (não teste independente).",
       "- **11 famílias do artigo**: suas curvas foram **adaptadas e reajustadas**",
       "  para prever a altura Meta a partir do diâmetro circular equivalente de",
       "  **superpixel Quickshift**, não largura de copa medida. As previsões",
       "  **OOF 250 m** vieram da validação espacial com blocos de 250 m e",
       "  **25 m de embargo**, sem usar o alvo de cada ponto no respectivo ajuste.",
       "- **Controle constante** e **seleção aninhada** são referências de",
       "  validação, e não equações de altura individual comprovada.",
       "",
       "As famílias do artigo original ajustam **largura de copa CW=f(H)**,",
       "não o problema empregado aqui. Não use estes resultados para alegar",
       "que as onze equações publicadas foram reproduzidas com seus",
       "coeficientes originais. As alturas Meta são **modeladas**,",
       "não medidas em campo; todos os erros são **versus Meta**,",
       "não erros de altura real.",
       "",
       "## Tabela completa: 257 árvores",
       "",
       "| "+" | ".join(main.columns)+" |",
       "| "+" | ".join("---:" for _ in main.columns)+" |",
    ]
    for row in main.itertuples(index=False,name=None):
        rendered=[]
        for i,value in enumerate(row):
            if i in (0,len(row)-2):rendered.append(str(int(value)))
            elif isinstance(value,(int,float,np.integer,np.floating)):
                rendered.append(f"{float(value):.2f}".replace(".",","))
            else:rendered.append(str(value))
        lines.append("| "+" | ".join(rendered)+" |")
    lines.extend([
        "",
        "## Downloads e reprodução",
        "",
        "- [CSV principal com todas as famílias em blocos de 250 m](v3_todos_modelos_meta_257.csv).",
        "- [CSV ampliado: C1–C6 lineares, alturas ajustadas a 5 m e",
        "  previsões OOF em blocos de 500 m](v3_todos_modelos_meta_257_completo.csv).",
        "- [Resultados de validação das onze famílias](v3_11_familias_meta_resumo.csv).",
        "- [Script reproduzível desta tabela](../../experimentos/v3_gerar_tabela_todos_modelos.py).",
        "",
    ])
    md=opt.out/"v3_todos_modelos_meta_257_tabela.md"
    md.write_text("\n".join(lines),encoding="utf-8")
    print("SUCESSO",len(main),"pontos",len(main.columns),"colunas na tabela",
          len(full.columns),"colunas no CSV completo")
    print("Primeiras colunas:",main.columns[:3].tolist())

if __name__=="__main__":
    main()
