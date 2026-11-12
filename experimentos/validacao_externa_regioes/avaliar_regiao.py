#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Avaliação EXTERNA com pontos locais independentes; nunca seleciona modelos.

Métrica por segmento rotulado único, depois de descartar referências conflitantes
na mesma segmentação. Não confundir mapas previstos sem rótulos com F1 medido.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
import geopandas as gpd
import rasterio
from sklearn.metrics import (accuracy_score, balanced_accuracy_score,
                             classification_report, confusion_matrix, f1_score)

CLASS = {1:"arvore", 2:"grama"}
EXPECTED = {"arvore", "grama"}


def read_references(tree_path: Path, grass_path: Path, crs) -> pd.DataFrame:
    pts = []
    for path, classe in [(tree_path,"arvore"), (grass_path,"grama")]:
        layer = gpd.read_file(path)
        if layer.crs is None or layer.empty:
            raise ValueError(f"Referências sem CRS ou vazias: {path}")
        if not layer.geometry.geom_type.eq("Point").all():
            raise ValueError(f"Exigem-se pontos individuais, não polígonos: {path}")
        transformed = layer.to_crs(crs)
        for idx, point in enumerate(transformed.geometry):
            if point is not None and not point.is_empty:
                pts.append({"ref_id":f"{classe}_{idx}","classe":classe,
                            "x":point.x,"y":point.y})
    if not pts:
        raise ValueError("Sem referências externas independentes.")
    return pd.DataFrame(pts)


def sample_raster(path, coords):
    with rasterio.open(path) as ds:
        return np.asarray([float(value[0]) for value in ds.sample(coords, indexes=1)],
                          dtype=float)


