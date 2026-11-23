#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Auditoria reproduzível dos arquivos compactados e rasters regionais.

O nome da pasta NÃO comprova que Sagrada Família é idêntica à Area1.
Primeiro inventaria os ZIP/RAR sem descompactar; opcionalmente extrai com
proteção contra path traversal e inspeciona metadados de arquivos reais.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
import os
import shutil
import subprocess
import zipfile
from pathlib import Path

SUPPORTED = {".zip", ".rar"}
RASTER = {".tif", ".tiff", ".vrt", ".img", ".jp2"}
VECTOR = {".gpkg", ".shp", ".geojson", ".kml", ".prj", ".shx", ".dbf"}


def archive_list(path: Path) -> list[dict]:
    items = []
    if path.suffix.lower() == ".zip":
        with zipfile.ZipFile(path) as file:
            for i in file.infolist():
                items.append({"caminho": i.filename, "tamanho": i.file_size,
                              "comprimido": i.compress_size,
                              "pasta": i.is_dir(), "origem": path.name})
    elif path.suffix.lower() == ".rar":
        try:
            import rarfile
        except ImportError as ex:
            raise RuntimeError("Execute pip install rarfile para inventariar RAR.") from ex
        with rarfile.RarFile(path) as file:
            for i in file.infolist():
                items.append({"caminho": i.filename, "tamanho": i.file_size,
                              "comprimido": i.compress_size,
                              "pasta": i.is_dir(), "origem": path.name})
    else:
        raise ValueError(f"Arquivo compactado não suportado: {path}")
    return items


def is_safe_member(name: str) -> bool:
    normalized = name.replace("\\", "/")
    parts = normalized.split("/")
    return (not normalized.startswith("/")
            and not (len(normalized) >= 2 and normalized[1] == ":")
            and not any(part in {"..", ""} for part in parts if part != parts[-1])
            and ".." not in parts)


def unpack_zip_safely(path: Path, dest: Path, max_bytes=40_000_000_000):
    dest.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path) as archive:
        members = archive.infolist()
        if len(members) > 100_000:
            raise ValueError("Quantidade inesperada de arquivos: revisar manualmente.")
        total = sum(m.file_size for m in members)
        if total > max_bytes:
            raise ValueError(f"Extração excederia {max_bytes} bytes: {total}")
        for m in members:
            if not is_safe_member(m.filename):
                raise ValueError(f"Nome de arquivo potencialmente inseguro: {m.filename}")
            if (m.external_attr >> 16) & 0o170000 == 0o120000:
                raise ValueError(f"Link simbólico em ZIP não será extraído: {m.filename}")
            if m.file_size > 100_000_000 and m.file_size / max(1, m.compress_size) > 250:
                raise ValueError(f"Alta taxa de compressão: rever {m.filename}")
        for m in members:
            target = dest / m.filename.replace("\\", "/")
            if m.is_dir():
                target.mkdir(parents=True, exist_ok=True)
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                if target.exists() and target.stat().st_size == m.file_size:
                    continue
                with archive.open(m) as src, target.open("wb") as dst:
                    shutil.copyfileobj(src, dst, length=1024 * 1024)


def unpack_rar(path: Path, dest: Path):
    try:
        import rarfile
    except ImportError as exc:
        raise RuntimeError("pip install rarfile e apt install unrar-free/p7zip-full.") from exc
    dest.mkdir(parents=True, exist_ok=True)
    with rarfile.RarFile(path) as f:
        entries = f.infolist()
        for m in entries:
            if not is_safe_member(m.filename):
                raise ValueError(f"Nome inválido em RAR: {m.filename}")
        if sum(m.file_size for m in entries) > 40_000_000_000:
            raise ValueError("RAR excederia limite de extração de 40 GB.")
        # rarfile exige ferramenta externa disponível (unrar, unar ou 7z).
        try:
            f.extractall(dest)
        except Exception as exc:
            raise RuntimeError("Falha na extração RAR; verifique a disponibilidade de unrar/unar/7z.") from exc


def inspect_file(path: Path) -> dict:
    entry = {"caminho": str(path), "nome": path.name,
             "extensao": path.suffix.lower(), "bytes": path.stat().st_size,
             "tipo": "desconhecido"}
    if path.suffix.lower() in RASTER:
        import rasterio
        try:
            with rasterio.open(path) as ds:
                entry.update(tipo="raster", largura=ds.width, altura=ds.height,
                             bandas=ds.count, crs=str(ds.crs), resolucao=list(ds.res),
                             limites=list(ds.bounds), transform=tuple(ds.transform)[:6],
                             band_descriptions=list(ds.descriptions),
                             nodata=ds.nodata, dtype=list(ds.dtypes))
        except Exception as exc:
            entry.update(tipo="raster_nao_lido", erro=str(exc))
    elif path.suffix.lower() in VECTOR and path.suffix.lower() in {".gpkg", ".shp", ".geojson"}:
        import geopandas as gpd
        try:
            gdf = gpd.read_file(path)
            entry.update(tipo="vetor", crs=str(gdf.crs), quantidade=len(gdf),
                         geom_types=sorted(map(str, gdf.geom_type.unique())),
                         limites=list(gdf.total_bounds))
        except Exception as exc:
            entry.update(tipo="vetor_nao_lido", erro=str(exc))
    return entry


