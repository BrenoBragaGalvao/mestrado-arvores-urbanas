#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Ablação PAREADA (nova bateria) de LR: HSV+Canny vs HSV+Canny+NDVI.

Área 1: 30 partições espaciais de 500 m com embargo GEOMÉTRICO de 25 m.
Regiões externas: exatamente os mesmos 600 pontos cegos, CHMv2 B elegível,
30 bootstraps PAREADOS por bloco de 500 m, SEM re-treinar no teste externo.

Não reescreve resultados históricos. Exige atributos reais dos segmentos,
máscaras e rótulos originais, e verifica a identidade da previsão A congelada.
Não aceita amostras simuladas como resultado científico.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import f1_score
from sklearn.model_selection import GroupShuffleSplit
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

FEATURES = {
    "HSV + Canny": ["mean_intensity", "mean_edges"],
    "HSV + Canny + NDVI": ["mean_intensity", "mean_edges", "mean_ndvi"],
}
REGIONS = {
    "sagrada_familia_caxias": ("Sagrada Família", 179),
    "lomba_grande_novo_hamburgo": ("Lomba Grande", 183),
    "cristo_rei_sao_leopoldo": ("Cristo Rei", 181),
}
CLASSES = {"arvore", "grama"}
SEED = 20261120


def model():
    return make_pipeline(
        StandardScaler(),
        LogisticRegression(C=0.1, penalty="l2", max_iter=3000, random_state=42),
    )


def validate_numeric(frame, keys):
    if not np.isfinite(frame[list(keys)].to_numpy(dtype=float)).all():
        raise ValueError("Atributos/posições não finitos")
    if frame[list(keys)].isna().any().any():
        raise ValueError("Atributos ausentes")


def load_area1(area1_csv: Path, geopackage: Path):
    frame = pd.read_csv(area1_csv, dtype={"id": str})
    needed = {"id", "classe", "x", "y", *FEATURES["HSV + Canny + NDVI"]}
    if not needed.issubset(frame):
        raise ValueError(f"Area1 sem campos: {sorted(needed - set(frame.columns))}")
    if len(frame) != 505 or frame.id.duplicated().any():
        raise ValueError("Area1 deve ter 505 segmentos únicos")
    if frame.classe.value_counts().to_dict() != {"arvore": 257, "grama": 248}:
        raise ValueError("Distribuição da Area1 não corresponde à base original")
    validate_numeric(frame, {"x", "y", *FEATURES["HSV + Canny + NDVI"]})
    geometry = gpd.read_file(geopackage)
    if geometry.crs is None or not geometry.crs.is_projected:
        raise ValueError("GeoPackage Area1 precisa ter CRS projetado em metros")
    if "segmento_id" not in geometry:
        raise ValueError("GeoPackage sem segmento_id")
    geometry["segmento_id"] = geometry.segmento_id.astype(str)
    if geometry.segmento_id.duplicated().any():
        raise ValueError("Geometrias duplicadas")
    ordered = geometry.set_index("segmento_id").reindex(frame.id)
    if ordered.geometry.isna().any():
        raise ValueError("Segmentos Area1 sem geometria correspondente")
    return frame.reset_index(drop=True), ordered.geometry.to_numpy()


def paired_splits(frame, geometries, n=30):
    xy = frame[["x", "y"]].to_numpy(dtype=float)
    groups = np.asarray([f"{int(np.floor(x / 500))}_{int(np.floor(y / 500))}"
                         for x, y in xy])
    labels = frame.classe.to_numpy()
    splitter = GroupShuffleSplit(n_splits=max(300, n * 15),
                                 test_size=0.20, random_state=SEED)
    selected = []
    for train, test in splitter.split(xy, labels, groups):
        if len(test) < 10 or len(set(labels[test])) != 2:
            continue
        # Embargo por geometrias reais; não substituir por distância entre centroides.
        test_shapes = [geometries[int(i)] for i in test]
        safe = np.asarray([int(i) for i in train
                           if all(geometries[int(i)].distance(g) > 25
                                  for g in test_shapes)], dtype=int)
        if len(safe) < 50 or len(set(labels[safe])) != 2:
            continue
        if not set(groups[safe]).isdisjoint(set(groups[test])):
            raise AssertionError("Vazamento de blocos")
        selected.append((safe, test))
        if len(selected) == n:
            break
    if len(selected) != n:
        raise RuntimeError(f"Só {len(selected)} partições espaciais válidas; esperadas {n}")
    return selected


