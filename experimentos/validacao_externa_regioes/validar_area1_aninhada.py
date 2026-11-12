#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Nova avaliação Area1 com TESTE ESPACIAL EXTERNO AO AJUSTE e CV aninhada.

Para cada escala (250 m e 500 m): 5 partições externas espaciais válidas
80/20; em cada partição, seleciona hiperparâmetros em 3 validações internas
APENAS nos blocos do treino externo, com embargo 25 m em cada separação.
Depois treina nos dados disponíveis do treino externo e avalia no teste.

Não é reprodução estrita da partição/semente dos experimentos históricos.
Não utiliza nem importa rótulos de outras cidades.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import (accuracy_score, balanced_accuracy_score,
                             confusion_matrix, f1_score)
from sklearn.model_selection import GroupShuffleSplit

from treinar_area1 import (MODELS, SCALES, FEATURES, RECEITAS, criar_modelo,
                           read_training_data, read_geometry, assign_groups,
                           embargo_train)


def candidate_splits(indices, groups, labels, xy, geoms, n, seed, embargo=25,
                     test_size=.2, minimum_train=35, minimum_test=10):
    """Cria n splits válidos, sem sobreposição de grupos e sem fuga espacial."""
    if len(set(groups[indices]))<5:
        raise ValueError("Não há pelo menos 5 blocos espaciais no treino da Area1.")
    split=GroupShuffleSplit(n_splits=max(n*30,50),test_size=test_size,random_state=seed)
    selected=[]
    for tr_local,va_local in split.split(indices,labels[indices],groups[indices]):
        tr_global=indices[tr_local]
        va_global=indices[va_local]
        tr_global=embargo_train(xy,tr_global,va_global,embargo,geoms)
        if len(tr_global)<minimum_train or len(va_global)<minimum_test:
            continue
        if len(set(labels[tr_global]))<2 or len(set(labels[va_global]))<2:
            continue
        if not set(groups[tr_global]).isdisjoint(set(groups[va_global])):
            raise AssertionError("Vazamento de grupo train/test")
        selected.append((tr_global,va_global))
        if len(selected)==n:
            return selected
    raise RuntimeError(f"Não foram obtidas {n} partições válidas; apenas {len(selected)}.")


def evaluate(dataset:Path, output:Path, geometry:Path|None=None,
             centroid_embargo:bool=False,
             outer:int=5, inner:int=3, models=None, scales=SCALES):
    if geometry is None and not centroid_embargo:
        raise ValueError("Forneça --geometrias ou --permitir-embargo-centroides.")
    if outer<2 or inner<2:
        raise ValueError("São necessárias ao menos duas partições internas e externas.")
    frame=read_training_data(dataset)
    geoms=read_geometry(geometry,frame)
    xy=frame[["x","y"]].to_numpy(dtype=float)
    X=frame[list(FEATURES)].to_numpy(dtype=float)
    y=frame.classe.to_numpy(dtype=str)
    chosen_models=tuple(models or MODELS)
    unknown=set(chosen_models)-set(MODELS)
    if unknown:
        raise ValueError(f"Modelos desconhecidos: {unknown}")
    output.mkdir(parents=True,exist_ok=True)
    evaluations=[]
    selections=[]
    for block in scales:
        groups=assign_groups(xy,block)
        outer_splits=candidate_splits(
            np.arange(len(frame)),groups,y,xy,geoms,outer,
            seed=20261112+block,test_size=.2,minimum_train=50,minimum_test=12)
        for split_no,(tr,te) in enumerate(outer_splits,1):
            inner_splits=candidate_splits(
                tr,groups,y,xy,geoms,inner,
                seed=20270000+block*100+split_no,
                test_size=.25,minimum_train=35,minimum_test=10)
            if not set(tr).isdisjoint(te):
                raise AssertionError("Índices outer train/test repetidos")
            for name in chosen_models:
                choices=[]
                for recipe in ("moderada","forte"):
                    params=RECEITAS[recipe][name]
                    values=[]
                    for it,(itr,iva) in enumerate(inner_splits,1):
                        clf=criar_modelo(name,params)
                        clf.fit(X[itr],y[itr])
                        pred=clf.predict(X[iva])
                        metric=float(f1_score(y[iva],pred,average="macro",
                                              labels=["arvore","grama"],zero_division=0))
                        values.append(metric)
                        selections.append({
                            "bloco_m":block,"divisao_externa":split_no,
                            "modelo":name,"receita":recipe,"validacao_interna":it,
                            "f1_validacao_interna":metric,
                            "n_treino_interno":len(itr),"n_validacao_interna":len(iva)
                        })
                    choices.append((float(np.mean(values)),recipe,params))
                cv_mean,recipe,params=sorted(choices,key=lambda v:(-v[0],v[1]))[0]
                final=criar_modelo(name,params).fit(X[tr],y[tr])
                pred=final.predict(X[te])
                cm=confusion_matrix(y[te],pred,labels=["arvore","grama"])
                evaluations.append({
                    "bloco_m":block,"divisao_externa":split_no,
                    "modelo":name,"receita_escolhida":recipe,
                    "f1_validacao_interna":cv_mean,
                    "f1_teste_espacial":float(f1_score(
                        y[te],pred,average="macro",labels=["arvore","grama"],zero_division=0)),
                    "acuracia":float(accuracy_score(y[te],pred)),
                    "acuracia_balanceada":float(balanced_accuracy_score(y[te],pred)),
                    "n_treino":len(tr),"n_teste":len(te),
                    "cm_arvore_arvore":int(cm[0,0]),
                    "cm_arvore_grama":int(cm[0,1]),
                    "cm_grama_arvore":int(cm[1,0]),
                    "cm_grama_grama":int(cm[1,1])
                })
        print(f"Concluído protocolo Area1 em blocos de {block} m",flush=True)
    tab=pd.DataFrame(evaluations)
    tab.to_csv(output/"area1_aninhada_divisoes.csv",index=False)
    pd.DataFrame(selections).to_csv(output/"area1_validacao_interna.csv",index=False)
    summary=(tab.groupby(["bloco_m","modelo"],as_index=False)
             .agg(f1_macro_media=("f1_teste_espacial","mean"),
                  f1_macro_dp=("f1_teste_espacial","std"),
                  acuracia_media=("acuracia","mean"),
                  acuracia_balanceada_media=("acuracia_balanceada","mean"),
                  folds=("divisao_externa","count")))
    summary.to_csv(output/"area1_resumo_oito_modelos.csv",index=False)
    report={
        "status":"Nova execução de validação espacial aninhada Area1",
        "base_sha256":hashlib.sha256(dataset.read_bytes()).hexdigest(),
        "amostras_segmentos":len(frame),
        "escala_blocos_m":list(scales),
        "particoes_externas_por_escala":outer,
        "particoes_internas_por_particao_externa":inner,
        "razao_teste_externo":.2,
        "distancia_embargo_m":25,
        "embargo":"geometrico" if geoms is not None else "centroides_aproximacao",
        "modelos":list(chosen_models),
        "classes":["arvore","grama"],
        "features":list(FEATURES),
        "aviso":"Partições/sementes novas. NÃO afirmar que estes são os folds históricos do mestrado."
    }
    (output/"metodologia_area1_aninhada.json").write_text(
        json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    print(summary.to_string(index=False))
    return summary


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--csv",type=Path,required=True)
    p.add_argument("--geometrias",type=Path)
    p.add_argument("--permitir-embargo-centroides",action="store_true")
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    evaluate(a.csv,a.out,a.geometrias,a.permitir_embargo_centroides)


if __name__=="__main__":
    main()
