#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Consolidação auditável de métricas EXTERNAS verificadas.

Compara resultados de outras regiões a métricas históricas da Area1 apenas
como CONTEXTO DESCRITIVO (protocolos não pareados; jamais teste cegamente
reproduzido). Regiões sem rótulos aparecem como "não avaliada", sem F1 inventado.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

REGIONS=(
    ("centro_novo_hamburgo","Centro — Novo Hamburgo"),
    ("lomba_grande_novo_hamburgo","Lomba Grande — Novo Hamburgo"),
    ("cristo_rei_sao_leopoldo","Cristo Rei — São Leopoldo"),
)


def aggregate(directory:Path,baseline:Path,output:Path):
    output.mkdir(parents=True,exist_ok=True)
    region_rows=[]
    metrics=[]
    for code,name in REGIONS:
        path=directory/code/"metricas_externas.csv"
        manifest=directory/code/"manifesto_avaliacao.json"
        if not path.is_file() or not manifest.is_file():
            region_rows.append(dict(regiao=code,nome=name,status="não avaliada",
                                    modelos_validados=0,amostras_unicas=None))
            continue
        state=json.loads(manifest.read_text(encoding="utf-8"))
        if state.get("status")!="VALIDACAO_EXTERNA_CONCLUIDA" or state.get("regiao")!=code:
            raise ValueError(f"Manifesto inválido ou divergente em {code}.")
        data=pd.read_csv(path)
        required={"modelo","f1_macro","acuracia","acuracia_balanceada","amostras"}
        if not required.issubset(data.columns):
            raise ValueError(f"Campos faltantes de {code}: {required-set(data.columns)}")
        if data.modelo.duplicated().any() or len(data)!=8:
            raise ValueError(f"São esperados exatamente 8 modelos distintos em {code}.")
        if not data.f1_macro.between(0,1).all():
            raise ValueError(f"F1 inválido em {code}.")
        if data.amostras.nunique()!=1 or data.amostras.iloc[0]<10:
            raise ValueError(f"Base de avaliação externa insuficiente/inconsistente em {code}.")
        data["regiao"]=code
        data["nome_regiao"]=name
        metrics.append(data)
        region_rows.append(dict(regiao=code,nome=name,status="métricas externas verificadas",
                                modelos_validados=len(data),amostras_unicas=int(data.amostras.iloc[0])))
    states=pd.DataFrame(region_rows)
    states.to_csv(output/"status_regioes.csv",index=False)
    if not metrics:
        (output/"relatorio.md").write_text(
            "# Comparação externa — aguardando rótulos e métricas\n\n"
            "Ainda não existem resultados externos verificáveis de Centro, Lomba Grande ou Cristo Rei. "
            "Não é cientificamente correto calcular F1 ou comparar classificadores sem rótulos independentes.\n",
            encoding="utf-8")
        print("Sem validação externa disponível; relatório de status gerado.")
        return states
    external=pd.concat(metrics,ignore_index=True)
    external.to_csv(output/"comparacao_externa_oito_modelos.csv",index=False)
    if baseline.is_file():
        old=pd.read_csv(baseline)
        needed={"bloco_m","modelo","NDVI + HSV + Canny"}
        if not needed.issubset(old.columns):
            raise ValueError(f"CSV base Area1 sem colunas {needed-set(old.columns)}")
        old=old[["bloco_m","modelo","NDVI + HSV + Canny"]].rename(
            columns={"NDVI + HSV + Canny":"f1_area1_historico"})
        ext=external.merge(old,on="modelo",how="left",validate="many_to_many")
        ext["diferenca_descritiva"]=ext.f1_macro-ext.f1_area1_historico
        ext["comparabilidade"]="Não pareado: validação interna histórica Area1 vs teste geográfico externo de novo ajuste"
        ext.to_csv(output/"contexto_descritivo_area1_vs_externo.csv",index=False)
    summary=["# Validação geográfica externa — resultados executados", "",
             "**Resultados calculados exclusivamente a partir de rótulos locais independentes.**",
             "",
             "| Região | Situação | Modelos | Segmentos validados |",
             "|---|---|---:|---:|"]
    for rec in region_rows:
        n=rec["amostras_unicas"]
        summary.append(f'| {rec["nome"]} | {rec["status"]} | {rec["modelos_validados"]} | {n if n is not None else "—"} |')
    summary+=["","## Melhores classificadores por região",""]
    for code,name in REGIONS:
        data=external.loc[external.regiao==code]
        if data.empty:
            summary.append(f"- **{name}:** não avaliada — sem dados suficientes.")
            continue
        best=data.sort_values("f1_macro",ascending=False).iloc[0]
        summary.append(f'- **{name}:** {best.modelo}, F1-macro = {best.f1_macro:.4f} (n={int(best.amostras)} segmentos únicos).')
    summary+=["",
      "**Limitações de interpretação:** modelos foram selecionados e treinados exclusivamente na Area1. "
      "A comparação de F1 externo com 250/500 m da Area1 é descritiva, pois as partições, "
      "os dados e o modelo final de transferência são diferentes. "
      "Não inferir significância estatística ou desempenho universal apenas desses valores.",
      ""]
    (output/"relatorio.md").write_text("\n".join(summary),encoding="utf-8")
    print(states.to_string(index=False))
    return states


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--metricas-root",type=Path,required=True)
    p.add_argument("--baseline",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    aggregate(args.metricas_root,args.baseline,args.out)


if __name__=="__main__":
    main()
