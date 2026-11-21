#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Ponto de entrada auditável para a próxima etapa REAL da Proposta 1.

Reconstrói os 505 segmentos rotulados a partir dos 510 pontos originais da
Area1, escolhe e treina os oito classificadores SEM utilizar regiões externas,
e realiza nova avaliação espacial aninhada 5x2 (250/500m; embargo geométrico
25m). Requer os rasters e GeoPackages PRIVADOS no Google Drive montado.

Não publica os dados originais nem altera o README ou resultados históricos.
As métricas internas da Area1 NÃO são medidas de generalização geográfica.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import geopandas as gpd
import joblib
import pandas as pd
import rasterio

from extrair_base_area1 import run as reconstruct
from treinar_area1 import read_training_data, read_geometry, run as train
from validar_area1_aninhada import evaluate

REQUIRED_FILES=(
    "AOI_RGB_NEW.tif", "AOI_NEW_MULTI.tif", "AOI_new.shp",
    "AOI_new.shx", "AOI_new.dbf", "AOI_new.prj",
    "Arvores.gpkg", "Grama.gpkg",
)
CLASSIFIER_FILES=(
    "random_forest.joblib", "svm_rbf.joblib", "regressao_logistica.joblib",
    "extra_trees.joblib", "knn.joblib", "hist_gradient_boosting.joblib",
    "gaussian_naive_bayes.joblib", "dummy.joblib",
)


def audit_source(area1: Path) -> dict:
    """Confere existência, geometria, contagem de rótulos e grade sem editar."""
    missing=[name for name in REQUIRED_FILES if not (area1/name).is_file()]
    if missing:
        raise FileNotFoundError(
            f"Faltam arquivos originais em {area1}: {', '.join(missing)}")
    with rasterio.open(area1/"AOI_RGB_NEW.tif") as rgb, \
         rasterio.open(area1/"AOI_NEW_MULTI.tif") as multi:
        if rgb.count<3 or multi.count<4:
            raise ValueError("Bandas insuficientes para RGB + NIR na Area1.")
        if rgb.crs is None or not rgb.crs.is_projected:
            raise ValueError("RGB original sem CRS projetado.")
        if multi.crs!=rgb.crs or rgb.shape!=multi.shape:
            raise ValueError("Rasters Area1 devem compartilhar dimensões e CRS.")
        raster_info=dict(
            rgb_pixels=list(rgb.shape),rgb_bandas=rgb.count,
            multiespectral_bandas=multi.count,crs=str(rgb.crs),
            grade_geotransformacao_identica=rgb.transform.almost_equals(multi.transform),
            resolucao_rgb=list(rgb.res),resolucao_multiespectral=list(multi.res))
        # A diferença de transform no notebook original deve ser registrada,
        # não corrigida silenciosamente durante reconstrução do histórico.
    labels={}
    for filename,classe,expected in (
        ("Arvores.gpkg","arvore",257),
        ("Grama.gpkg","grama",253)):
        ref=gpd.read_file(area1/filename)
        if ref.crs is None or not ref.geometry.geom_type.eq("Point").all():
            raise ValueError(f"Referências inválidas ou sem CRS: {filename}")
        if len(ref)!=expected:
            raise ValueError(
                f"Esperados {expected} pontos de {classe}; encontrados {len(ref)}.")
        labels[classe]=len(ref)
    aoi=gpd.read_file(area1/"AOI_new.shp")
    if aoi.empty or aoi.crs is None:
        raise ValueError("AOI_new.shp ausente ou sem geometria/CRS.")
    summary={
        "dados":"Area1: arquivos reais originais sob Drive privado",
        "quantidades_referencia":labels,
        "total_pontos_referencia":sum(labels.values()),
        "raster":raster_info,
        "aoi_crs":str(aoi.crs),"aoi_geometrias":len(aoi),
        "fonte":{f:{"bytes":(area1/f).stat().st_size}
                 for f in REQUIRED_FILES},
        "protecao":"Sem cópia dos rasters nem pontos individuais para o GitHub."
    }
    return summary


def sha256_file(path: Path) -> str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(2*1024*1024),b""):
            h.update(chunk)
    return h.hexdigest()


def verify_models(models: Path, csv_sha:str)->dict:
    path=models/"manifesto_modelos.json"
    if not path.is_file():
        raise FileNotFoundError("Treinamento incompleto: manifesto não foi produzido.")
    meta=json.loads(path.read_text(encoding="utf-8"))
    if meta.get("base_area1_sha256")!=csv_sha:
        raise ValueError("Modelos salvos foram treinados com CSV diferente.")
    if len(meta.get("modelos",{}))!=8:
        raise ValueError("Manifesto não registra oito classificadores.")
    for filename in CLASSIFIER_FILES:
        p=models/filename
        if not p.is_file() or p.stat().st_size==0:
            raise FileNotFoundError(f"Classificador ausente ou vazio: {filename}")
    if meta.get("validacao",{}).get("tipo_embargo")!="geometrias":
        raise ValueError("Embargo original requerido: use geometrias de segmentos.")
    return meta