def internal_scores(frame, geoms, n=30):
    y = frame.classe.to_numpy()
    splits = paired_splits(frame, geoms, n)
    result = []
    for fold, (tr, te) in enumerate(splits, 1):
        for variant, cols in FEATURES.items():
            m = model().fit(frame.iloc[tr][cols].to_numpy(dtype=float), y[tr])
            score = f1_score(y[te], m.predict(frame.iloc[te][cols].to_numpy(dtype=float)),
                             average="macro", labels=["arvore", "grama"], zero_division=0)
            result.append({"regiao": "Area1", "divisao": fold,
                           "configuracao": variant, "f1_macro": float(score),
                           "n_treino": int(len(tr)), "n_teste": int(len(te))})
    return pd.DataFrame(result)


def load_external(files, frozen_path):
    frames = []
    for region, path in files:
        if region not in REGIONS:
            raise ValueError("Região desconhecida no argumento externo")
        f = pd.read_csv(path, dtype={"segmento_id": str, "amostra_id": str})
        needed = {"regiao", "amostra_id", "segmento_id", "bloco_500m", "B",
                  *FEATURES["HSV + Canny + NDVI"]}
        if not needed.issubset(f):
            raise ValueError(f"{region}: campos ausentes: {sorted(needed-set(f))}")
        if len(f) != 200 or f.amostra_id.duplicated().any() or f.segmento_id.duplicated().any():
            raise ValueError(f"{region}: esperados 200 pontos e segmentos únicos")
        if set(f.regiao) != {region} or not set(f.B).issubset(CLASSES | {"incerto"}):
            raise ValueError(f"{region}: região/rótulo incompatível com CHMv2 B")
        if int(f.B.isin(CLASSES).sum()) != REGIONS[region][1]:
            raise ValueError(f"{region}: número de pseudo-rótulos válidos mudou")
        validate_numeric(f, FEATURES["HSV + Canny + NDVI"])
        frames.append(f)
    if len(frames) != 3 or len({region for region, _ in files}) != 3:
        raise ValueError("Exigem-se as três regiões externas")
    external = pd.concat(frames, ignore_index=True)
    frozen = pd.read_csv(frozen_path, dtype={"segmento_id": str, "amostra_id": str})
    ids = ["regiao", "amostra_id", "segmento_id"]
    if len(frozen) != 600 or frozen.duplicated(ids).any():
        raise ValueError("Arquivo de 600 pontos congelados inválido")
    compared = external.merge(frozen[ids + ["predicao_modelo", "B", "bloco_500m"]],
                              on=ids, validate="one_to_one", how="inner",
                              suffixes=("", "_original"))
    if len(compared) != 600:
        raise ValueError("Não são exatamente os mesmos 600 pontos originais")
    if not (compared.B == compared.B_original).all() or not (
        compared.bloco_500m.astype(str) == compared.bloco_500m_original.astype(str)
    ).all():
        raise ValueError("Rótulos CHMv2 ou blocos espaciais foram alterados")
    return compared