def intersect_area(bounds_a, bounds_b):
    x0 = max(bounds_a[0], bounds_b[0])
    x1 = min(bounds_a[2], bounds_b[2])
    y0 = max(bounds_a[1], bounds_b[1])
    y1 = min(bounds_a[3], bounds_b[3])
    return max(x1-x0, 0) * max(y1-y0, 0)


def compare_original(original: Path, other: Path, compare_pixels=False) -> dict:
    import rasterio
    import numpy as np
    with rasterio.open(original) as a, rasterio.open(other) as b:
        same_crs = a.crs == b.crs
        area1_rect = max((a.bounds.right-a.bounds.left)*(a.bounds.top-a.bounds.bottom), 1e-12)
        result = {
            "original": str(original), "candidato": str(other),
            "mesmo_crs": same_crs,
            "mesma_forma": (a.width, a.height) == (b.width, b.height),
            "mesmo_numero_bandas": a.count == b.count,
            "mesma_transformacao": a.transform.almost_equals(b.transform),
            "sobreposicao_retangulo_area1": (
                intersect_area(a.bounds, b.bounds) / area1_rect if same_crs else None),
            "pixels_identicos": None,
            "conclusao": "NÃO COMPROVADO; nomes e região são insuficientes"
        }
        if compare_pixels and result["mesma_forma"] and result["mesma_transformacao"] and same_crs and result["mesmo_numero_bandas"]:
            identical = True
            for _, window in a.block_windows(1):
                if not np.array_equal(a.read(window=window), b.read(window=window)):
                    identical = False
                    break
            result["pixels_identicos"] = identical
            if identical:
                result["conclusao"] = "Rasters equivalentes em pixels, CRS, grade e bandas"
        return result


def run(archives: Path | None, extracted: Path | None, out: Path,
        unpack: bool, original_rgb: Path | None, compare_pixels: bool):
    out.mkdir(parents=True, exist_ok=True)
    archive_rows, extracted_rows = [], []
    archive_paths = sorted(p for p in archives.iterdir()
                           if p.is_file() and p.suffix.lower() in SUPPORTED) if archives else []
    for path in archive_paths:
        items = archive_list(path)
        for item in items:
            item["categoria"] = Path(item["caminho"]).suffix.lower()
        archive_rows.extend(items)
        print(f"{path.name}: {len(items)} entradas | {sum(x['tamanho'] for x in items):,} bytes descompactados")
        if unpack:
            if extracted is None:
                raise ValueError("--extrair exige --extraidos")
            region_dir = extracted / path.stem
            if path.suffix.lower() == ".zip":
                unpack_zip_safely(path, region_dir)
            else:
                unpack_rar(path, region_dir)
    if extracted and extracted.is_dir():
        for file in sorted(extracted.rglob("*")):
            if file.is_file() and file.suffix.lower() in RASTER | VECTOR:
                extracted_rows.append(inspect_file(file))
    comparisons = []
    if original_rgb and original_rgb.is_file():
        for e in extracted_rows:
            if e["tipo"] == "raster" and int(e["bandas"]) >= 3:
                comparisons.append(compare_original(original_rgb, Path(e["caminho"]), compare_pixels))
    report = {
        "arquivos_compactados": [dict(nome=p.name, tamanho_comprimido=p.stat().st_size) for p in archive_paths],
        "inventario_arquivos": archive_rows,
        "arquivos_inspecionados": extracted_rows,
        "comparacoes_area1": comparisons,
        "restricao": ("Inventário do conteúdo do arquivo ZIP/RAR é distinto de validação científica. "
                      "Nem NIR nem anotações de árvores/grama podem ser presumidos por nome."),
        "status": "auditado_localmente" if archive_paths or extracted_rows else "nenhum_arquivo_local"
    }
    (out / "auditoria_pacotes.json").write_text(json.dumps(report, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    if archive_rows:
        import pandas as pd
        pd.DataFrame(archive_rows).to_csv(out / "inventario_pacotes.csv", index=False)
    if extracted_rows:
        import pandas as pd
        pd.DataFrame(extracted_rows).to_csv(out / "metadados_geoespaciais.csv", index=False)
    if comparisons:
        import pandas as pd
        pd.DataFrame(comparisons).to_csv(out / "comparacao_com_area1.csv", index=False)
    print(f"Auditoria gravada em {out}")


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--arquivos", type=Path, help="Pasta com ZIPs/RAR copiados do Drive")
    p.add_argument("--extraidos", type=Path, help="Pasta onde os arquivos foram ou serão extraídos")
    p.add_argument("--extrair", action="store_true", help="Extrai cada pacote em subpasta própria")
    p.add_argument("--rgb-area1", type=Path, help="AOI_RGB_NEW.tif para comparar metadados de raster")
    p.add_argument("--comparar-pixels", action="store_true", help="Lê pixels quando grades coincidem; pode consumir tempo")
    p.add_argument("--out", type=Path, required=True)
    args = p.parse_args()
    run(args.arquivos, args.extraidos, args.out, args.extrair, args.rgb_area1, args.comparar_pixels)


if __name__ == "__main__":
    main()