def run_pipeline(area1:Path, output:Path, only_audit:bool=False,
                 run_nested:bool=True)->dict:
    area1=area1.expanduser().resolve()
    output=output.expanduser().resolve()
    if area1 == output or area1 in output.parents:
        raise ValueError("A saída não pode estar dentro da pasta de entrada Area1.")
    output.mkdir(parents=True,exist_ok=True)
    original=audit_source(area1)
    (output/"auditoria_arquivos_area1.json").write_text(
        json.dumps(original,ensure_ascii=False,indent=2),encoding="utf-8")
    if only_audit:
        print("AUDITORIA DOS DADOS REAIS OK: 257 árvores + 253 gramíneas.")
        return {"estado":"auditoria_concluida","originais":original}

    start=time.monotonic()
    base=output/"base_rotulada_505"
    csv=base/"rotulos_sem_duplicacao.csv"
    geo=base/"E3c_geometrias_rotuladas_812.gpkg"
    if not csv.is_file() or not geo.is_file():
        resume=(base/"assinatura_reconstrucao.json").is_file()
        print("Reconstruindo 505 segmentos rotulados com Quickshift...",
              "retomada" if resume else "primeira execução",flush=True)
        reconstruct(area1,base,expect=505,resume=resume)
    if not csv.is_file() or not geo.is_file():
        raise RuntimeError("Base rotulada ou geometria não foram confirmadas.")
    frame=read_training_data(csv)
    if len(frame)!=505:
        raise ValueError(f"São esperados 505 segmentos; encontrados {len(frame)}.")
    geometries=read_geometry(geo,frame)
    if len(geometries)!=505:
        raise ValueError("Polígonos da Area1 não correspondem aos 505 segmentos.")
    csv_hash=sha256_file(csv)

    models=output/"modelos_fixos_area1"
    model_manifest=models/"manifesto_modelos.json"
    if model_manifest.is_file():
        print("Modelos já existentes: conferindo correspondência do CSV.",flush=True)
        model_metadata=verify_models(models,csv_hash)
    else:
        print("Selecionando regularização por validação espacial interna e treinando os 8 modelos...",flush=True)
        train(csv,models,geo_path=geo,allow_centroid=False)
        model_metadata=verify_models(models,csv_hash)

    validation=output/"validacao_aninhada_area1"
    nested_done=validation/"metodologia_area1_aninhada.json"
    if run_nested:
        if not nested_done.is_file():
            print("Executando 5 divisões externas × 2 escalas com 3 divisões internas...",flush=True)
            evaluate(csv,validation,geometry=geo,centroid_embargo=False,
                     outer=5,inner=3)
        nested_meta=json.loads(nested_done.read_text(encoding="utf-8"))
        if nested_meta.get("base_sha256")!=csv_hash or \
           nested_meta.get("embargo")!="geometrico" or \
           nested_meta.get("particoes_externas_por_escala")!=5:
            raise ValueError("Manifesto da validação aninhada não corresponde à base.")
        summary=pd.read_csv(validation/"area1_resumo_oito_modelos.csv")
        if len(summary)!=16 or not summary["folds"].eq(5).all():
            raise ValueError("Esperados 8 modelos × 2 escalas e 5 divisões por escala.")
    else:
        nested_meta=None

    report={
        "estado":"AREA1_TREINADA_E_AUDITADA",
        "gerado_em_utc":datetime.now(timezone.utc).isoformat(),
        "originais":original,
        "area1_segmentos_rotulados_unicos":len(frame),
        "area1_base_rotulada_sha256":csv_hash,
        "treinamento_oito_modelos":True,
        "embargo_geometrico_25m":True,
        "nova_validacao_aninhada_concluida":nested_meta is not None,
        "modelos":[
            {"nome":name,
             "arquivo":info["arquivo"],"regularizacao":info["receita"],
             "f1_validacao_interna":info["f1_validacao_interna"]}
            for name,info in model_metadata["modelos"].items()
        ],
        "nunca_aplicou_rotulos_externos":True,
        "metricas_geograficas_externas_calculadas":False,
        "metrica_area1_comparavel_a_teste_externo":False,
        "duracao_desta_execucao_segundos":round(time.monotonic()-start,1),
        "proximas_etapas":[
            "Conferir a identidade da banda NIR dos quatro novos rasters",
            "Aplicar estes modelos fixos a A1, A2, A3, A4",
            "Rotular referências independentes antes de calcular F1 externo"
        ],
        "nota":"Resultados antigos intactos; avaliação Area1 com novas divisões não é teste geográfico externo."
    }
    (output/"resumo_execucao_treinamento.json").write_text(
        json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    print(f"SUCESSO: 505 segmentos, 8 classificadores e "
          f"{'5 divisões por escala' if run_nested else 'validação aninhada dispensada'}.",
          flush=True)
    print("Relatório:",output/"resumo_execucao_treinamento.json")
    return report


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--area1",type=Path,required=True,
                   help="Pasta privada original com os TIFFs e GeoPackages Area1")
    p.add_argument("--out",type=Path,required=True,
                   help="Pasta NOVA de resultados fora da pasta Area1")
    p.add_argument("--so-auditoria",action="store_true",
                   help="Verifica arquivos e 510 pontos sem executar Quickshift/treino")
    p.add_argument("--sem-validacao-aninhada",action="store_true",
                   help="Treina os oito modelos, mas não executa a avaliação 5x2")
    a=p.parse_args()
    run_pipeline(a.area1,a.out,a.so_auditoria,not a.sem_validacao_aninhada)


if __name__=="__main__":
    main()