def external_scores(area1, external, n=30):
    y_train = area1.classe.to_numpy()
    frame = external.copy()
    for variant, cols in FEATURES.items():
        m = model().fit(area1[cols].to_numpy(dtype=float), y_train)
        frame["prev_" + str(len(cols))] = m.predict(frame[cols].to_numpy(dtype=float))

    # Controle rígido: o pipeline original de 3 atributos DEVE reproduzir
    # as predições A congeladas antes de atribuir resultados à mesma experiência.
    mismatch = int((frame.prev_3 != frame.predicao_modelo).sum())
    if mismatch:
        raise ValueError(
            f"Predição original de 3 atributos divergiu em {mismatch}/600 pontos. "
            "Resultados não comparáveis; investigar base/grade/extrator antes de reportar F1."
        )

    results = []
    for region, (name, _) in REGIONS.items():
        group = frame[(frame.regiao == region) & frame.B.isin(CLASSES)].copy()
        keys = sorted(group.bloco_500m.astype(str).unique())
        mapping = {k: group[group.bloco_500m.astype(str) == k] for k in keys}
        rng = np.random.default_rng(SEED + list(REGIONS).index(region))
        for fold in range(1, n+1):
            chosen = rng.choice(keys, size=len(keys), replace=True)
            sample = pd.concat([mapping[k] for k in chosen], ignore_index=True)
            for variant, cols in FEATURES.items():
                score = f1_score(sample.B, sample["prev_" + str(len(cols))],
                                 average="macro", labels=["arvore", "grama"],
                                 zero_division=0)
                results.append({"regiao": name, "divisao": fold,
                                "configuracao": variant, "f1_macro": float(score),
                                "n_treino": len(area1), "n_teste": len(sample)})
    return pd.DataFrame(results)


def summary(rows):
    result = rows.groupby(["configuracao", "regiao"], as_index=False).agg(
        media=("f1_macro", "mean"),
        desvio_padrao=("f1_macro", "std"),
        avaliacoes=("f1_macro", "size"),
    )
    if result.shape[0] != 8 or not result.avaliacoes.eq(30).all():
        raise AssertionError("Esperadas duas configurações x quatro regiões x 30 avaliações")
    return result


def run(area1_csv, geoms, external_paths, frozen_csv, output):
    area1, geometry = load_area1(area1_csv, geoms)
    external = load_external(external_paths, frozen_csv)
    rows = pd.concat(
        [internal_scores(area1, geometry), external_scores(area1, external)],
        ignore_index=True,
    )
    tab = summary(rows)
    output.mkdir(parents=True, exist_ok=True)
    rows.to_csv(output / "ablacao_f1_pareado_240_avaliacoes.csv", index=False)
    tab.to_csv(output / "ablacao_f1_resumo_quatro_regioes.csv", index=False)
    table = tab.pivot(index="configuracao", columns="regiao", values="media")
    table = table.reindex(list(FEATURES), axis=0)
    table = table.reindex(["Area1", *(value[0] for value in REGIONS.values())], axis=1)
    table.to_csv(output / "tabela_readme_ablacao_hsv_canny_ndvi.csv")
    manifest = {
        "status": "NOVA_BATERIA_PAREADA_CALCULADA",
        "escalas": [500], "embargo_area1_m": 25,
        "semente": SEED, "n_avaliacoes_por_configuracao_regiao": 30,
        "n_teste_externo_total": 600, "n_teste_externo_elegivel": 543,
        "modelo": "StandardScaler + LogisticRegression C=0.1",
        "nota": "Não substituir a tabela histórica de 30 avaliações por estes valores; "
                "são uma nova bateria pareada. F1 externo é concordância com CHMv2, "
                "não rotulagem humana. Comparações só entre braços do MESMO novo protocolo.",
        "modelo_tres_atributos_confere_predicoes_congeladas": True,
    }
    (output / "manifesto_ablacao.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return tab


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--area1", type=Path, required=True,
                   help="CSV dos 505 segmentos rotulados; colunas id, classe, x, y, atributos")
    p.add_argument("--geometrias", type=Path, required=True,
                   help="GeoPackage Area1 com segmento_id e geometrias reais")
    p.add_argument("--externos", type=Path, nargs=3, required=True,
                   help="Três CSV gerados por get_features() nos 600 pontos originais")
    p.add_argument("--congelados", type=Path, required=True,
                   help="600_pontos_cegos_CHMv2_congelados.csv do Git")
    p.add_argument("--out", type=Path, required=True)
    args = p.parse_args()
    regions = list(REGIONS)
    external = list(zip(regions, args.externos))
    tab = run(args.area1, args.geometrias, external, args.congelados, args.out)
    print(tab.to_string(index=False))


if __name__ == "__main__":
    main()
