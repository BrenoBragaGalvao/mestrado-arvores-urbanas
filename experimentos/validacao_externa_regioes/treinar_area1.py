#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Treinamento APENAS na Area1 para transferência geográfica independente.

Seleciona duas receitas de regularização via validação interna espacial na
Area1, sem ler ou usar referências das regiões externas. O conjunto de teste
externo de Novo Hamburgo/São Leopoldo permanece intocado.

Os resultados históricos do README não são reescritos. Esta é uma NOVA
seleção de modelo final, não a reprodução exata dos folds históricos E2.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import platform
import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from scipy.spatial import cKDTree
from sklearn.metrics import f1_score
from sklearn.model_selection import GroupShuffleSplit

# Importa a própria implementação auditada do repositório, sem copiar receitas.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from v2_auditoria_regularizacao import FEATURES, RECEITAS, criar_modelo  # noqa:E402

MODELS = ("Random Forest", "SVM RBF", "Regressão logística",
          "Extra Trees", "KNN", "HistGradientBoosting",
          "Gaussian Naive Bayes", "Dummy")
CLASSES = ("arvore", "grama")
SCALES = (250, 500)


def read_training_data(path: Path) -> pd.DataFrame:
    if not path.is_file():
        raise FileNotFoundError(f"Base rotulada Area1 ausente: {path}")
    frame = pd.read_csv(path)
    if "id" not in frame and "segmento_id" in frame:
        frame = frame.rename(columns={"segmento_id": "id"})
    needed = {"id", "classe", "x", "y", *FEATURES}
    missing = needed - set(frame.columns)
    if missing:
        raise ValueError(f"Colunas faltantes da base Area1: {sorted(missing)}")
    if frame.id.astype(str).duplicated().any():
        raise ValueError("Base Area1 tem IDs de segmento duplicados.")
    if set(frame.classe.astype(str)) != set(CLASSES):
        raise ValueError("Os rótulos esperados são exclusivamente 'arvore' e 'grama'.")
    cols = ["x", "y", *FEATURES]
    if not np.isfinite(frame[cols].to_numpy(dtype=float)).all():
        raise ValueError("Coordenadas ou características da Area1 têm NaN/inf.")
    if len(frame) < 80:
        raise ValueError("Base Area1 insuficiente para validação espacial.")
    return frame.reset_index(drop=True)


def read_geometry(path: Path | None, frame: pd.DataFrame):
    if path is None:
        return None
    import geopandas as gpd
    geo = gpd.read_file(path)
    if geo.crs is None or not geo.crs.is_projected:
        raise ValueError("Geometrias Area1 devem possuir CRS projetado em metros.")
    if "segmento_id" not in geo:
        raise ValueError("GeoPackage precisa ter a coluna segmento_id.")
    geo.segmento_id = geo.segmento_id.astype(str)
    if geo.segmento_id.duplicated().any():
        raise ValueError("Segmentos duplicados no GeoPackage.")
    geo = geo.set_index("segmento_id").reindex(frame.id.astype(str))
    if geo.geometry.isna().any():
        raise ValueError("Há IDs Area1 sem geometria no GeoPackage.")
    return geo.geometry.to_numpy()


def assign_groups(xy: np.ndarray, block_m: int) -> np.ndarray:
    gx = np.floor((xy[:, 0] - xy[:, 0].min()) / block_m).astype(int)
    gy = np.floor((xy[:, 1] - xy[:, 1].min()) / block_m).astype(int)
    return np.array([f"{a}:{b}" for a, b in zip(gx, gy)])


def embargo_train(xy, tr, te, distance_m, geometries=None):
    if geometries is None:
        dist, _ = cKDTree(xy[te]).query(xy[tr], k=1)
        return tr[dist > distance_m]
    test_g = [geometries[int(k)] for k in te]
    # 505 segmentos: comparação explícita, auditável e suficiente em memória.
    safe = [int(i) for i in tr
            if all(geometries[int(i)].distance(g) > distance_m for g in test_g)]
    return np.asarray(safe, dtype=int)


def inner_splits(frame, geometries, n_splits=3, distance_m=25):
    xy = frame[["x", "y"]].to_numpy(dtype=float)
    labels = frame.classe.to_numpy(dtype=str)
    for scale in SCALES:
        groups = assign_groups(xy, scale)
        if len(set(groups)) < 5:
            raise ValueError(f"Apenas {len(set(groups))} blocos de {scale} m na Area1.")
        spl = GroupShuffleSplit(n_splits=n_splits, test_size=.25,
                                random_state=20261112 + scale)
        valid = []
        for fold, (tr, val) in enumerate(spl.split(xy, labels, groups), 1):
            tr = embargo_train(xy, tr, val, distance_m, geometries)
            if len(tr) < 45 or len(val) < 12 or len(set(labels[tr])) != 2 or len(set(labels[val])) != 2:
                continue
            if not set(groups[tr]).isdisjoint(groups[val]):
                raise AssertionError("Vazamento de blocos espaciais.")
            valid.append((scale, fold, tr, val))
        if len(valid) < 2:
            raise RuntimeError(f"Validação espacial insuficiente em {scale} m: {len(valid)} folds válidos.")
        yield from valid


