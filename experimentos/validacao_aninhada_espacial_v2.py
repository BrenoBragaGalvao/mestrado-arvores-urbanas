#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Validação aninhada e auditoria de sobreajuste para E2/E3A/E3B.

Reusa SOMENTE dados da Area1. As partições externas (E2/E9) já foram vistas em
estudos anteriores; portanto não constituem teste externo cego. A seleção de
modelo/hiperparâmetros em CADA rodada ocorre estritamente em blocos dos dados
externos de treinamento, com novo embargo espacial. O teste externo NÃO decide
hiperparâmetros. Imprime todas as métricas, inclusive possíveis sobreajustes.

Reprodução das evidências: --modo evidencias --entradas /path/entradas --out /path/saida
Reexecução no notebook V2: --modo v2 --e2 /path/rotulos_sem_duplicacao.csv
                              --e9 /path/e9_dir --out /path/saida
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.spatial import cKDTree
from sklearn.metrics import f1_score, balanced_accuracy_score
from sklearn.model_selection import GroupShuffleSplit

# Módulo auditado e preservado para manter compatibilidade com o notebook V2.
from v2_auditoria_regularizacao import (
    carregar_evidencias, carregar_v2, criar_modelo, RECEITAS,
)

# Grade curta e PRÉ-FIXADA; não examinamos os resultados do teste para ampliá-la.
CANDIDATOS = [
    (nome, receita, RECEITAS[receita][nome])
    for nome in ('Regressão logística', 'SVM RBF', 'KNN')
    for receita in ('forte', 'moderada')
]


def indices_grupos(xy: np.ndarray, bloco: int, origin=None) -> np.ndarray:
    x0, y0 = (float(xy[:,0].min()), float(xy[:,1].min())) if origin is None else origin
    gx = np.floor((xy[:, 0] - x0) / bloco).astype(int)
    gy = np.floor((xy[:, 1] - y0) / bloco).astype(int)
    return np.array([f'{a}_{b}' for a, b in zip(gx, gy)])


def montar_internos(d, train_outer, bloco, tipo_embargo, adj, seed, origin=None):
    xy, yy = d['xy'], d['y']
    grupos = indices_grupos(xy, bloco, origin)
    n_grupos = len(set(grupos[train_outer]))
    if n_grupos < 5:
        raise ValueError(f'Apenas {n_grupos} blocos distintos no treino externo')
    validos = []
    spl = GroupShuffleSplit(n_splits=3, test_size=.25, random_state=seed)
    # Os exemplos de teste EXTERNOS nunca aparecem em train_outer.
    for itr, ite in spl.split(xy[train_outer], yy[train_outer], groups=grupos[train_outer]):
        tr, te = train_outer[itr], train_outer[ite]
        if tipo_embargo == 'geometrias':
            if adj is None: raise ValueError('Geometrias não preparadas')
            tr = tr[~adj[np.ix_(te,tr)].any(axis=0)]
        else:
            dist, _ = cKDTree(xy[te]).query(xy[tr], k=1)
            tr = tr[dist > 25]
        if len(tr) < 45 or len(te) < 12 or len(set(yy[tr])) < 2 or len(set(yy[te])) < 2:
            continue
        if not set(d['id'][tr]).isdisjoint(set(d['id'][te])):
            raise AssertionError('IDs compartilhados em divisão interna')
        if not set(grupos[tr]).isdisjoint(set(grupos[te])):
            raise AssertionError('Blocos compartilhados em divisão interna')
        validos.append((tr, te))
    if len(validos) < 2:
        raise RuntimeError(f'Validação interna insuficiente: {len(validos)} divisões válidas')
    return validos


