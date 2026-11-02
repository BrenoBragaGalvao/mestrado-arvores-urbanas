#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""V3: estimativas de altura de dossel em 257 pontos originais da Area1.

Duas referências públicas no Google Earth Engine:
  - Meta/WRI (~1 m): projects/sat-io/open-datasets/facebook/meta-canopy-height
  - ETH Zurich (10 m, 2020): users/nlang/ETH_GlobalCanopyHeight_2020_10m_v1

NÃO são alturas medidas de árvores individuais. Não usar como verdade de campo.
Requer autenticação do Earth Engine e projeto habilitado.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import geopandas as gpd
import pandas as pd

META_ASSET = "projects/sat-io/open-datasets/facebook/meta-canopy-height"
ETH_ASSET = "users/nlang/ETH_GlobalCanopyHeight_2020_10m_v1"
ETH_SD_ASSET = "users/nlang/ETH_GlobalCanopyHeightSD_2020_10m_v1"
MISSING = -9999.0


def pontos_originais(arvores: Path) -> pd.DataFrame:
    if not arvores.is_file():
        raise FileNotFoundError(f"Arquivo não encontrado: {arvores}")
    geo = gpd.read_file(arvores)
    if len(geo) != 257:
        raise ValueError(f"Esperados 257 pontos originais; encontrados {len(geo)}.")
    if geo.crs is None or not geo.geometry.geom_type.eq("Point").all():
        raise ValueError("Arvores.gpkg precisa conter pontos e CRS explícito.")
    geo = geo.to_crs("EPSG:4326")
    return pd.DataFrame({
        "ponto_id": range(len(geo)),
        "longitude": geo.geometry.x.values,
        "latitude": geo.geometry.y.values,
    })


def inicializar_gee(project: str) -> object:
    import ee
    try:
        ee.Initialize(project=project)
    except Exception:
        print("Solicitando autenticação do Google Earth Engine...")
        ee.Authenticate()
        ee.Initialize(project=project)
    return ee


def amostrar(ee, pontos, image, bandas, escala_m=1):
    """Amostra estritamente nos pontos, preservando os IDs para posterior left join."""
    base = {int(i): {} for i in pontos["ponto_id"]}
    for inicio in range(0, len(pontos), 50):
        fatia = pontos.iloc[inicio:inicio + 50]
        fc = ee.FeatureCollection([
            ee.Feature(
                ee.Geometry.Point([float(row.longitude), float(row.latitude)]),
                {"ponto_id": int(row.ponto_id)}
            )
            for row in fatia.itertuples(index=False)
        ])
        # O sentinel -9999 distingue ausência de cobertura de alturas baixas.
        fc_resultado = image.unmask(MISSING).sampleRegions(
            collection=fc, properties=["ponto_id"], scale=escala_m,
            geometries=False, tileScale=4
        )
        retorno = fc_resultado.getInfo()
        for feat in retorno.get("features", []):
            p = feat.get("properties", {})
            idx = int(p["ponto_id"])
            for coluna in bandas:
                v = p.get(coluna)
                if v is not None and float(v) != MISSING:
                    base[idx][coluna] = float(v)
    return pd.DataFrame([{"ponto_id":idx, **props} for idx,props in base.items()])


def coletar_meta(ee, pontos):
    multiponto = ee.Geometry.MultiPoint(
        pontos[["longitude", "latitude"]].values.astype(float).tolist()
    )
    colecao = ee.ImageCollection(META_ASSET).filterBounds(multiponto.bounds())
    total_cenas = int(colecao.size().getInfo())
    if total_cenas < 1:
        raise RuntimeError("Meta/WRI não retornou imagens para a Area1.")
    imagem = colecao.mosaic().select([0], ["altura_meta_1m_m"])
    return amostrar(ee, pontos, imagem, ["altura_meta_1m_m"], escala_m=1), total_cenas


