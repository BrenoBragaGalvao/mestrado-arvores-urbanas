#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Prepara revisão CEGA de bases locais sugeridas por IA, sem criar rótulos.

As referências externas nesta bateria NÃO são verdade-terreno até revisão humana.
Não reexecuta treinamento, não altera originais e NÃO calcula F1 externo.

Exemplo (Google Drive montado):
  python preparar_revisao_humana_250.py preparar \
    --pacotes "/content/drive/MyDrive/.../02_sagrada_familia_caxias_250_por_classe.zip" \
              "/content/drive/MyDrive/.../03_centro_novo_hamburgo_250_por_classe.zip" \
              "/content/drive/MyDrive/.../04_lomba_grande_novo_hamburgo_250_por_classe.zip" \
              "/content/drive/MyDrive/.../05_cristo_rei_sao_leopoldo_250_por_classe.zip" \
    --out "/content/drive/MyDrive/Proposta1_AUDITORIA_HUMANA"
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
from pathlib import Path
import re
import zipfile

import geopandas as gpd
import numpy as np
import pandas as pd
from shapely.geometry import Point

VALID_CLASSES = {"arvore", "grama", "outro", "incerto"}


def _source_file(archive: zipfile.ZipFile, basename: str) -> bytes:
    matches = [n for n in archive.namelist() if Path(n).name.casefold() == basename.casefold()]
    if len(matches) != 1:
        raise ValueError(f"{archive.filename}: esperado um arquivo {basename}, encontrados {len(matches)}")
    return archive.read(matches[0])


def _col(frame: pd.DataFrame, *candidates: str) -> str | None:
    normalized = {name.strip().lower(): name for name in frame.columns}
    for candidate in candidates:
        if candidate.lower() in normalized:
            return normalized[candidate.lower()]
    return None


def read_source(path: Path) -> tuple[pd.DataFrame, dict]:
    if not path.is_file() or not zipfile.is_zipfile(path):
        raise ValueError(f"Pacote ausente ou não é ZIP válido: {path}")
    with zipfile.ZipFile(path) as archive:
        damaged = archive.testzip()
        if damaged is not None:
            raise ValueError(f"CRC inválido no pacote {path}: {damaged}")
        frame = pd.read_csv(io.BytesIO(_source_file(archive, "Amostras_treino.csv")))
        try:
            manifest = json.loads(_source_file(archive, "Manifesto_amostragem.json"))
        except ValueError:
            manifest = {"advertencia": "Manifesto de amostragem não localizado no ZIP"}
    return frame, manifest


def _normalize_class(value: object) -> str:
    value = str(value).strip().casefold()
    if value in ("arvore", "árvore", "tree"):
        return "arvore"
    if value in ("grama", "graminea", "gramínea", "grass"):
        return "grama"
    return value if value not in ("nan", "none", "") else ""