def executar(bases, divisoes, geometrias, out):
    out.mkdir(parents=True, exist_ok=True)
    selecoes, finais, internos = [], [], []
    adj = None
    if geometrias is not None:
        geo = geometrias.reindex(bases['E2']['id'])
        if geo.isna().any(): raise ValueError('Segmento sem geometria na lista E2')
        # Índice espacial e buffer calculados uma única vez (E2). Matriz apenas
        # de vizinhança geométrica: NÃO usa rótulos ou atributos do teste.
        v = geo.sindex.query(geo.buffer(25), predicate='intersects')
        adj = np.zeros((len(geo),len(geo)),dtype=bool)
        adj[v[0],v[1]] = True
        if not np.all(adj == adj.T): raise AssertionError('Matriz geométrica assimétrica')
    if len(divisoes) != 30:
        raise ValueError('Esperadas 30 divisões externas (10 por experimento)')
    for k, (exp, bloco, rodada, ids_tr, ids_te, tipo) in enumerate(divisoes, 1):
        d = bases[exp]
        lookup = {str(z): i for i, z in enumerate(d['id'])}
        tr_o = np.array([lookup[str(z)] for z in ids_tr], dtype=int)
        te_o = np.array([lookup[str(z)] for z in ids_te], dtype=int)
        if not set(tr_o).isdisjoint(set(te_o)):
            raise AssertionError('IDs de treino e teste externos se repetem')
        yy, xx = d['y'], d['x']
        origin = (float(geometrias.bounds.minx.min()),float(geometrias.bounds.miny.min())) if exp=='E2' and geometrias is not None else None
        grupos = indices_grupos(d['xy'], bloco, origin)
        if not set(grupos[tr_o]).isdisjoint(set(grupos[te_o])):
            raise AssertionError('Blocos externos se repetem')
        if tipo == 'geometrias':
            if adj is None: raise ValueError('Matriz de embargo geométrico ausente')
            if adj[np.ix_(te_o,tr_o)].any(): raise AssertionError('Embargo E2 violado')
        else:
            dist,_ = cKDTree(d['xy'][te_o]).query(d['xy'][tr_o],k=1)
            if float(dist.min()) <= 25: raise AssertionError('Embargo por pontos/centroides violado')
        inn = montar_internos(d, tr_o, bloco, tipo, adj if exp=='E2' else None, seed=20261103+rodada, origin=origin)
        scores = []
        for nome, receita, params in CANDIDATOS:
            vals, trs = [], []
            for j, (itr, ite) in enumerate(inn, 1):
                modelo = criar_modelo(nome, params)
                modelo.fit(xx[itr], yy[itr])
                ftr = f1_score(yy[itr], modelo.predict(xx[itr]), average='macro', zero_division=0)
                fte = f1_score(yy[ite], modelo.predict(xx[ite]), average='macro', zero_division=0)
                vals.append(float(fte)); trs.append(float(ftr))
                internos.append(dict(experimento=exp, bloco_m=bloco, rodada=rodada, inner_fold=j,
                                     modelo=nome, receita=receita, n_treino=len(itr), n_validacao=len(ite),
                                     f1_treino=float(ftr), f1_validacao=float(fte)))
            scores.append((float(np.mean(vals)), float(np.mean(trs)), nome, receita, params))
        # Critério pré-definido: maior F1-macro MÉDIO no conjunto de validação interna.
        # Se empatar numericamente, prioriza modelo de menor complexidade.
        simplicidade = {'Regressão logística':0, 'KNN':1, 'SVM RBF':2}
        winner = sorted(scores, key=lambda p:(-p[0], simplicidade[p[2]], p[3]))[0]
        inner_f1, inner_train_f1, nome, receita, params = winner
        modelo = criar_modelo(nome, params)
        modelo.fit(xx[tr_o], yy[tr_o])
        yp_tr, yp_te = modelo.predict(xx[tr_o]), modelo.predict(xx[te_o])
        ftr = float(f1_score(yy[tr_o], yp_tr, average='macro', zero_division=0))
        fte = float(f1_score(yy[te_o], yp_te, average='macro', zero_division=0))
        finais.append(dict(experimento=exp, bloco_m=bloco, rodada=rodada, modelo=nome,
                           receita=receita, f1_treino=ftr, f1_teste=fte, delta=ftr-fte,
                           f1_interno=inner_f1, n_treino=len(tr_o), n_teste=len(te_o),
                           f1_balanceado=float(balanced_accuracy_score(yy[te_o], yp_te))))
        for s, it, name, rec, _ in scores:
            selecoes.append(dict(experimento=exp, bloco_m=bloco, rodada=rodada,
                                 modelo=name, receita=rec, f1_validacao_interna=s,
                                 f1_treino_interno=it, escolhido=(name==nome and rec==receita)))
        print(f'{k:02d}/30 {exp} {bloco}m: escolhido {nome} / {receita} | F1 interno={inner_f1:.4f}, externo={fte:.4f}, gap={ftr-fte:+.4f}',flush=True)
    finals = pd.DataFrame(finais)
    finals.to_csv(out/'avaliacoes_externas_aninhadas.csv',index=False)
    pd.DataFrame(selecoes).to_csv(out/'selecao_apenas_treino.csv',index=False)
    pd.DataFrame(internos).to_csv(out/'avaliacoes_validacao_interna.csv',index=False)
    resumo = finals.groupby('experimento',as_index=False).agg(f1_treino=('f1_treino','mean'),
                f1_teste=('f1_teste','mean'),delta=('delta','mean'),dp_teste=('f1_teste','std'),
                folds=('rodada','size'),folds_gap_gt_005=('delta',lambda x:int((x>.05).sum())))
    resumo.to_csv(out/'resumo_aninhado.csv',index=False)
    resumo_esc = finals.groupby(['experimento','bloco_m'],as_index=False).agg(f1_treino=('f1_treino','mean'),f1_teste=('f1_teste','mean'),delta=('delta','mean'),folds=('rodada','size'))
    resumo_esc.to_csv(out/'resumo_por_escala.csv',index=False)
    (out/'manifesto.json').write_text(json.dumps({
       'protocolo':'tuning espacial interno 3 splits + teste externo já utilizado em estudos anteriores',
       'candidatos_por_rodada':len(CANDIDATOS), 'avaliacoes_internas':len(internos), 'ajustes_externos':len(finals),
       'advertencia':'Teste externo já conhecido de estudos anteriores, não é teste virgem. Overfitting não pode ser zerado ou descartado apenas por diferença de médias.'
       },ensure_ascii=False,indent=2))
    print('\nRESUMO POR EXPERIMENTO:')
    print(resumo.to_string(index=False))
    print('\nRESUMO POR ESCALA:')
    print(resumo_esc.to_string(index=False))
    return resumo


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--modo',choices=['evidencias','v2'],default='evidencias')
    p.add_argument('--entradas',type=Path)
    p.add_argument('--e2',type=Path)
    p.add_argument('--e9',type=Path)
    p.add_argument('--out',type=Path,required=True)
    a=p.parse_args()
    if a.modo=='evidencias':
        if a.entradas is None:p.error('Indique --entradas')
        data, folds, geo=carregar_evidencias(a.entradas)
    else:
        if a.e2 is None or a.e9 is None:p.error('Indique --e2 e --e9')
        data, folds, geo=carregar_v2(a.e2,a.e9)
    executar(data,folds,geo,a.out)

if __name__=='__main__':
    main()