#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""V3: compara Meta/WRI com C1-C6 potenciais/lineares, log e potencia ajustada.

ENTRADA:
- 257 pontos com area de superpixel e Meta/WRI no pixel exato e no raio 5m;
- parametros de formulas ajustadas existentes no repositorio.
SAIDA:
- planilha principal: Arvore (contagem 1-257) na PRIMEIRA coluna, Meta pixel na SEGUNDA, Meta maximo 5m na TERCEIRA;
- tabela integral com variantes lineares e as duas referencias Meta lado a lado.
LIMITES:
- C1-C6 originais sao INDICES EMPIRICOS, nao alturas calibradas em metros.
- A e area de superpixel, nao area confirmada de copa.
- Log e potencia calibradas frente a Meta usando todos os 257 pontos:
  esta tabela descreve valores calculados; nao fornece validacao independente.
- Formula de diametro de copa H=c+a*D_copa^b NAO e calculavel aqui:
  D_copa individual e coeficientes especificos nao foram observados.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import numpy as np
import pandas as pd

COEFS={
    "C1": (.5,.7),
    "C2": (.6,.8),
    "C3": (2.5,.4),
    "C4": (4.,.5),
    "C5": (.4,.9),
    "C6": (1.35,.72),
}
FIELDS=["ponto_id","area_superpixel_m2","altura_meta_pixel_m","altura_meta_max_5m_m","toca_borda_tile"]

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--pontos",type=Path,required=True)
    ap.add_argument("--parametros",type=Path,required=True)
    ap.add_argument("--out",type=Path,required=True)
    x=ap.parse_args()
    df=pd.read_csv(x.pontos,encoding="utf-8-sig")
    pars=json.loads(x.parametros.read_text(encoding="utf-8"))
    if len(df)!=257 or df.ponto_id.nunique()!=257 or not set(FIELDS).issubset(df):
        raise ValueError("Entrada deve conter todos os 257 pontos originais.")
    df=df.sort_values("ponto_id").reset_index(drop=True)
    a=df.area_superpixel_m2.astype(float).to_numpy()
    if not np.isfinite(a).all() or (a<=0).any():
        raise ValueError("Areas invalidas ou ausentes.")
    p_pixel=pars["altura_meta_pixel_m"]["formula_final"]
    p_5m=pars["altura_meta_max_5m_m"]["formula_final"]
    def log(p):
        c,d=p["logaritmica"]["params"]
        return c+d*np.log1p(a)
    def power(p):
        c,d=p["potencia"]["params"]
        return c*np.power(a,d)
    meta=df.altura_meta_pixel_m.astype(float).to_numpy()
    m5=df.altura_meta_max_5m_m.astype(float).to_numpy()
    if not np.isfinite(meta).all() or not np.isfinite(m5).all():
        raise ValueError("Meta possui valores ausentes; revisar fonte.")
    tab=pd.DataFrame({"Arvore":np.arange(1,len(df)+1,dtype=int),
                      "Meta_WRI_pixel_m":meta,"Meta_WRI_maximo_5m_m":m5})
    for name,(c,d) in COEFS.items():
        tab[name+"_potencial"]=c*a**d
    for name,(c,d) in COEFS.items():
        tab[name+"_linear"]=c+d*a
    tab["Logaritmica_ajustada_pixel_m"]=log(p_pixel)
    tab["Potencial_ajustada_pixel_m"]=power(p_pixel)
    tab["Ponto_ID"]=df.ponto_id.astype(int)
    tab["Area_superpixel_m2"]=a
    tab["Meta_WRI_maximo_5m_m"]=m5
    tab["Logaritmica_ajustada_5m_m"]=log(p_5m)
    tab["Potencial_ajustada_5m_m"]=power(p_5m)
    tab["Superpixel_toca_borda"]=df.toca_borda_tile.astype(bool)
    maincols=["Arvore","Meta_WRI_pixel_m","Meta_WRI_maximo_5m_m"]+[
        name+"_potencial" for name in COEFS]+[
        "Logaritmica_ajustada_pixel_m","Potencial_ajustada_pixel_m","Ponto_ID","Area_superpixel_m2"]
    fullcols=["Arvore","Meta_WRI_pixel_m","Meta_WRI_maximo_5m_m"]+[
        name+"_potencial" for name in COEFS]+[name+"_linear" for name in COEFS]+[
        "Logaritmica_ajustada_pixel_m","Potencial_ajustada_pixel_m",
        "Logaritmica_ajustada_5m_m","Potencial_ajustada_5m_m",
        "Ponto_ID","Area_superpixel_m2","Superpixel_toca_borda"]
    x.out.mkdir(parents=True,exist_ok=True)
    mainpath=x.out/"v3_comparacao_c1_c6_log_pot_meta_257.csv"
    fullpath=x.out/"v3_comparacao_completa_c1_c6_pot_linear_log_meta_257.csv"
    tab[maincols].to_csv(mainpath,index=False,encoding="utf-8",float_format="%.6f")
    tab[fullcols].to_csv(fullpath,index=False,encoding="utf-8",float_format="%.6f")
    # Desvios numericos, todos os 257: nao chamar MAE de altura real.
    metrics=[]
    for name in list(COEFS)+["Logaritmica","Potencial ajustada"]:
        col=(name+"_potencial" if name in COEFS else
             "Logaritmica_ajustada_pixel_m" if name=="Logaritmica" else "Potencial_ajustada_pixel_m")
        v=tab[col].to_numpy(float)
        metrics.append({"modelo":name,"n":257,
          "desvio_abs_medio_vs_meta_pixel":float(np.mean(abs(v-meta))),
          "mediana_indice_ou_predicao":float(np.median(v)),
          "interpretacao":("indice original SEM unidade de altura validada" if name in COEFS
                            else "predicao calibrada ao produto Meta/WRI; nao campo")})
    metricpath=x.out/"v3_comparacao_c1_c6_log_pot_resumo.csv"
    pd.DataFrame(metrics).to_csv(metricpath,index=False,encoding="utf-8",float_format="%.6f")
    print(json.dumps({"pontos":len(tab),"colunas_iniciais":maincols[:3],
          "modelo_potencia_ajustada_pixel":p_pixel["potencia"]["formula"],
          "modelo_logaritmico_pixel":p_pixel["logaritmica"]["formula"],
          "tabela_principal":str(mainpath),"tabela_ampliada":str(fullpath)},
          indent=2,ensure_ascii=False))
if __name__=="__main__":main()