def run(area1: Path, output: Path, geo_path: Path | None = None,
        allow_centroid: bool = False):
    if geo_path is None and not allow_centroid:
        raise ValueError(
            "Forneça --geometrias para embargo geométrico ou use explicitamente "
            "--permitir-embargo-centroides (protocolo diferente, documentado).")
    output.mkdir(parents=True, exist_ok=True)
    frame = read_training_data(area1)
    geoms = read_geometry(geo_path, frame)
    mode = "geometrias" if geoms is not None else "centroides"
    x = frame[list(FEATURES)].to_numpy(dtype=np.float64)
    y = frame.classe.to_numpy(dtype=str)
    splits = list(inner_splits(frame, geoms))
    if len(splits) < 4:
        raise RuntimeError("Esperadas pelo menos quatro divisões internas válidas.")
    all_rows, chosen_rows = [], []
    for name in MODELS:
        options = []
        for recipe in ("moderada", "forte"):
            params = RECEITAS[recipe][name]
            scores = []
            for scale, fold, tr, va in splits:
                if name == "KNN" and len(tr) < params["n_neighbors"]:
                    raise RuntimeError("Amostras insuficientes para o KNN definido.")
                model = criar_modelo(name, params)
                model.fit(x[tr], y[tr])
                score = float(f1_score(y[va], model.predict(x[va]),
                                       average="macro", zero_division=0))
                scores.append(score)
                all_rows.append(dict(modelo=name, receita=recipe, bloco_m=scale,
                                     divisao=fold, f1_validacao=score,
                                     n_treino=len(tr), n_validacao=len(va)))
            options.append((np.mean(scores), recipe, params))
        best_score, recipe, params = sorted(options, key=lambda item: (-item[0], item[1]))[0]
        chosen_rows.append(dict(modelo=name, receita=recipe,
                                f1_validacao_interna=float(best_score),
                                parametros=json.dumps(params, ensure_ascii=False, sort_keys=True)))
        final = criar_modelo(name, params)
        final.fit(x, y)
        slug = ["random_forest", "svm_rbf", "regressao_logistica", "extra_trees",
                "knn", "hist_gradient_boosting", "gaussian_naive_bayes", "dummy"][MODELS.index(name)]
        joblib.dump(final, output / (slug + ".joblib"), compress=3)
    pd.DataFrame(all_rows).to_csv(output / "validacoes_internas_area1.csv", index=False)
    pd.DataFrame(chosen_rows).to_csv(output / "modelos_escolhidos_area1.csv", index=False)
    manifest = {
        "tipo": "modelos de transferência geográfica treinados exclusivamente na Area1",
        "base_area1_sha256": hashlib.sha256(area1.read_bytes()).hexdigest(),
        "amostras_rotuladas": int(len(frame)),
        "classes": list(CLASSES),
        "features": list(FEATURES),
        "validacao": {"blocos_m": list(SCALES), "divisoes_pretendidas_por_escala": 3,
                     "divisoes_validas": len(splits), "embargo_m": 25,
                     "tipo_embargo": mode, "objetivo": "seleção interna de regularização"},
        "modelos": {row["modelo"]: {
            "arquivo": ["random_forest", "svm_rbf", "regressao_logistica",
                        "extra_trees", "knn", "hist_gradient_boosting",
                        "gaussian_naive_bayes", "dummy"][MODELS.index(row["modelo"])] + ".joblib",
            "receita": row["receita"],
            "f1_validacao_interna": row["f1_validacao_interna"],
            "parametros": json.loads(row["parametros"])
        } for row in chosen_rows},
        "escopo": ("Seleção interna de modelos para transferência externa: NÃO representa "
                   "um novo teste externo nem reproduz exatamente as tabelas históricas."),
        "versionamento": {"python": platform.python_version(),
                         "sklearn": __import__("sklearn").__version__,
                         "numpy": np.__version__,
                         "pandas": pd.__version__}
    }
    (output / "manifesto_modelos.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(pd.DataFrame(chosen_rows)[["modelo", "receita", "f1_validacao_interna"]].to_string(index=False))
    print("Modelos Area1 gravados em", output)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--area1-csv", required=True, type=Path,
                   help="rotulos_sem_duplicacao.csv original dos 812 quadrantes da Area1")
    p.add_argument("--geometrias", type=Path, help="E3c_geometrias_rotuladas_812.gpkg: embargo geométrico")
    p.add_argument("--permitir-embargo-centroides", action="store_true",
                   help="Aproximação explícita se não houver geometrias; não equivale ao protocolo geométrico")
    p.add_argument("--out", required=True, type=Path)
    args = p.parse_args()
    run(args.area1_csv, args.out, args.geometrias, args.permitir_embargo_centroides)


if __name__ == "__main__":
    main()
