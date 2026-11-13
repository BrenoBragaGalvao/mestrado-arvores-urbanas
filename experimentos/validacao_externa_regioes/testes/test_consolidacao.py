#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Consolidação sem resultados nunca inventa métricas; com dados, exige manifesto."""
import json
import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from consolidar_resultados import aggregate


def test_ausencia_resultados_registra_pendencias(tmp_path):
    root=tmp_path/"metricas"
    root.mkdir()
    baseline=tmp_path/"baseline.csv"
    out=tmp_path/"saida"
    states=aggregate(root,baseline,out)
    assert states.status.eq("não avaliada").all()
    assert not (out/"comparacao_externa_oito_modelos.csv").exists()
    assert "aguardando rótulos" in (out/"relatorio.md").read_text()


def test_consolida_uma_regiao_mantendo_outros_sem_metricas(tmp_path):
    root=tmp_path/"metricas"
    folder=root/"centro_novo_hamburgo"
    folder.mkdir(parents=True)
    pd.DataFrame([{"modelo":f"modelo_{i}","f1_macro":.7+i*.01,
                   "acuracia":.75,"acuracia_balanceada":.7,"amostras":40}
                  for i in range(8)]).to_csv(folder/"metricas_externas.csv",index=False)
    (folder/"manifesto_avaliacao.json").write_text(
        json.dumps({"status":"VALIDACAO_EXTERNA_CONCLUIDA",
                    "regiao":"centro_novo_hamburgo"}),encoding="utf-8")
    pd.DataFrame([{"modelo":f"modelo_{i}","bloco_m":250,
                   "NDVI + HSV + Canny":.80} for i in range(8)]).to_csv(
        tmp_path/"base.csv",index=False)
    out=tmp_path/"saida"
    states=aggregate(root,tmp_path/"base.csv",out)
    assert states.loc[states.regiao=="centro_novo_hamburgo","status"].item()=="métricas externas verificadas"
    assert states.status.eq("não avaliada").sum()==2
    assert len(pd.read_csv(out/"comparacao_externa_oito_modelos.csv"))==8
    comp=pd.read_csv(out/"contexto_descritivo_area1_vs_externo.csv")
    assert comp.comparabilidade.str.contains("Não pareado").all()
    assert "não avaliada" in (out/"relatorio.md").read_text()
