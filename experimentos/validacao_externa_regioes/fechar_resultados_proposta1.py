"""Verifica os mapas, resume a transferência e prepara arquivos de rotulação cega."""
from __future__ import annotations

import argparse
from contextlib import ExitStack
from pathlib import Path
import json

import geopandas as gpd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
import numpy as np
import pandas as pd
import rasterio
from rasterio.enums import ColorInterp, Resampling
from rasterio.features import geometry_mask
from rasterio.windows import Window
from shapely.geometry import mapping

from preparar_rotulacao import excluded_segment_ids, generate_segments
from treinar_area1 import FEATURES, MODELS


AREAS = {
    "area1_caxias": "Area1 · Caxias do Sul",
    "sagrada_familia_caxias": "Sagrada Família · Caxias do Sul",
    "centro_novo_hamburgo": "Centro · Novo Hamburgo",
    "lomba_grande_novo_hamburgo": "Lomba Grande · Novo Hamburgo",
    "cristo_rei_sao_leopoldo": "Cristo Rei · São Leopoldo",
}
TREE = "#249759"
GRASS = "#f2bc42"
NAMES = ("Árvore prevista", "Gramínea prevista")
SLUGS = (
    "random_forest", "svm_rbf", "regressao_logistica", "extra_trees",
    "knn", "hist_gradient_boosting", "gaussian_naive_bayes", "dummy",
)


def parse_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def shade_rgb(src, shape):
    image = np.moveaxis(src.read([1, 2, 3], out_shape=(3, *shape),
                                 resampling=Resampling.bilinear), 0, -1)
    lo, hi = np.percentile(image, (2, 98))
    return np.clip((image.astype(np.float32) - lo) / max(hi - lo, 1), 0, 1)


def verify_maps(maps, rgb_path, summary):
    totals = np.zeros((len(MODELS), 3), dtype=np.int64)
    segment_totals = np.zeros((len(MODELS), 2), dtype=np.int64)
    signatures = np.zeros(256, dtype=np.int64)
    with ExitStack() as stack:
        source = stack.enter_context(rasterio.open(rgb_path))
        ids = stack.enter_context(rasterio.open(maps / "segmento_id.tif"))
        predicted = [stack.enter_context(rasterio.open(maps / f"classificacao_{slug}.tif"))
                     for slug in SLUGS]
        for ds in [ids, *predicted]:
            if (ds.crs, ds.transform, ds.shape) != (source.crs, source.transform, source.shape):
                raise ValueError(f"Grade ou CRS divergente: {ds.name}")
        pixels = 0
        segments = 0
        for _, window in ids.block_windows(1):
            tags = ids.read(1, window=window)
            valid = tags > 0
            pixels += int(valid.sum())
            segments += len(np.unique(tags[valid]))
            agreement = np.zeros(tags.shape, dtype=np.uint8)
            for i, ds in enumerate(predicted):
                arr = ds.read(1, window=window)
                if arr.max() > 2 or not np.array_equal(arr > 0, valid):
                    raise ValueError(f"Códigos ou máscara inconsistentes: {ds.name}")
                totals[i] += np.bincount(arr.ravel(), minlength=3)
                segment_totals[i] += [np.unique(tags[arr == cl]).size for cl in (1, 2)]
                agreement |= (arr == 1).astype(np.uint8) << i
            signatures += np.bincount(agreement[valid], minlength=256)
        summary = summary.set_index("modelo").loc[list(MODELS)].reset_index()
        expected_pixels = summary[["pixels_previstos_arvore", "pixels_previstos_grama"]]
        expected_segments = summary[["segmentos_previstos_arvore", "segmentos_previstos_grama"]]
        if not np.array_equal(totals[:, 1:], expected_pixels.to_numpy()):
            raise ValueError("Contagens de pixels divergem dos GeoTIFFs.")
        if not np.array_equal(segment_totals, expected_segments.to_numpy()):
            raise ValueError("Contagens de segmentos divergem dos GeoTIFFs.")
        if not np.all(segment_totals.sum(axis=1) == segments):
            raise ValueError("Segmentos com classificação incompleta.")
        pixel_area = abs(source.transform.a * source.transform.e -
                         source.transform.b * source.transform.d)
        if not source.crs.is_projected or source.crs.linear_units.lower() not in {"metre", "meter", "m"}:
            raise ValueError("Áreas requerem CRS projetado com unidades em metros.")
        agreement_by_model = np.ones((len(MODELS), len(MODELS)), dtype=float)
        codes = np.arange(256, dtype=np.uint8)
        for i in range(len(MODELS)):
            for j in range(i):
                equal = ((codes >> i) & 1) == ((codes >> j) & 1)
                agreement_by_model[i, j] = agreement_by_model[j, i] = signatures[equal].sum() / pixels
        for idx, cls in enumerate(("arvore", "grama"), 1):
            summary[f"area_prevista_{cls}_ha"] = totals[:, idx] * pixel_area / 10_000
            summary[f"proporcao_pixels_{cls}"] = totals[:, idx] / pixels
        summary["pixels_validos"] = pixels
        summary["segmentos_validos"] = segments
        summary["area_valida_ha"] = pixels * pixel_area / 10_000
        audit = {
            "pixels_grade": source.width * source.height,
            "pixels_validos": pixels,
            "segmentos_validos": segments,
            "resolucao_m": list(source.res),
            "crs": str(source.crs),
            "area_por_pixel_m2": pixel_area,
            "raster_RGB_dimensoes": [source.width, source.height],
        }
    return summary, agreement_by_model, audit


