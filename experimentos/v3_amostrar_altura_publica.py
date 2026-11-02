#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Amostra previsões de altura de dossel CHMv2 (Meta/WRI) em pontos da Area1.

Fonte pública: Meta/WRI CHMv2 2026, licença CC-BY 4.0.
https://registry.opendata.aws/dataforgood-fb-forestsv2/

Somente estimativa modelada em pixel e vizinhança, não altura observada em campo.
Usa GeoTIFF COG por leituras HTTP Range (sem Google Earth Engine/conta AWS).
"""
from __future__ import annotations
import argparse
import json
import math
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import rasterio
from rasterio.windows import Window
from pyproj import Transformer

PREFIX = "https://dataforgood-fb-data.s3.us-east-1.amazonaws.com/forests/v2/global/dinov3_global_chm_v2_ml3/chm/"
DATASET = "Meta/WRI CHMv2 2026 (DINOv3)"


def quadkey(lat: float, lon: float, z: int = 10) -> str:
    if not (-85.0511 <= lat <= 85.0511 and -180 <= lon <= 180):
        raise ValueError("Coordenada fora do intervalo válido de Web Mercator")
    x = int((lon + 180) / 360 * (1 << z))
    y = int((1 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2 * (1 << z))
    x = min((1 << z) - 1, max(0, x))
    y = min((1 << z) - 1, max(0, y))
    return "".join(str(int(bool(x & (1 << i))) + 2 * int(bool(y & (1 << i))))
                   for i in range(z - 1, -1, -1))


def index_point_pixel(ds, x_m, y_m):
    col, row = (~ds.transform) * (x_m, y_m)
    return int(math.floor(row)), int(math.floor(col))


def valid_data(array, ds):
    arr = np.ma.array(array, copy=False)
    if ds.nodata is not None:
        arr = np.ma.masked_equal(arr, ds.nodata)
    arr = np.ma.masked_invalid(arr)
    return arr.compressed()


def sample_point(ds, lon: float, lat: float, raio: float = 5.0):
    xx, yy = Transformer.from_crs("EPSG:4326", ds.crs, always_xy=True).transform(lon, lat)
    row, col = index_point_pixel(ds, xx, yy)
    if row < 0 or col < 0 or row >= ds.height or col >= ds.width:
        return None, None, "fora_dos_limites"
    pixel = ds.read(1, window=Window(col, row, 1, 1), masked=True)
    arr = valid_data(pixel, ds)
    value = float(arr[0]) if len(arr) else None
    # Um raio local é auxiliar; pode incluir árvores vizinhas e não mede a copa.
    resx, resy = abs(ds.res[0]), abs(ds.res[1])
    half_x = max(1, math.ceil(raio / resx))
    half_y = max(1, math.ceil(raio / resy))
    left = max(0, col - half_x)
    top = max(0, row - half_y)
    right = min(ds.width, col + half_x + 1)
    bottom = min(ds.height, row + half_y + 1)
    local = ds.read(1, window=Window(left, top, right - left, bottom - top), masked=True)
    yy_grid, xx_grid = np.mgrid[top:bottom, left:right]
    gx, gy = rasterio.transform.xy(ds.transform, yy_grid, xx_grid, offset='center')
    dist2 = (np.asarray(gx) - xx)**2 + (np.asarray(gy) - yy)**2
    circular = np.ma.array(local, mask=np.ma.getmaskarray(local) | (dist2 > raio ** 2))
    valid = valid_data(circular, ds)
    m = float(np.max(valid)) if len(valid) else None
    status = "sem_dado" if value is None and m is None else "estimativa_modelada"
    return value, m, status


def executar(pontos_csv: Path, saida: Path, raio: float = 5.):
    pontos = pd.read_csv(pontos_csv)
    required = {"ponto_id", "latitude", "longitude"}
    if not required.issubset(pontos.columns):
        raise ValueError(f"CSV deve conter: {sorted(required)}")
    if len(pontos) != 257 or pontos.ponto_id.nunique() != 257:
        raise ValueError("São necessários exatamente 257 pontos originais únicos")
    pontos = pontos.copy()
    pontos["quadkey_meta_v2"] = [quadkey(float(p.latitude), float(p.longitude))
                                     for p in pontos.itertuples(index=False)]
    resultados = []
    sources = []
    for key, group in pontos.groupby("quadkey_meta_v2"):
        url = PREFIX + key + ".tif"
        print("Lendo COG público:", url, "pontos:", len(group), flush=True)
        with rasterio.Env(GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR",
                          CPL_VSIL_CURL_ALLOWED_EXTENSIONS=".tif",
                          GDAL_HTTP_MAX_RETRY="2", GDAL_HTTP_RETRY_DELAY="2",
                          GDAL_CACHEMAX="128"):
            with rasterio.open("/vsicurl/" + url) as src:
                if src.count != 1 or src.crs is None:
                    raise ValueError("GeoTIFF inesperado: uma banda georreferenciada é obrigatória")
                if src.crs.to_epsg() != 3857:
                    raise ValueError(f"CRS do Meta CHMv2 inesperado: {src.crs}")
                sources.append({"quadkey":key, "url":url, "crs":str(src.crs),
                                "pixel_m":list(src.res), "nodata":src.nodata,
                                "dtype":str(src.dtypes[0])})
                for row in group.itertuples(index=False):
                    val,local,status = sample_point(src,float(row.longitude),float(row.latitude),raio)
                    resultados.append({"ponto_id":int(row.ponto_id),
                                       "altura_meta_v2_pixel_m":val,
                                       "altura_meta_v2_max_raio_5m_m":local,
                                       "status_amostragem":status,
                                       "quadkey_meta_v2":key})
    out = pontos.merge(pd.DataFrame(resultados),on=["ponto_id","quadkey_meta_v2"],how="left",validate="one_to_one")
    if len(out)!=257 or out.status_amostragem.isna().any():
        raise RuntimeError("Erro: pontos perdidos ao combinar dados")
    out["interpretacao"]="PREDICAO DE ALTURA DO DOSSEL: nao e altura de arvore medida"
    saida.mkdir(parents=True,exist_ok=True)
    path=saida / "v3_meta_chmv2_estimativas_257_arvores.csv"
    out.to_csv(path,index=False,encoding="utf-8-sig")
    summary={"fonte":DATASET,"licenca":"CC BY 4.0","consultado_em_utc":datetime.now(timezone.utc).isoformat(),
             "n_pontos":len(out),"com_predicao_no_pixel":int(out.altura_meta_v2_pixel_m.notna().sum()),
             "com_predicao_na_vizinhanca_5m":int(out.altura_meta_v2_max_raio_5m_m.notna().sum()),
             "mediana_pixel_m":float(out.altura_meta_v2_pixel_m.median()) if out.altura_meta_v2_pixel_m.notna().any() else None,
             "mediana_max_raio_5m_m":float(out.altura_meta_v2_max_raio_5m_m.median()) if out.altura_meta_v2_max_raio_5m_m.notna().any() else None,
             "fontes":sources,
             "ressalvas":["Dados preditos a partir de satelite, sem validacao de campo no local",
                          "Pixel no ponto pode nao coincidir com topo da copa",
                          "O maximo em 5m pode incluir vegetacao de outro individuo",
                          "C3 e indice empirico, nao altura real validada"]}
    (saida / "v3_meta_chmv2_resumo.json").write_text(json.dumps(summary,indent=2,ensure_ascii=False),encoding="utf-8")
    print(json.dumps(summary,indent=2,ensure_ascii=False))
    print("Resultados:",path)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pontos",type=Path,required=True)
    parser.add_argument("--out",type=Path,required=True)
    parser.add_argument("--raio",type=float,default=5.0)
    args=parser.parse_args()
    executar(args.pontos,args.out,args.raio)

if __name__=="__main__":
    main()