def prepare_one(source: Path, out: Path, epsg: int = 31982, expected: int = 500) -> dict:
    frame, manifest = read_source(source)
    slug = re.sub(r"[^a-z0-9_]+", "_", source.stem.lower()).strip("_")
    dest = out / slug
    if dest.exists():
        raise FileExistsError(f"Saída existente; preservar versões anteriores: {dest}")
    id_col = _col(frame, "segmento_id", "id_segmento", "id")
    x_col, y_col = _col(frame, "x", "lon", "longitude"), _col(frame, "y", "lat", "latitude")
    label_col = _col(frame, "classe", "classe_sugerida", "classe_preliminar", "rotulo_preliminar")
    if not all((id_col, x_col, y_col, label_col)):
        raise ValueError(f"{source.name}: faltam colunas obrigatórias. Obtidas: {frame.columns.tolist()}")
    if len(frame) != expected:
        raise ValueError(f"{source.name}: esperadas {expected} amostras, encontradas {len(frame)}")
    if frame[id_col].isna().any() or frame[id_col].astype(str).duplicated().any():
        raise ValueError(f"{source.name}: IDs de segmento ausentes ou repetidos")
    xy = frame[[x_col, y_col]].apply(pd.to_numeric, errors="coerce").to_numpy(dtype=float)
    if not np.isfinite(xy).all():
        raise ValueError(f"{source.name}: coordenadas inválidas")
    labels = frame[label_col].map(_normalize_class)
    if (labels.value_counts().reindex(["arvore", "grama"], fill_value=0) != expected // 2).any() or not labels.isin(["arvore", "grama"]).all():
        raise ValueError(f"{source.name}: esperado conjunto equilibrado; obtidas {labels.value_counts().to_dict()}")
    human_col = _col(frame, "classe_verificada")
    human_count = (frame[human_col].fillna("").astype(str).str.strip().ne("").sum() if human_col else 0)
    if human_count:
        raise ValueError(f"{source.name}: contém {human_count} rótulos alegadamente verificados; auditar origem antes de gerar base cega")
    # IDs estáveis vinculados ao ZIP; NÃO colocar sugestão de IA nem qualquer previsão no GeoPackage.
    samples = pd.DataFrame({
        "amostra_id": [f"R{k:04d}" for k in range(1, len(frame) + 1)],
        "segmento_id": frame[id_col].astype(str).to_numpy(),
        "classe_verificada": [""] * len(frame),
        "observacoes": [""] * len(frame),
        "revisor": [""] * len(frame),
        "data_revisao": [""] * len(frame),
        "x": xy[:, 0], "y": xy[:, 1],
    })
    gdf = gpd.GeoDataFrame(samples, geometry=[Point(x, y) for x, y in xy],
                           crs=f"EPSG:{epsg}")
    dest.mkdir(parents=True, exist_ok=False)
    blinded = dest / "amostras_treino_REVISAO_CEGA.gpkg"
    gdf.to_file(blinded, driver="GPKG")
    # A chave é confidencial em relação a quem anota: não deve ser carregada no QGIS da revisão.
    key = pd.DataFrame({"amostra_id": samples.amostra_id,
                        "segmento_id": samples.segmento_id,
                        "classe_sugerida_IA_NAO_VERIFICADA": labels})
    key.to_csv(dest / "chave_sugestoes_IA_NAO_MOSTRAR_AO_REVISOR.csv", index=False)
    saved = {
        "status": "AGUARDA REVISAO HUMANA",
        "tipo": "treino local; NÃO é avaliação externa cega de 200 pontos",
        "origem_zip": source.name,
        "zip_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "n_amostras": len(frame),
        "n_sugestoes_arvore": int(labels.eq("arvore").sum()),
        "n_sugestoes_grama": int(labels.eq("grama").sum()),
        "rótulos_humanos_confirmados": 0,
        "crs_usado": f"EPSG:{epsg}",
        "origem_documentada": manifest,
        "advertencias": [
            "O GeoPackage não contém sugestões nem predições; abrir somente ele e RGB no QGIS.",
            "Não consultar a chave de IA durante revisão; reconhecer árvore/gramínea/outro/incerto.",
            "Não considerar candidato sugerido automaticamente como referência humana.",
            "Manter os 200 pontos de avaliação geográfica separados deste treino.",
            "Não incluir segmentos de Sagrada Família sobre a Area1 + buffer 25 m; verificar geometria antes de validar.",
            "Conferir CRS informado com o raster RGB e a fonte antes da anotação.",
        ],
    }
    (dest / "manifesto_revisao_cega.json").write_text(
        json.dumps(saved, ensure_ascii=False, indent=2), encoding="utf-8")
    (dest / "INSTRUCOES_QGIS.txt").write_text(
        "REVISÃO CEGA — base de TREINAMENTO local\n\n"
        "1. Carregar apenas o arquivo amostras_treino_REVISAO_CEGA.gpkg e a ortoimagem RGB original.\n"
        "2. Confirmar EPSG/posição dos pontos sobre a ortoimagem antes de anotar.\n"
        "3. NÃO carregar a chave de sugestões de IA nem os mapas de predição.\n"
        "4. Classificar o segmento da localização por RGB: arvore, grama, outro ou incerto.\n"
        "5. Preencher revisor, data_revisao e observacoes; preservar amostra_id e segmento_id.\n"
        "6. Se houver duas classes ou sombra que impeçam conclusão, usar incerto ou outro.\n"
        "7. Guardar o GPKG revisado separado do original. Nunca alterar dados históricos.\n"
        "8. Executar 'conferir' com esse GPKG; não medir F1 externo com estes pontos de treino.\n",
        encoding="utf-8",
    )
    return {"regiao": slug, "pacote": source.name, "amostras": len(frame),
            "confirmadas": 0, "status": "AGUARDA_REVISAO", "pasta": str(dest)}


def check_review(review: Path, key_file: Path, out: Path) -> dict:
    """Confere integridade da anotação; não verifica se a interpretação humana está correta."""
    gdf = gpd.read_file(review)
    key = pd.read_csv(key_file, dtype={"amostra_id": str, "segmento_id": str})
    required = {"amostra_id", "segmento_id", "classe_verificada", "revisor"}
    if not required.issubset(gdf.columns):
        raise ValueError(f"Campos ausentes: {sorted(required - set(gdf.columns))}")
    if gdf.amostra_id.duplicated().any() or gdf.segmento_id.astype(str).duplicated().any():
        raise ValueError("IDs duplicados no arquivo revisado")
    left = gdf[["amostra_id", "segmento_id"]].astype(str).sort_values("amostra_id").reset_index(drop=True)
    right = key[["amostra_id", "segmento_id"]].astype(str).sort_values("amostra_id").reset_index(drop=True)
    if not left.equals(right):
        raise ValueError("Amostras acrescentadas, excluídas ou IDs de segmentos trocados")
    classes = gdf.classe_verificada.map(_normalize_class)
    if not set(classes).issubset(VALID_CLASSES | {""}):
        raise ValueError(f"Rótulos inválidos: {set(classes) - VALID_CLASSES - {''}}")
    reviewers = gdf.revisor.fillna("").astype(str).str.strip()
    if ((classes != "") & (reviewers == "")).any():
        raise ValueError("Há rótulo preenchido sem identificação do revisor")
    counts = classes.value_counts().to_dict()
    report = {"status": "REVISADO_PARCIALMENTE", "n": len(gdf),
              "contagens": counts, "sem_rotulo": int(classes.eq("").sum()),
              "incertos": int(classes.eq("incerto").sum()),
              "outras_coberturas": int(classes.eq("outro").sum()),
              "aviso": "Esta checagem não demonstra independência nem precisão dos rótulos e NÃO calcula F1 externo"}
    if not report["sem_rotulo"]:
        report["status"] = "ANOTACOES_COMPLETAS_AGUARDA_AUDITORIA_DE_QUALIDADE"
    out.parent.mkdir(parents=True, exist_ok=True)
    if out.exists():
        raise FileExistsError(f"Preservar relatório anterior: {out}")
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report


def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="acao", required=True)
    prep = sub.add_parser("preparar")
    prep.add_argument("--pacotes", nargs="+", required=True, type=Path)
    prep.add_argument("--out", required=True, type=Path)
    prep.add_argument("--epsg", type=int, default=31982)
    prep.add_argument("--esperadas-por-imagem", type=int, default=500)
    conf = sub.add_parser("conferir")
    conf.add_argument("--anotadas", required=True, type=Path)
    conf.add_argument("--chave", required=True, type=Path)
    conf.add_argument("--out", required=True, type=Path)
    args = p.parse_args()
    if args.acao == "preparar":
        results = [prepare_one(path, args.out, args.epsg, args.esperadas_por_imagem)
                   for path in args.pacotes]
        print(json.dumps(results, ensure_ascii=False, indent=2))
    else:
        print(json.dumps(check_review(args.anotadas, args.chave, args.out),
                         ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