def regional_figure(region, rgb_path, maps, dest):
    with rasterio.open(rgb_path) as src:
        scale = min(1, 1120 / max(src.shape))
        shape = (round(src.height * scale), round(src.width * scale))
        image = shade_rgb(src, shape)
        bounds = src.bounds
    extent = (bounds.left, bounds.right, bounds.bottom, bounds.top)
    length = 1000 if bounds.right - bounds.left > 6500 else 500
    rgb_colors = np.array([matplotlib.colors.to_rgba(TREE, .59),
                           matplotlib.colors.to_rgba(GRASS, .53)], dtype=np.float32)
    fig, axes = plt.subplots(3, 3, figsize=(11.7, 12.5))
    fig.subplots_adjust(top=.90, bottom=.13, hspace=.20, wspace=.035, left=.05, right=.95)
    panels = zip(axes.ravel(), ["Ortoimagem RGB", *MODELS], [None, *SLUGS])
    for ax, name, slug in panels:
        ax.imshow(image, extent=extent, interpolation="nearest")
        if slug:
            with rasterio.open(maps / f"classificacao_{slug}.tif") as src:
                classes = src.read(1, out_shape=shape, resampling=Resampling.nearest)
            overlay = np.zeros((*shape, 4), dtype=np.float32)
            overlay[classes > 0] = rgb_colors[classes[classes > 0] - 1]
            ax.imshow(overlay, extent=extent, interpolation="nearest")
        ax.set_title(name, fontsize=10, fontweight="semibold")
        ax.set(xticks=[], yticks=[])
        x = bounds.left + .055 * (bounds.right - bounds.left)
        y = bounds.bottom + .055 * (bounds.top - bounds.bottom)
        ax.plot([x, x + length], [y, y], lw=2.5, color="white", solid_capstyle="butt")
        ax.text(x, y + .018 * (bounds.top - bounds.bottom), f"{length:,} m".replace(",", "."),
                color="white", fontsize=7, backgroundcolor="#21312d")
    fig.suptitle(AREAS[region], y=.97, fontsize=19, fontweight="bold", color="#142c25")
    fig.text(.5, .925, "Predições por segmento Quickshift  •  SIRGAS 2000 / UTM 22S",
             ha="center", fontsize=10, color="#304d44")
    fig.legend(handles=[Patch(facecolor=TREE, label=NAMES[0]), Patch(facecolor=GRASS, label=NAMES[1]),
                        Patch(facecolor="#d9dedb", label="RGB sem sobreposição de classe")],
               loc="lower center", bbox_to_anchor=(.5, .065), ncol=3, frameon=False, fontsize=9)
    fig.text(.5, .038, "EPSG:31982  |  Resolução nominal do GeoTIFF de classificação: 0,5 m",
             ha="center", fontsize=8, color="#304d44")
    fig.savefig(dest, dpi=135)
    plt.close(fig)


def transfer_features(maps, base, dest, region, exclude):
    data = pd.read_csv(maps / "segmentos.csv.gz", usecols=["segmento_id", *FEATURES])
    area1 = pd.read_csv(base, usecols=list(FEATURES))
    if data.empty or data.segmento_id.duplicated().any():
        raise ValueError("Tabela regional de segmentos ausente ou duplicada.")
    flags = {"todos_segmentos": np.ones(len(data), dtype=bool)}
    if exclude:
        aoi = gpd.read_file(exclude)
        with rasterio.open(maps / "segmento_id.tif") as src:
            polygon = aoi.to_crs(src.crs).geometry.union_all().buffer(25)
            excluded = excluded_segment_ids(src, polygon)
        flags["fora_area1_e_buffer"] = ~data.segmento_id.isin(excluded)
    result = []
    for scope, valid in flags.items():
        for key in FEATURES:
            x = data.loc[valid, key].to_numpy()
            y = area1[key].to_numpy()
            if not len(x) or not np.isfinite(x).all():
                raise ValueError("Atributos sem observações válidas.")
            p05, median, p95 = np.quantile(x, [.05, .5, .95])
            result.append({
                "regiao": region, "recorte": scope, "atributo": key,
                "n_segmentos": len(x), "p05": p05, "mediana": median, "p95": p95,
                "min_treino": y.min(), "max_treino": y.max(),
                "frac_fora_minmax_treino": np.mean((x < y.min()) | (x > y.max())),
            })
    table = pd.DataFrame(result)
    table.to_csv(dest, index=False)
    return table