def coletar_eth(ee, pontos):
    imagem = ee.Image(ETH_ASSET).select([0], ["altura_eth_10m_m"])
    try:
        sd = ee.Image(ETH_SD_ASSET).select([0], ["desvio_eth_10m_m"])
        imagem = imagem.addBands(sd)
        bandas = ["altura_eth_10m_m", "desvio_eth_10m_m"]
        dados = amostrar(ee, pontos, imagem, bandas, escala_m=10)
    except Exception as error:
        print(f"Desvio-padrão ETH indisponível ({error}); tentando altura isolada.")
        altura = ee.Image(ETH_ASSET).select([0], ["altura_eth_10m_m"])
        dados = amostrar(ee, pontos, altura, ["altura_eth_10m_m"], escala_m=10)
    return dados


def principal():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--area", required=True, type=Path, help="Pasta Area1 do Drive")
    parser.add_argument("--out", required=True, type=Path, help="Destino do CSV")
    parser.add_argument("--project", required=True, help="ID do projeto Cloud com Earth Engine habilitado")
    parser.add_argument("--fontes", choices=["ambas","meta","eth"], default="ambas")
    parser.add_argument("--indices-v3", type=Path, help="CSV opcional com indice_potencial_C3 da V3")
    args = parser.parse_args()

    pts = pontos_originais(args.area / "Arvores.gpkg")
    ee = inicializar_gee(args.project)
    saida = args.out
    saida.mkdir(parents=True, exist_ok=True)
    result = pts.copy()
    aviso = {}
    concluido = 0

    if args.fontes in ("ambas", "meta"):
        try:
            dados, n = coletar_meta(ee, pts)
            result = result.merge(dados, on="ponto_id", how="left", validate="one_to_one")
            aviso["meta_cenas"] = n
            concluido += 1
        except Exception as err:
            aviso["erro_meta"] = str(err)
            print("Não foi possível amostrar o conjunto Meta:", err)

    if args.fontes in ("ambas", "eth"):
        try:
            dados = coletar_eth(ee, pts)
            result = result.merge(dados, on="ponto_id", how="left", validate="one_to_one")
            concluido += 1
        except Exception as err:
            aviso["erro_eth"] = str(err)
            print("Não foi possível amostrar o conjunto ETH:", err)

    if concluido == 0:
        raise RuntimeError(f"Nenhuma fonte pôde ser consultada: {aviso}")

    if args.indices_v3:
        v3 = pd.read_csv(args.indices_v3)
        colunas = ["ponto_id", "indice_potencial_C3"]
        if not set(colunas).issubset(v3.columns):
            raise ValueError(f"Arquivo V3 precisa conter {colunas}")
        if v3.ponto_id.duplicated().any():
            raise ValueError("IDs duplicados nos índices da V3")
        result = result.merge(v3[colunas], on="ponto_id", how="left", validate="one_to_one")

    for campo in ("altura_meta_1m_m", "altura_eth_10m_m"):
        if campo in result.columns:
            result[campo] = pd.to_numeric(result[campo], errors="coerce")
            result["qualidade_" + campo] = result[campo].apply(
                lambda v: "sem_dado" if pd.isna(v)
                else ("verificar_zero" if v <= 0
                      else ("verificar_extremo" if v > 60 else "estimativa_modelada"))
            )
    if len(result) != 257 or result.ponto_id.nunique() != 257:
        raise RuntimeError("Perda ou duplicação de pontos; CSV não salvo.")

    result["aviso"] = "Altura MODELADA de dossel; NAO e altura medida da arvore."
    output = saida / "v3_alturas_dossel_estimadas_257_pontos.csv"
    result.to_csv(output, index=False, encoding="utf-8-sig")
    resumo = {
        "total_pontos":len(result),
        "fontes_consultadas":args.fontes,
        "meta_asset":META_ASSET,
        "eth_asset":ETH_ASSET,
        "avisos":aviso,
        "observacao":"Estimativa indireta da vegetacao observada; nao se pode afirmar altura real individual."
    }
    for coluna in ("altura_meta_1m_m", "altura_eth_10m_m"):
        if coluna in result:
            serie = result[coluna].dropna()
            resumo[coluna] = {"com_valor":int(len(serie)),
                              "mediana_m":float(serie.median()) if len(serie) else None}
    (saida / "v3_alturas_dossel_resumo.json").write_text(
        json.dumps(resumo, indent=2, ensure_ascii=False), encoding="utf-8")
    print("Salvo:",output)
    print(json.dumps(resumo, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    principal()
