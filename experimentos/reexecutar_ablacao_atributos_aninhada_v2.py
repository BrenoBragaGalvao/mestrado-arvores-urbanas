#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""E4b aninhado: duas combinacoes de atributos, mesmos folds da secao 3.6.1.

Escolhe regularizacao somente no treino externo e mede F1 no teste sem usá-lo
para escolha. E2 no modo evidencias usa embargo GEOMETRICO; --modo v2 usa
CENTROIDES e nao reproduz as mesmas tabelas. Uma Area1 nao valida generalizacao.
"""
from __future__ import annotations
import argparse, json
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.spatial import cKDTree
from sklearn.metrics import f1_score
from v2_auditoria_regularizacao import carregar_evidencias, carregar_v2, criar_modelo, RECEITAS
from validacao_aninhada_espacial_v2 import indices_grupos, montar_internos

MODELOS=['Regressão logística','SVM RBF','KNN','Random Forest','Extra Trees',
        'HistGradientBoosting','Gaussian Naive Bayes','Dummy']
COMBOS={'HSV + Canny':[0,1], 'NDVI + HSV + Canny':[0,1,2]}


def executar(bases, splits, geometrias, out, modo, conferir=None):
    out.mkdir(parents=True,exist_ok=True)
    folds=[s for s in splits if s[0]=='E2']
    if len(folds)!=10:raise ValueError('E2 precisa de 10 particoes espaciais')
    d=bases['E2']; ids=d['id']; y=d['y']; x=d['x']; xy=d['xy']
    lookup={str(z):j for j,z in enumerate(ids)}
    if len(lookup)!=len(ids):raise AssertionError('Duplicacoes de IDs')
    adj=None; origin=None
    if geometrias is not None:
        geo=geometrias.reindex(ids)
        if geo.isna().any():raise ValueError('Falta geometria')
        pairs=geo.sindex.query(geo.buffer(25),predicate='intersects')
        adj=np.zeros((len(geo),len(geo)),dtype=bool)
        adj[pairs[0],pairs[1]]=True
        if not np.array_equal(adj,adj.T):raise ValueError('Matriz geometrica nao simetrica')
        origin=(float(geometrias.bounds.minx.min()),float(geometrias.bounds.miny.min()))
    ext=[]; internal=[]; selected=[]; checks=[]
    for i,(exp,block,round_id,tr_ids,te_ids,kind) in enumerate(folds,1):
        tr=np.array([lookup[str(z)] for z in tr_ids],dtype=int)
        te=np.array([lookup[str(z)] for z in te_ids],dtype=int)
        if len(set(tr))!=len(tr) or len(set(te))!=len(te) or not set(tr).isdisjoint(te):
            raise AssertionError('Vazamento de IDs')
        group=indices_grupos(xy,block,origin)
        if not set(group[tr]).isdisjoint(set(group[te])):raise AssertionError('Blocos compartilhados')
        if kind=='geometrias':
            if adj is None or adj[np.ix_(te,tr)].any():raise AssertionError('Embargo geometrico violado')
        else:
            if float(cKDTree(xy[te]).query(xy[tr],k=1)[0].min())<=25:
                raise AssertionError('Embargo por centroides violado')
        inn=montar_internos(d,tr,block,kind,adj,seed=20261103+round_id,origin=origin)
        checks.append(dict(bloco_m=block,rodada=round_id,n_treino=len(tr),n_teste=len(te),
                           ids_compartilhados=0,blocos_compartilhados=0,embargo=kind,
                           n_validacoes_internas=len(inn)))
        for attr,features in COMBOS.items():
            X=x[:,features]
            for name in MODELOS:
                recipes=['moderada'] if name=='Dummy' else ['forte','moderada']
                candidates=[]
                for recipe in recipes:
                    params=RECEITAS[recipe][name]
                    vals=[]
                    for j,(ti,vi) in enumerate(inn,1):
                        model=criar_modelo(name,params)
                        model.fit(X[ti],y[ti])
                        ftrain=float(f1_score(y[ti],model.predict(X[ti]),average='macro',zero_division=0))
                        fvalid=float(f1_score(y[vi],model.predict(X[vi]),average='macro',zero_division=0))
                        vals.append(fvalid)
                        internal.append(dict(bloco_m=block,rodada=round_id,atributos=attr,
                                             modelo=name,receita=recipe,fold_interno=j,
                                             n_treino=len(ti),n_validacao=len(vi),
                                             f1_treino=ftrain,f1_validacao=fvalid))
                    candidates.append((float(np.mean(vals)),recipe,params))
                # Criterio IDENTICO ao da nova secao 3.6.1.
                winner=sorted(candidates,key=lambda v:(-v[0],0 if v[1]=='forte' else 1))[0]
                for f,recipe,params in candidates:
                    selected.append(dict(bloco_m=block,rodada=round_id,atributos=attr,
                                         modelo=name,receita=recipe,f1_validacao_interna=f,
                                         escolhida=(recipe==winner[1])))
                m=criar_modelo(name,winner[2]);m.fit(X[tr],y[tr])
                ftr=float(f1_score(y[tr],m.predict(X[tr]),average='macro',zero_division=0))
                fte=float(f1_score(y[te],m.predict(X[te]),average='macro',zero_division=0))
                ext.append(dict(bloco_m=block,rodada=round_id,atributos=attr,modelo=name,
                                receita=winner[1],parametros=json.dumps(winner[2],sort_keys=True),
                                f1_interno=winner[0],f1_treino=ftr,f1_teste=fte,gap=ftr-fte,
                                n_treino=len(tr),n_teste=len(te)))
        print(f'[{i}/10] E2 {block} m rodada {round_id} completo, {len(inn)} folds internos',flush=True)
    ext=pd.DataFrame(ext);inn=pd.DataFrame(internal)
    ext.to_csv(out/'avaliacoes_externas_e4b.csv',index=False)
    inn.to_csv(out/'avaliacoes_internas_e4b.csv',index=False)
    pd.DataFrame(selected).to_csv(out/'receitas_selecionadas_e4b.csv',index=False)
    pd.DataFrame(checks).to_csv(out/'auditoria_particoes_e4b.csv',index=False)
    summary=ext.groupby(['bloco_m','atributos','modelo'],as_index=False).agg(
        f1_treino=('f1_treino','mean'),f1_teste=('f1_teste','mean'),
        gap=('gap','mean'),dp_teste=('f1_teste','std'),folds=('rodada','size'),
        folds_gap_005=('gap',lambda v:int((v>0.05).sum())))
    summary.to_csv(out/'resumo_atributos_e4b.csv',index=False)
    table=summary.pivot(index=['bloco_m','modelo'],columns='atributos',values='f1_teste').reset_index()
    table['ganho_ao_acrescentar_ndvi']=table['NDVI + HSV + Canny']-table['HSV + Canny']
    table=table.sort_values(['bloco_m','NDVI + HSV + Canny'],ascending=[True,False])
    table.to_csv(out/'tabelas_readme_secao_3_5.csv',index=False)
    if conferir is not None:
        previous=pd.read_csv(conferir)
        previous=previous[previous.experimento.eq('E2')]
        current=summary[summary.atributos.eq('NDVI + HSV + Canny')]
        m=current.merge(previous,on=['bloco_m','modelo'],validate='one_to_one',suffixes=('_atual','_publicado'))
        if len(m)!=16:raise AssertionError('Nao ha 16 comparacoes E2')
        diff=float((m.f1_teste_atual-m.f1_teste_publicado).abs().max())
        if diff>1e-10:raise AssertionError(f'Falhou consistencia com 3.6.1: {diff}')
        print('CONFERIDO: todos os 16 F1 do braço triplo batem exatamente com a secao 3.6.1; diferença=',diff,flush=True)
    manifest=dict(modo=modo,amostras=len(ids),classificadores=8,
                  combinacoes=list(COMBOS),folds_externos=len(folds),
                  avaliacoes_internas=len(internal),avaliacoes_externas=len(ext),
                  tipo_embargo='geometrias' if modo=='evidencias' else 'centroides',
                  ressalva='Dados externos reutilizados, sem garantia de ausencia de overfitting; mesma Area1',
                  sklearn=__import__('sklearn').__version__)
    (out/'manifesto.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    print('\nNOVOS F1 E4b:\n'+table.round(4).to_string(index=False),flush=True)
    return table


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--modo',choices=['evidencias','v2'],default='evidencias')
    p.add_argument('--entradas',type=Path)
    p.add_argument('--e2',type=Path);p.add_argument('--e9',type=Path)
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--conferir-3-6-1',type=Path)
    a=p.parse_args()
    if a.modo=='evidencias':
        if a.entradas is None:p.error('Passe --entradas')
        bases,splits,geo=carregar_evidencias(a.entradas)
    else:
        if a.e2 is None or a.e9 is None:p.error('Passe --e2 e --e9')
        bases,splits,geo=carregar_v2(a.e2,a.e9)
    executar(bases,splits,geo,a.out,a.modo,a.conferir_3_6_1)

if __name__=='__main__':main()