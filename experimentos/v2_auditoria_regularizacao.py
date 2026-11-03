#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Auditoria de regularizacao E2 / E3A / E3B para a V2 do mestrado.

Modos:
  --modo v2: reexecuta sobre as saidas produzidas no Colab pelo notebook V2;
             o embargo de E2 e por CENTROIDES, nao por geometrias.
  --modo evidencias: reproduz as 30 particoes de 03/11/2026 com os quatro
             arquivos originais de entradas do pacote de evidencias, inclusive
             o geopackage de GEOMETRIAS de E2. Nao e um teste externo novo.

NUNCA altere as metricas historicas nem selecione a melhor receita pelo teste.
"""
from __future__ import annotations
import argparse
import json
import platform
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.spatial import cKDTree
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import ExtraTreesClassifier, HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, balanced_accuracy_score, f1_score
from sklearn.model_selection import GroupShuffleSplit
from sklearn.naive_bayes import GaussianNB
from sklearn.neighbors import KNeighborsClassifier
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC

FEATURES = ['mean_intensity', 'mean_edges', 'mean_ndvi']
RECEITAS = {
    'moderada': {
        'Random Forest': dict(n_estimators=100, max_depth=4, min_samples_leaf=15, max_features=1.0),
        'Extra Trees': dict(n_estimators=100, max_depth=4, min_samples_leaf=15, max_features=1.0),
        'HistGradientBoosting': dict(max_leaf_nodes=3, max_iter=60, learning_rate=.05, min_samples_leaf=30, l2_regularization=5.),
        'SVM RBF': dict(C=.2), 'Regressão logística': dict(C=.1),
        'KNN': dict(n_neighbors=25), 'Gaussian Naive Bayes': dict(var_smoothing=1e-3),
        'Dummy': dict(strategy='most_frequent')},
    'forte': {
        'Random Forest': dict(n_estimators=100, max_depth=2, min_samples_leaf=30, max_features=1.0),
        'Extra Trees': dict(n_estimators=100, max_depth=2, min_samples_leaf=30, max_features=1.0),
        'HistGradientBoosting': dict(max_leaf_nodes=2, max_iter=40, learning_rate=.04, min_samples_leaf=40, l2_regularization=10.),
        'SVM RBF': dict(C=.05), 'Regressão logística': dict(C=.02),
        'KNN': dict(n_neighbors=35), 'Gaussian Naive Bayes': dict(var_smoothing=1e-2),
        'Dummy': dict(strategy='most_frequent')},
}


def criar_modelo(nome, p):
    if nome == 'Random Forest':
        return RandomForestClassifier(random_state=42, n_jobs=1, **p)
    if nome == 'Extra Trees':
        return ExtraTreesClassifier(random_state=42, n_jobs=1, **p)
    if nome == 'HistGradientBoosting':
        return HistGradientBoostingClassifier(random_state=42, **p)
    if nome == 'SVM RBF':
        return make_pipeline(StandardScaler(), SVC(kernel='rbf', gamma='scale', **p))
    if nome == 'Regressão logística':
        return make_pipeline(StandardScaler(), LogisticRegression(max_iter=3000, random_state=42, **p))
    if nome == 'KNN':
        return make_pipeline(StandardScaler(), KNeighborsClassifier(**p))
    if nome == 'Gaussian Naive Bayes':
        return GaussianNB(**p)
    return DummyClassifier(**p)


def preparar_base(frame, id_col, cols=FEATURES, x='x', y='y'):
    requerido = [id_col, 'classe', x, y, *cols]
    faltam = [k for k in requerido if k not in frame.columns]
    if faltam:
        raise ValueError('Colunas ausentes: ' + ', '.join(faltam))
    if frame[id_col].duplicated().any():
        raise ValueError('IDs duplicados em ' + id_col)
    xmat = frame[list(cols)].to_numpy(float)
    xy = frame[[x, y]].to_numpy(float)
    if not np.isfinite(xmat).all() or not np.isfinite(xy).all():
        raise ValueError('Caracteristicas/coordenadas invalidas')
    result = {'id': frame[id_col].astype(str).to_numpy(), 'y': frame.classe.astype(str).to_numpy(), 'x': xmat, 'xy': xy}
    if len(result['id']) < 30 or len(set(result['y'])) != 2:
        raise ValueError('Base supervisionada insuficiente')
    return result


def carregar_v2(e2_path, e9_dir):
    e2 = pd.read_csv(e2_path)
    a = preparar_base(e2, 'id')
    b512 = pd.read_csv(e9_dir / 'amostras_comuns_512.csv')
    b256 = pd.read_csv(e9_dir / 'amostras_comuns_256.csv')
    if set(b512.point_id) != set(b256.point_id):
        raise ValueError('E9 nao possui os mesmos IDs nos dois bracos')
    b512 = b512.sort_values('point_id').reset_index(drop=True)
    b256 = b256.sort_values('point_id').reset_index(drop=True)
    if not np.array_equal(b512.classe, b256.classe):
        raise ValueError('E9 possui classes divergentes')
    base = {'E2': a, 'E3A': preparar_base(b512, 'point_id'), 'E3B': preparar_base(b256, 'point_id')}
    divisoes = []
    # E2 usa centroides exportados pela rota progressiva atual da V2.
    xy = a['xy']; y = a['y']
    for tam in (250, 500):
        gx = np.floor((xy[:, 0] - xy[:, 0].min()) / tam).astype(int)
        gy = np.floor((xy[:, 1] - xy[:, 1].min()) / tam).astype(int)
        grupos = np.array([f'{xx}_{yy}' for xx, yy in zip(gx, gy)])
        for rodada, (tr, te) in enumerate(GroupShuffleSplit(n_splits=5, test_size=.2, random_state=42).split(xy, y, grupos), 1):
            dist, _ = cKDTree(xy[te]).query(xy[tr], k=1)
            tr = tr[dist > 25]
            divisoes.append(('E2', tam, rodada, a['id'][tr].tolist(), a['id'][te].tolist(), 'centroides'))
    e9_split = pd.read_csv(e9_dir / 'particoes_identicas.csv')
    e9_split = e9_split.loc[e9_split['embargo_pontos_m'].eq(25)]
    if len(e9_split) != 10:
        raise ValueError('A comparacao E9 precisa de dez divisoes com embargo de 25 m')
    for row in e9_split.itertuples(index=False):
        treino = str(row.ids_treino).split(';')
        teste = str(row.ids_teste).split(';')
        for exp in ('E3A', 'E3B'):
            divisoes.append((exp, int(row.bloco_m), int(row.rodada), treino, teste, 'pontos'))
    return base, divisoes, None


def carregar_evidencias(pasta):
    import geopandas as gpd
    a = pd.read_csv(pasta / 'E3c_base_rotulada_812.csv')
    geo = gpd.read_file(pasta / 'E3c_geometrias_rotuladas_812.gpkg')
    if geo.crs is None or not geo.crs.is_projected:
        raise ValueError('E2 exige CRS metrico projetado')
    a = gpd.GeoDataFrame(a.merge(geo, on='segmento_id', validate='one_to_one'), geometry='geometry', crs=geo.crs)
    a['x'] = a.geometry.centroid.x
    a['y'] = a.geometry.centroid.y
    b = pd.read_csv(pasta / 'amostras_comuns.csv')
    if len(a) != 505 or len(b) != 505:
        raise ValueError('O pacote de evidencias deve conter 505 observacoes por base')
    bases = {'E2': preparar_base(a, 'segmento_id')}
    for exp, sufixo in [('E3A', 'cont'), ('E3B', 'quad')]:
        frame = b[['point_id', 'classe', 'x', 'y', *[f'{f}_{sufixo}' for f in FEATURES]]].copy()
        frame.columns = ['point_id', 'classe', 'x', 'y', *FEATURES]
        bases[exp] = preparar_base(frame, 'point_id')
    splits = pd.read_csv(pasta / 'particoes_auditadas.csv')
    divisoes = []
    for row in splits.itertuples(index=False):
        exp = str(row.experimento).split(' — ')[0]
        divisoes.append((exp, int(row.bloco_m), int(row.rodada), str(row.ids_treino).split(';'), str(row.ids_teste).split(';'), 'geometrias' if exp == 'E2' else 'pontos'))
    return bases, divisoes, a.set_index(a.segmento_id.astype(str)).geometry


def executar(bases, divisoes, geometrias, out, modo):
    out.mkdir(parents=True, exist_ok=True)
    if len(divisoes) != 30:
        raise ValueError(f'Esperadas 30 divisoes, obtidas {len(divisoes)}')
    linhas, aud = [], []
    for i, (exp, tam, rodada, ids_tr, ids_te, embargo) in enumerate(divisoes, 1):
        d = bases[exp]
        look = {key: j for j, key in enumerate(d['id'])}
        if len(look) != len(d['id']):
            raise AssertionError('IDs duplicados')
        tr = np.array([look[z] for z in ids_tr], dtype=int)
        te = np.array([look[z] for z in ids_te], dtype=int)
        if not set(tr).isdisjoint(te):
            raise AssertionError('Vazamento direto de IDs de treino/teste')
        if len(tr) < 15 or len(te) < 7 or len(set(d['y'][tr])) < 2 or len(set(d['y'][te])) < 2:
            raise ValueError(f'Divisao invalida em {exp} / {tam} / {rodada}')
        # O embargo de E2 no modo evidencias e por GEOMETRIAS;
        # no modo V2 e por CENTROIDES. Nao apresentar como equivalentes.
        if embargo == 'geometrias':
            if geometrias is None:
                raise ValueError('Geometrias ausentes')
            teste = geometrias.loc[ids_te]
            unido = teste.buffer(25).union_all()
            if geometrias.loc[ids_tr].intersects(unido).any():
                raise AssertionError('Embargo geometrico E2 violado')
            menor_dist = None
        else:
            menor_dist = float(cKDTree(d['xy'][te]).query(d['xy'][tr], k=1)[0].min())
            if menor_dist <= 25:
                raise AssertionError(f'Embargo entre {embargo} nao respeitado: {menor_dist}')
        aud.append(dict(experimento=exp, bloco_m=tam, rodada=rodada, n_treino=len(tr), n_teste=len(te),
                        ids_sobrepostos=0, tipo_embargo=embargo, distancia_minima_m=menor_dist, embargo_verificado=True))
        for receita, configuracao in RECEITAS.items():
            for nome, params in configuracao.items():
                mdl = criar_modelo(nome, params)
                mdl.fit(d['x'][tr], d['y'][tr])
                pred_tr, pred_te = mdl.predict(d['x'][tr]), mdl.predict(d['x'][te])
                ftr = float(f1_score(d['y'][tr], pred_tr, average='macro', zero_division=0))
                fte = float(f1_score(d['y'][te], pred_te, average='macro', zero_division=0))
                linhas.append(dict(experimento=exp, bloco_m=tam, rodada=rodada, receita=receita, modelo=nome,
                                   f1_treino=ftr, f1_teste=fte, delta=ftr-fte,
                                   acuracia_teste=float(accuracy_score(d['y'][te], pred_te)),
                                   acuracia_balanceada_teste=float(balanced_accuracy_score(d['y'][te], pred_te)),
                                   n_treino=len(tr), n_teste=len(te), parametros=json.dumps(params, sort_keys=True)))
        print(f'[{i}/30] {exp} | {tam} m | rodada {rodada} | embargo {embargo}', flush=True)
    resultados = pd.DataFrame(linhas)
    assert len(resultados) == 480 and len(aud) == 30
    resultados.to_csv(out / 'avaliacoes_480_ajustes.csv', index=False)
    pd.DataFrame(aud).to_csv(out / 'auditoria_particoes.csv', index=False)
    agrupamento = ['experimento', 'receita', 'modelo']
    resumo = resultados.groupby(agrupamento, as_index=False).agg(
        f1_treino=('f1_treino', 'mean'), f1_teste=('f1_teste', 'mean'),
        delta=('delta', 'mean'), dp_f1_teste=('f1_teste', 'std'), folds=('rodada', 'size'),
        folds_delta_maior_005=('delta', lambda s: int((s > .05).sum())))
    resumo.to_csv(out / 'resumo_todos_modelos.csv', index=False)
    por_escala = resultados.groupby(['experimento','bloco_m','receita','modelo'],as_index=False).agg(
        f1_treino=('f1_treino','mean'),f1_teste=('f1_teste','mean'),
        delta=('delta','mean'),folds=('rodada','size'))
    por_escala.to_csv(out / 'resumo_por_escala.csv', index=False)
    manifesto = dict(modo=modo, origem='Area1', particoes=30, ajustes=480,
        ids_sobrepostos=0, classificadores=8, receitas=list(RECEITAS),
        embargo_E2='geometrias' if modo=='evidencias' else 'centroides',
        embargo_E3A_E3B='pontos',
        ressalva='Validacao interna na mesma AOI; diferenca pequena nao prova ausencia de overfitting.',
        versoes=dict(python=platform.python_version(), sklearn=__import__('sklearn').__version__))
    (out/'manifesto.json').write_text(json.dumps(manifesto, indent=2, ensure_ascii=False), encoding='utf-8')
    print('\nResultados completos: ', out)
    print(resumo[['experimento','receita','modelo','f1_treino','f1_teste','delta']].round(4).to_string(index=False))
    return resumo


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--modo', choices=['v2','evidencias'], default='v2')
    p.add_argument('--e2', type=Path, help='Caminho para rotulos_sem_duplicacao.csv da V2')
    p.add_argument('--e9', type=Path, help='Pasta E9 contendo amostras_comuns_512/256.csv e particoes_identicas.csv')
    p.add_argument('--entradas', type=Path, help='Pasta entradas/ do pacote de evidencias de 03/11/2026')
    p.add_argument('--out', type=Path, required=True)
    args = p.parse_args()
    if args.modo == 'evidencias':
        if args.entradas is None:
            p.error('--entradas obrigatorio no modo evidencias')
        bases, divisoes, geometria = carregar_evidencias(args.entradas)
    else:
        if args.e2 is None or args.e9 is None:
            p.error('--e2 e --e9 obrigatorios no modo v2')
        bases, divisoes, geometria = carregar_v2(args.e2, args.e9)
    executar(bases, divisoes, geometria, args.out, args.modo)


if __name__ == '__main__':
    main()