def run(region: str, pred_dir: Path, trees: Path, grasses: Path, output: Path,
        min_class=5):
    output.mkdir(parents=True, exist_ok=True)
    manifest = pred_dir/"manifesto_execucao.json"
    if not manifest.is_file():
        raise FileNotFoundError("Execute aplicar_regiao.py antes de avaliar.")
    info = json.loads(manifest.read_text(encoding="utf-8"))
    if info.get("estado") != "concluido" or info.get("regiao") != region:
        raise RuntimeError("Classificação incompleta ou região divergente.")
    segments = pred_dir/"segmento_id.tif"
    with rasterio.open(segments) as src:
        if src.crs is None:
            raise ValueError("Mapas sem georreferenciamento.")
        references = read_references(trees,grasses,src.crs)
    coords = list(zip(references.x, references.y))
    references["segmento_id"] = sample_raster(segments,coords).astype("uint64")
    missed = int((references.segmento_id==0).sum())
    valid = references.loc[references.segmento_id.gt(0)].copy()
    conflict = valid.groupby("segmento_id").classe.nunique()
    conflicting = set(conflict.index[conflict>1])
    no_conflicts = valid.loc[~valid.segmento_id.isin(conflicting)].copy()
    unique = no_conflicts.drop_duplicates(subset="segmento_id").reset_index(drop=True)
    counts = unique.classe.value_counts().to_dict()
    for cls in EXPECTED:
        if counts.get(cls,0) < min_class:
            raise ValueError(f"Amostras independentes da classe {cls}: {counts.get(cls,0)}. "
                             f"Mínimo definido: {min_class}. F1 externo NÃO calculado.")
    pred_paths = info["mapas"]
    if len(pred_paths) != 8:
        raise ValueError("Foram esperados oito mapas previstos.")
    # CSV por referência mostra exclusões e conflitos, sem inflar a quantidade
    # de amostras ao avaliar múltiplos pontos da MESMA região segmentada.
    references["status"] = "valido"
    references.loc[references.segmento_id.eq(0),"status"] = "fora_da_imagem_ou_sem_predicao"
    references.loc[references.segmento_id.isin(conflicting),"status"] = "segmento_com_classes_conflitantes"
    references.to_csv(output/"auditoria_referencias.csv",index=False)
    coordinates = list(zip(unique.x,unique.y))
    metrics, confusion_rows = [], []
    for name,pathstr in pred_paths.items():
        path = Path(pathstr)
        if not path.is_file():
            # Se as pastas do Drive mudarem de lugar, os resultados continuam
            # no mesmo pred_dir. O nome do arquivo é preservado no manifesto.
            path = pred_dir/Path(pathstr).name
        if not path.is_file():
            raise FileNotFoundError(f"Mapa de classificador ausente: {path}")
        with rasterio.open(path) as ds:
            if ds.crs is None:
                raise ValueError(f"Mapa sem CRS: {path}")
        predicted_codes = sample_raster(path,coordinates).astype(int)
        no_prediction = np.count_nonzero(predicted_codes==0)
        if no_prediction:
            raise ValueError(f"{name}: {no_prediction} referências sem previsão. "
                             "Corrija a cobertura antes de calcular métricas.")
        if not set(predicted_codes).issubset(CLASS):
            raise ValueError("Mapa possui códigos de classe desconhecidos.")
        y_true = unique.classe.to_numpy(dtype=str)
        y_pred = np.array([CLASS[n] for n in predicted_codes])
        macro=float(f1_score(y_true,y_pred,labels=["arvore","grama"],
                             average="macro",zero_division=0))
        metrics.append(dict(regiao=region,modelo=name,amostras=len(unique),
                            n_arvore=counts.get("arvore",0),n_grama=counts.get("grama",0),
                            f1_macro=macro,
                            acuracia=float(accuracy_score(y_true,y_pred)),
                            acuracia_balanceada=float(balanced_accuracy_score(y_true,y_pred)),
                            referencias_ignoradas_sem_segmento=missed,
                            segmentos_conflitantes_removidos=len(conflicting)))
        for i,ground in enumerate(["arvore","grama"]):
            for j,pred in enumerate(["arvore","grama"]):
                confusion_rows.append(dict(regiao=region,modelo=name,
                                           classe_real=ground,classe_prevista=pred,
                                           quantidade=int(confusion_matrix(
                                               y_true,y_pred,labels=["arvore","grama"])[i,j])))
        unique["prev_"+Path(path).stem] = y_pred
        rpt=classification_report(y_true,y_pred,labels=["arvore","grama"],
                                  zero_division=0,output_dict=True)
        (output/("relatorio_"+Path(path).stem+".json")).write_text(
            json.dumps(rpt,ensure_ascii=False,indent=2),encoding="utf-8")
    pd.DataFrame(metrics).to_csv(output/"metricas_externas.csv",index=False)
    pd.DataFrame(confusion_rows).to_csv(output/"matrizes_confusao.csv",index=False)
    unique.to_csv(output/"comparacao_por_segmento.csv",index=False)
    result=dict(regiao=region,status="VALIDACAO_EXTERNA_CONCLUIDA",
                referencias_originais=len(references),
                referencias_fora_ou_invalidas=missed,
                conflitos_segmentacao=len(conflicting),
                segmentos_unicos_avaliados=len(unique), classes=counts,
                observado_em_campo=False,
                explicacao="Pontos conhecidos nas novas regiões; nenhum destes rótulos participou do treinamento Area1.",
                advertencia="Resultados dependem da qualidade e independência dos pontos de referência externos.")
    (output/"manifesto_avaliacao.json").write_text(
        json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
    print(pd.DataFrame(metrics)[["modelo","amostras","f1_macro","acuracia_balanceada"]].to_string(index=False))
    return pd.DataFrame(metrics)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--regiao",required=True)
    p.add_argument("--predicoes",type=Path,required=True)
    p.add_argument("--arvores",type=Path,required=True)
    p.add_argument("--grama",type=Path,required=True)
    p.add_argument("--min-por-classe",type=int,default=5)
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    run(args.regiao,args.predicoes,args.arvores,args.grama,args.out,args.min_por_classe)


if __name__=="__main__":
    main()
