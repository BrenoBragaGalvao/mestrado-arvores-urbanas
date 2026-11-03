#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Reexecuta tabelas da V2 com validacao espacial aninhada por classificador.

Usa features e particoes ja derivadas da Area1. Para CADA classificador,
seleciona moderada/forte pelo F1 de validacao interna; somente depois mede F1
externo. Mantem TODOS os resultados (inclusive indicios de overfitting).
Os testes externos foram vistos em experimentos anteriores: NAO sao novos
testes cegos e NAO provam ausencia de sobreajuste.

--modo evidencias --entradas <pasta> --out <pasta>
--modo v2 --e2 <rotulos_sem_duplicacao.csv> --e9 <pasta_e9> --out <pasta>
"""
from __future__ import annotations
import argparse, json, platform
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.spatial import cKDTree
from sklearn.metrics import f1_score, accuracy_score, balanced_accuracy_score

from v2_auditoria_regularizacao import (
    carregar_evidencias, carregar_v2, criar_modelo, RECEITAS,
)
from validacao_aninhada_espacial_v2 import indices_grupos, montar_internos

MODELOS = [
    'Regressão logística', 'SVM RBF', 'KNN', 'Random Forest',
    'Extra Trees', 'HistGradientBoosting', 'Gaussian Naive Bayes', 'Dummy',
]

def executar(bases, divisoes, geometrias, destino, modo):
    destino.mkdir(parents=True, exist_ok=True)
    if len(divisoes) != 30:
        raise ValueError('Esperadas 30 divisoes externas')
    adj = None
    if geometrias is not None:
        geo = geometrias.reindex(bases['E2']['id'])
        if geo.isna().any():
            raise ValueError('Faltam geometrias E2')
        pares = geo.sindex.query(geo.buffer(25), predicate='intersects')
        adj = np.zeros((len(geo), len(geo)), dtype=bool)
        adj[pares[0], pares[1]] = True
        if not np.array_equal(adj, adj.T):
            raise ValueError('Matriz de vizinhanca espacial assimetrica')

    externos, internos, auditoria, escolhas = [], [], [], []
    for n, (exp, bloco, rodada, ids_tr, ids_te, embargo) in enumerate(divisoes, 1):
        d = bases[exp]
        ids, xy, xx, yy = d['id'], d['xy'], d['x'], d['y']
        idx = {str(x): i for i, x in enumerate(ids)}
        tr = np.array([idx[str(x)] for x in ids_tr], dtype=int)
        te = np.array([idx[str(x)] for x in ids_te], dtype=int)
        if not set(tr).isdisjoint(set(te)):
            raise AssertionError('IDs em treino e teste externo')
        origin = (
            (float(geometrias.bounds.minx.min()),
             float(geometrias.bounds.miny.min()))
            if exp == 'E2' and geometrias is not None else None
        )
        grupos = indices_grupos(xy, bloco, origin)
        if not set(grupos[tr]).isdisjoint(set(grupos[te])):
            raise AssertionError('Blocos compartilhados entre treino e teste')
        if embargo == 'geometrias':
            if adj is None or adj[np.ix_(te, tr)].any():
                raise AssertionError('Embargo E2 por geometrias violado')
            menor_dist = np.nan
        else:
            menor_dist = float(cKDTree(xy[te]).query(xy[tr], k=1)[0].min())
            if menor_dist <= 25:
                raise AssertionError('Embargo por pontos/centroides violado')

        folds_internos = montar_internos(
            d, tr, bloco, embargo, adj if exp == 'E2' else None,
            seed=20261103 + rodada, origin=origin,
        )
        auditoria.append(dict(
            experimento=exp, bloco_m=bloco, rodada=rodada,
            n_treino=len(tr), n_teste=len(te), ids_compartilhados=0,
            blocos_compartilhados=0, embargo=embargo,
            distancia_minima_m=menor_dist,
            divisoes_internas_validas=len(folds_internos),
        ))
        for nome in MODELOS:
            receitas = ['moderada'] if nome == 'Dummy' else ['forte', 'moderada']
            candidatas = []
            for receita in receitas:
                params = RECEITAS[receita][nome]
                f1_vals = []
                for fold, (ti, vi) in enumerate(folds_internos, 1):
                    mdl = criar_modelo(nome, params)
                    mdl.fit(xx[ti], yy[ti])
                    f1_tr = float(f1_score(
                        yy[ti], mdl.predict(xx[ti]),
                        average='macro', zero_division=0,
                    ))
                    f1_val = float(f1_score(
                        yy[vi], mdl.predict(xx[vi]),
                        average='macro', zero_division=0,
                    ))
                    f1_vals.append(f1_val)
                    internos.append(dict(
                        experimento=exp, bloco_m=bloco, rodada=rodada,
                        modelo=nome, receita=receita, fold_interno=fold,
                        n_treino=len(ti), n_validacao=len(vi),
                        f1_treino=f1_tr, f1_validacao=f1_val,
                    ))
                candidatas.append((float(np.mean(f1_vals)), receita, params))
            # Seleciona SO com validacao interna; empate favorece regularizacao forte.
            vencedora = sorted(
                candidatas, key=lambda s: (-s[0], 0 if s[1] == 'forte' else 1)
            )[0]
            for f1_val, receita, _ in candidatas:
                escolhas.append(dict(
                    experimento=exp, bloco_m=bloco, rodada=rodada,
                    modelo=nome, receita=receita,
                    f1_validacao_interna=f1_val,
                    escolhida=receita == vencedora[1],
                ))
            mdl = criar_modelo(nome, vencedora[2])
            mdl.fit(xx[tr], yy[tr])
            pred_tr, pred_te = mdl.predict(xx[tr]), mdl.predict(xx[te])
            f1_tr = float(f1_score(
                yy[tr], pred_tr, average='macro', zero_division=0,
            ))
            f1_te = float(f1_score(
                yy[te], pred_te, average='macro', zero_division=0,
            ))
            externos.append(dict(
                experimento=exp, bloco_m=bloco, rodada=rodada,
                modelo=nome, receita=vencedora[1],
                parametros=json.dumps(vencedora[2], sort_keys=True),
                f1_validacao_interna=vencedora[0],
                f1_treino=f1_tr, f1_teste=f1_te,
                diferenca_treino_teste=f1_tr - f1_te,
                acuracia_teste=float(accuracy_score(yy[te], pred_te)),
                acuracia_balanceada_teste=float(
                    balanced_accuracy_score(yy[te], pred_te)
                ), n_treino=len(tr), n_teste=len(te),
            ))
        print(f'{n:02d}/30 {exp} {bloco}m rodada {rodada}: OK', flush=True)

    ext = pd.DataFrame(externos)
    ext.to_csv(destino / 'avaliacoes_externas_8_modelos.csv', index=False)
    pd.DataFrame(internos).to_csv(
        destino / 'avaliacoes_internas_8_modelos.csv', index=False
    )
    pd.DataFrame(auditoria).to_csv(destino / 'auditoria_particoes.csv', index=False)
    pd.DataFrame(escolhas).to_csv(
        destino / 'parametros_escolhidos_apenas_treino.csv', index=False
    )
    por_escala = ext.groupby(
        ['experimento', 'bloco_m', 'modelo'], as_index=False
    ).agg(
        f1_treino=('f1_treino', 'mean'),
        f1_teste=('f1_teste', 'mean'),
        delta=('diferenca_treino_teste', 'mean'),
        desvio_f1_teste=('f1_teste', 'std'),
        folds=('rodada', 'size'),
        divisao_sobreajuste_gap_005=(
            'diferenca_treino_teste', lambda x: int((x > .05).sum())
        ),
    )
    por_escala.to_csv(destino / 'tabelas_readme_3_6.csv', index=False)
    por_modelo = ext.groupby(
        ['experimento', 'modelo'], as_index=False
    ).agg(
        f1_treino=('f1_treino', 'mean'),
        f1_teste=('f1_teste', 'mean'),
        delta=('diferenca_treino_teste', 'mean'),
        folds=('rodada', 'size'),
        divisao_sobreajuste_gap_005=(
            'diferenca_treino_teste', lambda x: int((x > .05).sum())
        ),
    )
    por_modelo.to_csv(destino / 'resumo_sobreajuste_por_modelo.csv', index=False)
    manifesto = dict(
        modo=modo, dados='Area1 derivada, 505 exemplos por configuracao',
        folds_externos=len(divisoes), avaliacoes_externas=len(ext),
        ajustes_validacao_interna=len(internos), ids_compartilhados=0,
        receitas=['moderada','forte'],
        embargo_E2='geometrias' if modo=='evidencias' else 'centroides',
        embargo_E3A_E3B='pontos',
        limite='Teste externo reutilizado; ausencia de overfitting NAO comprovada',
        python=platform.python_version(),
        sklearn=__import__('sklearn').__version__,
    )
    (destino / 'manifesto.json').write_text(
        json.dumps(manifesto, ensure_ascii=False, indent=2), encoding='utf-8'
    )
    if len(ext) != 240 or len(internos) != 1350 or len(por_escala) != 48:
        raise AssertionError('Quantidade de avaliacoes inesperada')
    print(por_escala.round(4).to_string(index=False))
    return por_escala

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--modo', choices=['evidencias','v2'], default='evidencias')
    p.add_argument('--entradas', type=Path)
    p.add_argument('--e2', type=Path)
    p.add_argument('--e9', type=Path)
    p.add_argument('--out', required=True, type=Path)
    a = p.parse_args()
    if a.modo == 'evidencias':
        if a.entradas is None:
            p.error('--entradas obrigatorio')
        bases, divisoes, geo = carregar_evidencias(a.entradas)
    else:
        if a.e2 is None or a.e9 is None:
            p.error('--e2 e --e9 obrigatorios')
        bases, divisoes, geo = carregar_v2(a.e2, a.e9)
    executar(bases, divisoes, geo, a.out, a.modo)

if __name__ == '__main__':
    main()