def blind_context(rgb_path, sample_path, dest):
    """Ortoimagem de contexto e recortes RGB de 40 m sem camadas de predição."""
    samples = gpd.read_file(sample_path)
    tiles = dest / "recortes_rgb"
    tiles.mkdir(exist_ok=True)
    with rasterio.open(rgb_path) as rgb:
        samples = samples.to_crs(rgb.crs)
        for item in samples.itertuples():
            row, col = rgb.index(item.geometry.x, item.geometry.y)
            window = Window(col - 40, row - 40, 81, 81)
            data = rgb.read([1, 2, 3], window=window, boundless=True)
            plt.imsave(tiles / f"{item.amostra_id}.png", np.moveaxis(data, 0, -1))
        ratio = min(1, 2200 / max(rgb.shape))
        shape = (round(rgb.height * ratio), round(rgb.width * ratio))
        transform = rgb.transform * rgb.transform.scale(rgb.width / shape[1], rgb.height / shape[0])
        with rasterio.open(dest / "rgb_contexto.tif", "w", driver="GTiff", width=shape[1],
                           height=shape[0], transform=transform, crs=rgb.crs,
                           count=3, dtype="uint8", compress="deflate", photometric="RGB") as dst:
            dst.write(rgb.read([1, 2, 3], out_shape=(3, *shape), resampling=Resampling.bilinear))
            dst.colorinterp = (ColorInterp.red, ColorInterp.green, ColorInterp.blue)


def finish(region, rgb, maps, base, output, exclude=None):
    report = parse_json(maps / "manifesto_execucao.json")
    if report["estado"] != "concluido" or report["quadrantes_concluidos"] != report["quadrantes_previstos"]:
        raise ValueError("Mapas incompletos.")
    output.mkdir(parents=True, exist_ok=True)
    counts = pd.read_csv(maps / "resumo_classes_previstas.csv")
    summary, agreement, audit = verify_maps(maps, rgb, counts)
    features = transfer_features(maps, base, output / "distribuicao_atributos.csv", region, exclude)
    if len(features[features.recorte == "todos_segmentos"]) != len(FEATURES):
        raise ValueError("Atributos incompletos.")
    summary.insert(0, "regiao", region)
    summary.to_csv(output / "areas_previstas_hectares.csv", index=False)
    pd.DataFrame(agreement, index=MODELS, columns=MODELS).to_csv(output / "acordo_entre_modelos_pixels.csv")
    regional_figure(region, rgb, maps, output / "comparacao_cartografica.pdf")
    audit["regiao"] = region
    audit["quadrantes_concluidos"] = report["quadrantes_concluidos"]
    audit["n_mapas_verificados"] = len(MODELS)
    audit["estado_avaliacao_geografica"] = "nao_aplicavel_area_de_treino" if region == "area1_caxias" else "aguarda_referencias_independentes"
    if region != "area1_caxias":
        blind = output / "rotulacao_cega"
        if not (blind / "amostras_para_anotar.gpkg").is_file():
            generate_segments(maps / "segmento_id.tif", 200, 250, 20261112, blind,
                              exclude_aoi=exclude, exclusion_m=25)
        samples = gpd.read_file(blind / "amostras_para_anotar.gpkg")
        if not samples.classe_verificada.fillna("").eq("").all():
            raise ValueError("O pacote de distribuição cega contém rótulos preenchidos.")
        with rasterio.open(maps / "segmento_id.tif") as src:
            ids = [int(x[0]) for x in src.sample(zip(samples.geometry.x, samples.geometry.y))]
            if len(ids) != len(set(ids)) or min(ids) <= 0:
                raise ValueError("Amostras fora dos segmentos ou duplicadas.")
            if exclude:
                aoi = gpd.read_file(exclude).to_crs(src.crs).geometry.union_all()
                if any(aoi.distance(point) <= 25 for point in samples.geometry):
                    raise ValueError("Amostra na área de exclusão.")
                crossing = excluded_segment_ids(src, aoi.buffer(25))
                if crossing.intersection(ids):
                    raise ValueError("Amostra de segmento que cruza a área de exclusão.")
        blind_context(rgb, blind / "amostras_para_anotar.gpkg", blind)
        audit["amostras_cegas"] = len(samples)
    (output / "verificacao_resultados.json").write_text(json.dumps(audit, ensure_ascii=False, indent=2))
    print(json.dumps(audit, ensure_ascii=False), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--regiao", choices=AREAS, required=True)
    for name in ("rgb", "mapas", "base", "out"):
        parser.add_argument(f"--{name}", type=Path, required=True)
    parser.add_argument("--excluir-area1", type=Path)
    args = parser.parse_args()
    if args.regiao == "sagrada_familia_caxias" and args.excluir_area1 is None:
        parser.error("Sagrada Família exige o polígono da Area1 para a exclusão de 25 m.")
    finish(args.regiao, args.rgb, args.mapas, args.base, args.out, args.excluir_area1)


if __name__ == "__main__":
    main()
